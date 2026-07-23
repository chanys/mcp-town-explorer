"""V2 host: adds the LLM.

Natural language in; the model proposes tool calls; the HOST validates each one
before the CLIENT executes it. This file is the HOST (LLM + validation + MCP
client). The MCP CLIENT is `ClientSession`, from the SDK. The SERVER is unchanged.

    python v2_llm/host.py "Compare schools in Winchester and Lexington"
    python v2_llm/host.py --show-tokens "How safe is Woburn?"

Needs OPENAI_API_KEY in the environment.
"""

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

import tiktoken
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

SERVER = Path(__file__).resolve().parent.parent / "server" / "server.py"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "towns.csv"
MODEL = "gpt-5.4-mini"
MAX_ITERATIONS = 5

# ALLOWLIST: the exact tool names this host is willing to run. Every call the model
# proposes is checked against this list first. The server happens to offer exactly
# these, but the host keeps its own list so it never runs a tool just because the
# model asked for it.
ALLOWLIST = {"get_housing", "get_distance", "get_schools", "get_safety"}

SYSTEM_PROMPT = (
    "You answer questions about Massachusetts towns using the provided tools. "
    "Call a tool for each town/topic you need, then explain the results plainly. "
    "Only these towns exist in the dataset; do not invent data for others."
)


def valid_towns() -> set[str]:
    """Load the town names from the CSV. The host keeps its own copy so it can check
    the model's arguments before calling the server."""
    with DATA_PATH.open(newline="") as f:
        return {row["town"].lower() for row in csv.DictReader(f)}


def to_openai_tools(mcp_tools) -> list[dict]:
    """Translate MCP tool schemas into OpenAI Responses-API function tools.

    The Responses API flattens the function tool (name/description/parameters at
    the top level), unlike Chat Completions which nests them under "function".
    """
    return [
        {
            "type": "function",
            "name": t.name,
            "description": t.description,
            "parameters": t.inputSchema,
        }
        for t in mcp_tools
    ]


def count_schema_tokens(tools: list[dict]) -> int:
    """Count the tokens in the tool schemas. The model re-reads this block every
    turn, so it is a recurring cost -- the thing we want to measure."""
    try:
        enc = tiktoken.encoding_for_model(MODEL)
    except KeyError:
        enc = tiktoken.get_encoding("o200k_base")
    return len(enc.encode(json.dumps(tools)))


def validate(name: str, args: dict, towns: set[str], town_tools: set[str]) -> str | None:
    """Check one tool call the model proposed. Return a reason to reject it, or None
    to allow it.

    Two checks: (1) the tool name must be on the allowlist; (2) if the tool takes a
    `town`, that town must be one we have data for. We only validate the town because
    it is the one argument this host knows the valid values for. A tool with
    different arguments (say a weather tool taking lat/lon) only has to pass the
    allowlist -- the server checks its own inputs.
    """
    if name not in ALLOWLIST:
        return f"tool {name!r} is not on the allowlist"
    if name in town_tools:
        town = args.get("town")
        if not isinstance(town, str) or town.lower() not in towns:
            return f"unknown or missing town {town!r} (not in dataset)"
    return None


async def run(prompt: str, show_tokens: bool) -> int:
    towns = valid_towns()
    llm = OpenAI()

    # StdioServerParameters: how to start the server -- the command (this same Python
    # interpreter) and its arguments (the server script).
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    # stdio_client: starts the server as a child process and returns two pipes --
    # `read` for messages from the server, `write` for messages to it. This is the
    # transport (how bytes move); it is not MCP-aware.
    async with stdio_client(params) as (read, write):
        # ClientSession: the MCP client. It wraps the pipes and speaks the protocol
        # (initialize, list_tools, call_tool), so we never write raw JSON-RPC.
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = (await session.list_tools()).tools
            tools = to_openai_tools(mcp_tools)
            # The names of tools that take a `town` argument, read from the schema
            # the server advertised. Only these get the town check in validate(), so
            # a tool with different arguments needs no change here.
            town_tools = {
                t.name for t in mcp_tools
                if "town" in (t.inputSchema.get("properties") or {})
            }

            if show_tokens:
                print(f"[tokens] tool schema block = {count_schema_tokens(tools)} tokens "
                      f"({len(tools)} tools)", file=sys.stderr)

            # The first request sends the system prompt and the user's question.
            # After that we pass previous_response_id, so OpenAI keeps the running
            # conversation on its side and each later request only sends the new tool
            # results -- we never resend the whole history.
            response = llm.responses.create(
                model=MODEL,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                tools=tools,
            )

            for _ in range(MAX_ITERATIONS):
                calls = [item for item in response.output if item.type == "function_call"]
                if not calls:
                    print(response.output_text)
                    return 0

                tool_outputs = []
                for call in calls:
                    name = call.name
                    args = json.loads(call.arguments)

                    reason = validate(name, args, towns, town_tools)
                    if reason is not None:
                        print(f"[REJECTED] {name}({args}) -- {reason}", file=sys.stderr)
                        tool_outputs.append({
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": f"REJECTED by host: {reason}",
                        })
                        continue

                    # ---- PERMISSION BOUNDARY ----
                    # The checks above passed. On the very next line the model's
                    # *request* to call a tool becomes a real *execution* against the
                    # server. This is the one line where an untrusted proposal turns
                    # into an action; anything that failed validate() never reaches it.
                    print(f"[EXECUTE] {name}({args})", file=sys.stderr)
                    result = await session.call_tool(name, args)
                    text = "".join(b.text for b in result.content)
                    tool_outputs.append({
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": text,
                    })

                response = llm.responses.create(
                    model=MODEL,
                    previous_response_id=response.id,
                    input=tool_outputs,
                    tools=tools,
                )

            print(f"[stopped] hit MAX_ITERATIONS={MAX_ITERATIONS} without a final answer", file=sys.stderr)
            return 1


def main() -> None:
    # Load OPENAI_API_KEY from a .env at the repo root, if present, so a plain
    # `uv run python v2_llm/host.py ...` works without exporting the key first.
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    parser = argparse.ArgumentParser(description="V2 MCP host (LLM + validation).")
    parser.add_argument("prompt", help="natural-language question")
    parser.add_argument("--show-tokens", action="store_true", help="print tool-schema token cost")
    args = parser.parse_args()
    sys.exit(asyncio.run(run(args.prompt, args.show_tokens)))


if __name__ == "__main__":
    main()
