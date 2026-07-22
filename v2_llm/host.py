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
ALLOWLIST = {"get_housing", "get_schools", "get_safety"}

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
    """Translate MCP tool schemas into OpenAI's function-tool format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.inputSchema,
            },
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


def validate(name: str, args: dict, towns: set[str]) -> str | None:
    """Return a rejection reason, or None if the proposed call is allowed."""
    if name not in ALLOWLIST:
        return f"tool {name!r} is not on the allowlist"
    town = args.get("town")
    if not isinstance(town, str):
        return f"missing or non-string 'town' argument: {town!r}"
    if town.lower() not in towns:
        return f"unknown town {town!r} (not in dataset)"
    return None


async def run(prompt: str, show_tokens: bool) -> int:
    towns = valid_towns()
    llm = OpenAI()

    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = to_openai_tools((await session.list_tools()).tools)

            if show_tokens:
                print(f"[tokens] tool schema block = {count_schema_tokens(tools)} tokens "
                      f"({len(tools)} tools)", file=sys.stderr)

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]

            for _ in range(MAX_ITERATIONS):
                response = llm.chat.completions.create(model=MODEL, messages=messages, tools=tools)
                msg = response.choices[0].message

                if not msg.tool_calls:
                    print(msg.content or "")
                    return 0

                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
                })

                for tc in msg.tool_calls:
                    name = tc.function.name
                    args = json.loads(tc.function.arguments or "{}")

                    reason = validate(name, args, towns)
                    if reason is not None:
                        print(f"[REJECTED] {name}({args}) -- {reason}", file=sys.stderr)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": f"REJECTED by host: {reason}",
                        })
                        continue

                    # ---- PERMISSION BOUNDARY ----
                    # Validation passed. The model's PROPOSAL becomes an EXECUTION
                    # on the next line. Nothing below the model reaches the server
                    # without having cleared validate() above.
                    print(f"[EXECUTE] {name}({args})", file=sys.stderr)
                    result = await session.call_tool(name, args)
                    text = "".join(getattr(b, "text", "") for b in result.content)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": text})

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
