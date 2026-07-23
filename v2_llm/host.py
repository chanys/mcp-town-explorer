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
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

SERVER = Path(__file__).resolve().parent.parent / "server" / "server.py"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "towns.csv"
MODEL = "gpt-5.4-mini"
MAX_ITERATIONS = 5

# ALLOWLIST: the only tool names the host will ever execute. Checked before any
# call. The server advertises exactly these, but the allowlist is the host's own
# guarantee -- it does not trust the model to stay within bounds.
ALLOWLIST = {"get_housing", "get_distance", "get_schools", "get_safety"}

SYSTEM_PROMPT = (
    "You answer questions about Massachusetts towns using the provided tools. "
    "Call a tool for each town/topic you need, then explain the results plainly. "
    "Only these towns exist in the dataset; do not invent data for others."
)


def valid_towns() -> set[str]:
    """The host's own copy of the valid-town set, used to vet arguments."""
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
    """Token cost of the tool-schema block the model must read every turn."""
    try:
        enc = tiktoken.encoding_for_model(MODEL)
    except KeyError:
        enc = tiktoken.get_encoding("o200k_base")
    return len(enc.encode(json.dumps(tools)))


def validate(name: str, args: dict, towns: set[str], town_tools: set[str]) -> str | None:
    """Return a rejection reason, or None if the proposed call is allowed.

    The allowlist gates every tool. The dataset check applies only to tools that
    actually take a `town` (derived from their advertised schema), because that is
    the one argument this host has authoritative data for. A differently-shaped
    tool (say a weather tool taking lat/lon) is gated by the allowlist alone, and
    the server validates its own inputs.
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

    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = (await session.list_tools()).tools
            tools = to_openai_tools(mcp_tools)
            # Tools whose schema declares a `town` argument. Only these get the
            # dataset check in validate(); derived from the advertised schema, so a
            # server with differently-shaped tools needs no change here.
            town_tools = {
                t.name for t in mcp_tools
                if "town" in (t.inputSchema.get("properties") or {})
            }

            if show_tokens:
                print(f"[tokens] tool schema block = {count_schema_tokens(tools)} tokens "
                      f"({len(tools)} tools)", file=sys.stderr)

            # First turn carries the system + user input. Later turns chain off
            # the server-side conversation state via previous_response_id, so we
            # only ever send back the new tool outputs -- no manual history.
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
                    print(response.output_text or "")
                    return 0

                tool_outputs = []
                for call in calls:
                    name = call.name
                    args = json.loads(call.arguments or "{}")

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
                    # Validation passed. The model's PROPOSAL becomes an EXECUTION
                    # on the next line. Nothing below the model reaches the server
                    # without having cleared validate() above.
                    print(f"[EXECUTE] {name}({args})", file=sys.stderr)
                    result = await session.call_tool(name, args)
                    text = "".join(getattr(b, "text", "") for b in result.content)
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
    parser = argparse.ArgumentParser(description="V2 MCP host (LLM + validation).")
    parser.add_argument("prompt", help="natural-language question")
    parser.add_argument("--show-tokens", action="store_true", help="print tool-schema token cost")
    args = parser.parse_args()
    sys.exit(asyncio.run(run(args.prompt, args.show_tokens)))


if __name__ == "__main__":
    main()
