"""V1 host: NO LLM.

Argv selects the tool; the model is never involved. This isolates the MCP
protocol from any model behavior. This file is the HOST. The MCP CLIENT is
`ClientSession`, from the SDK -- it is not hand-written.

    python v1_cli/host.py housing Winchester
    python v1_cli/host.py distance Winchester
    python v1_cli/host.py schools Lexington
    python v1_cli/host.py safety Woburn
    python v1_cli/host.py list-tools
    python v1_cli/host.py resource Winchester
    python v1_cli/host.py --verbose housing Nowhere   # see the error path
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import AnyUrl

SERVER = Path(__file__).resolve().parent.parent / "server" / "server.py"
COMMAND_TO_TOOL = {
    "housing": "get_housing",
    "distance": "get_distance",
    "schools": "get_schools",
    "safety": "get_safety",
}


def log(verbose: bool, *parts) -> None:
    """Protocol-lifecycle logging goes to stderr, so stdout stays clean data."""
    if verbose:
        print("[protocol]", *parts, file=sys.stderr)


def _print_blocks(blocks, file=sys.stdout) -> None:
    for b in blocks:
        print(b.text, file=file)


async def run(args: argparse.Namespace) -> int:
    # Launch the server as a subprocess over stdio, using this same interpreter.
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            log(args.verbose, "-> initialize")
            init = await session.initialize()
            # The server's initialize response: protocol version it agreed to and
            # who it says it is. This is the MCP handshake.
            log(args.verbose, "<- initialized:",
                f"protocol={init.protocolVersion},",
                f"server={init.serverInfo.name} {init.serverInfo.version}")

            if args.command == "list-tools":
                log(args.verbose, "-> tools/list")
                result = await session.list_tools()
                log(args.verbose, f"<- tools/list ({len(result.tools)} tools)")
                # Print the raw advertised schema: this is what every client sees,
                # and in V2 it is what the model is billed tokens to read.
                for t in result.tools:
                    print(json.dumps(
                        {"name": t.name, "description": t.description, "inputSchema": t.inputSchema},
                        indent=2,
                    ))
                return 0

            if args.command == "resource":
                uri = f"town://{args.town}"
                log(args.verbose, "-> resources/read", uri)
                result = await session.read_resource(AnyUrl(uri))
                log(args.verbose, "<- resources/read")
                _print_blocks(result.contents)
                return 0

            tool = COMMAND_TO_TOOL[args.command]
            call_args = {"town": args.town}
            log(args.verbose, "-> tools/call", tool, call_args)
            result = await session.call_tool(tool, call_args)
            log(args.verbose, f"<- tools/call (isError={result.isError})")
            if result.isError:
                print("ERROR from server:", file=sys.stderr)
                _print_blocks(result.content, file=sys.stderr)  # error text lives here
                return 1
            _print_blocks(result.content)
            return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="V1 MCP host (no LLM).")
    parser.add_argument("--verbose", action="store_true", help="log the protocol lifecycle")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("housing", "distance", "schools", "safety", "resource"):
        p = sub.add_parser(cmd)
        p.add_argument("town")
    sub.add_parser("list-tools")

    args = parser.parse_args()
    sys.exit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
