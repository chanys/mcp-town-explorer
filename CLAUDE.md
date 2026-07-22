# mcp-town-explorer

A learning repo that makes every MCP boundary visible: host, client, server, transport, discovery, invocation.
It is a teaching exercise, not a portfolio piece. Do not add features beyond what a task asks for.

## The core invariant

One server, two hosts.
Both hosts talk to the SAME server (`server/server.py`) with zero server changes.
If a change would require editing the server to make a host work, stop and reconsider.

## Layout

- `data/towns.csv` — synthetic MA town data. Every row has `data_source = "synthetic"`.
- `server/server.py` — the MCP server (FastMCP, stdio transport). Three narrow tools + one resource.
- `v1_cli/host.py` — host with NO LLM. Argv selects the tool. Isolates protocol from model behavior.
- `v2_llm/host.py` — host WITH an LLM (OpenAI). Adds schema-driven tool selection and host-side validation.

The MCP client is `ClientSession` from the SDK. It is never hand-written. The server is never imported by a host.

## Conventions

- Python via `uv` only: `uv run python ...`, `uv add ...`. Never `python3` or `pip`.
- Pinned to Python 3.12.
- The data is FABRICATED. It must never be presented as usable for a real decision.
- Comment only where the MCP boundary is non-obvious. Mark the line where a model PROPOSAL becomes an EXECUTION.

## Running

    # V1 (no API key needed)
    uv run python v1_cli/host.py housing Winchester
    uv run python v1_cli/host.py list-tools

    # V2 (needs OPENAI_API_KEY)
    uv run python v2_llm/host.py "Compare schools in Winchester and Lexington"
