# Notes: how the MCP plumbing works

Reference notes for this repo, grounded in the actual objects the SDK returns.
Every value shown below was observed at runtime against `server/server.py`, not quoted from memory.

## Resources and `town://{town}`

Tools are *actions* (for example `get_safety`); resources are *readable content* addressed by a URI, like a file path or a URL.
`town://` is a custom URI scheme defined in this repo, and `{town}` is a template placeholder.

```python
@mcp.resource("town://{town}")
def town_profile(town: str) -> str: ...
```

FastMCP treats a URI with a placeholder as a *resource template*.
When a client reads `town://Woburn`, FastMCP matches the pattern, extracts `town="Woburn"`, calls the function, and returns its text.
It is the MCP equivalent of a parameterized GET endpoint: tools are the POST-like verbs, resources are the GET-like nouns.

## Server name and version

The server reports a name and a version to the client during the handshake, inside `serverInfo`.

- The name `town-explorer` is the string passed to the constructor: `mcp = FastMCP("town-explorer")`.
- The version `1.28.1` was never set explicitly. It is FastMCP's default, which is the installed `mcp` SDK version. Confirmed at runtime: the installed SDK is `1.28.1` and `serverInfo.version` is `1.28.1`.

To set your own, pass it: `FastMCP("town-explorer", version="0.1.0")`.

## The transport: `stdio_client(params)`

```python
async with stdio_client(params) as (read, write):
```

This is the transport layer. It:

1. Launches the server as a subprocess using `params.command` and `params.args` (here, this Python interpreter running `server/server.py`).
2. Wires the subprocess's stdin and stdout, and handles the newline-delimited JSON-RPC framing.
3. Yields two streams: `read` (messages coming from the server) and `write` (messages going to it).

The `async with` block starts the subprocess on entry and terminates it cleanly on exit.
At this point there is a working pipe, but nothing yet understands MCP semantics.

## The client: `ClientSession(read, write)`

```python
async with ClientSession(read, write) as session:
```

This is the MCP client (the "ClientSession, from the SDK, not hand-written" referenced in the README).
It wraps the raw streams in the MCP protocol: it builds and sends requests such as `initialize`, `tools/list`, and `tools/call`, matches responses to requests, and decodes results into typed objects.

The separation is the key idea.
`stdio_client` is how bytes move (transport); `ClientSession` is what the messages mean (protocol).
That is why swapping stdio for HTTP later would change only the transport line and leave the `session.*` calls untouched.

## The handshake: `session.initialize()`

This is the MCP handshake, required before any other call.
It:

1. Sends an `initialize` request carrying the client's protocol version and capabilities.
2. Receives the server's reply: `protocolVersion`, `serverInfo` (name and version), and `capabilities`. This is the `InitializeResult` that the V1 host prints in `--verbose` mode.
3. Sends the `initialized` notification to confirm.

Observed reply: `protocolVersion=2025-11-25`, `serverInfo=town-explorer 1.28.1`.
Until this completes, calls like `list_tools` or `call_tool` would error.

## Tool input schema and `get_safetyArguments`

FastMCP builds each tool's input JSON Schema by generating a Pydantic model from the function signature.
It names that model `<function_name>Arguments`, so `get_safety` produces `get_safetyArguments`, and Pydantic stamps that name into the schema's `title`.

It is just a human-readable label on the input schema and has no effect on how the tool is called.
The `town: str` parameter is what produced the `town` string property that sits alongside the title.

## Tool results: `content` versus `structuredContent`

`result.content` is a list of content blocks.
For the tools in this repo, each block is a `TextContent` with a `.text` string, and the returned dict arrives as JSON serialized into that string, not as a native Python dict.

Observed for `get_safety("Woburn")`:

```
content[0] type : TextContent
content[0].text : '{\n  "town": "Woburn",\n  "violent_crime_rate": 2.1\n}'
```

There is a separate field for structured data, `result.structuredContent`, but here it was `None`.
The reason is instructive: the tools are annotated `-> dict` (an untyped dict), so FastMCP generates no output schema and does not populate `structuredContent`.
If a tool were annotated with a typed return (a Pydantic model, a `TypedDict`, or a dataclass), FastMCP would emit an output schema and fill `structuredContent` with the real object, in addition to the text.

This is why both hosts treat results as text.
The V1 host prints `b.text`; the V2 host joins `b.text` across blocks and hands that JSON string back to the model, which reads JSON-as-text fine.
If a downstream consumer needed guaranteed structure rather than re-parsed text, that is the concrete reason to switch to a typed return and read `structuredContent`.
