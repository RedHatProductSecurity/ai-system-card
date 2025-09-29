# MCP HTTP Server for AI System Card

This directory contains the Model Context Protocol (MCP) HTTP server implementation that exposes AI system card sections as read-only resources.

## Files

- `mcp_server.py` - Main MCP HTTP server implementation
- `requirements.txt` - Python dependencies for the MCP server
- `MCP_SERVER.md` - Detailed documentation and usage guide

## Quick Start

1. **Install dependencies:**
   ```bash
   cd mcp_server
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python mcp_server.py ../examples/ask-red-hat.yaml ../schema/system-card.schema
   ```

3. **Test the server:**
   ```bash
   curl -X POST http://127.0.0.1:8000/mcp \
     -H "Content-Type: application/json" \
     -H "MCP-Protocol-Version: 2024-11-05" \
     -d '{"jsonrpc": "2.0", "id": "1", "method": "resources/list"}'
   ```

## Resources Exposed

The server exposes these system card sections as MCP resources:

- `system-card://metadata` - System metadata
- `system-card://purpose` - System purpose
- `system-card://technical-information` - Technical details
- `system-card://data-provenance` - Data provenance
- `system-card://security-safety` - Security & safety
- `system-card://governance` - Governance
- `system-card://references` - References

See `MCP_SERVER.md` for complete documentation.
