# MCP HTTP Server for AI System Card

This directory contains a Model Context Protocol (MCP) HTTP server that exposes AI system card sections as read-only resources. The server is designed to be secure and only advertises AI system data as specified in the system card.

## Directory Structure

```
mcp_server/
├── mcp_server.py      # Main MCP HTTP server implementation
├── requirements.txt   # Python dependencies for MCP server
├── README.md         # Quick start guide
└── MCP_SERVER.md     # This detailed documentation
```

## Features

- **HTTP Transport**: Uses FastAPI with uvicorn for HTTP-based MCP communication
- **Resource Exposure**: Exposes system card sections as MCP resources
- **Security Controls**: 
  - Bearer token authentication
  - Origin header validation (prevents DNS rebinding attacks)
  - MCP protocol version header validation
  - Localhost-only binding by default
- **Schema Validation**: Validates system card YAML against JSON schema before serving
- **Read-Only**: Only advertises system card data, performs no other actions

## Installation

Install the required dependencies:

```bash
cd mcp_server
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the MCP server with a system card and schema:

```bash
cd mcp_server
python mcp_server.py ../examples/ask-red-hat.yaml ../schema/system-card.schema
```

### Advanced Configuration

```bash
cd mcp_server
python mcp_server.py \
  ../examples/ask-red-hat.yaml \
  ../schema/system-card.schema \
  --host 127.0.0.1 \
  --port 8000 \
  --token "your-secure-token" \
  --allowed-origins "http://localhost:3000" "https://yourdomain.com"
```

### Environment Variables

- `MCP_SERVER_TOKEN`: Default authentication token (default: "default-secure-token")

## Security Configuration

### Authentication

The server requires Bearer token authentication. Set a secure token:

```bash
cd mcp_server
export MCP_SERVER_TOKEN="your-secure-random-token"
python mcp_server.py ../examples/ask-red-hat.yaml ../schema/system-card.schema
```

### Origin Validation

Configure allowed origins to prevent DNS rebinding attacks:

```bash
cd mcp_server
python mcp_server.py \
  ../examples/ask-red-hat.yaml \
  ../schema/system-card.schema \
  --allowed-origins "http://localhost:3000" "https://yourdomain.com"
```

### Network Binding

By default, the server binds to `127.0.0.1` (localhost only) for security. To bind to all interfaces (use with caution):

```bash
cd mcp_server
python mcp_server.py \
  ../examples/ask-red-hat.yaml \
  ../schema/system-card.schema \
  --host 0.0.0.0
```

## MCP Resources

The server exposes the following system card sections as MCP resources:

- `system-card://metadata` - AI system metadata (name, version, developer, contacts)
- `system-card://purpose` - System purpose and intended use
- `system-card://technical-information` - Technical details (model, platform, stack, guardrails)
- `system-card://data-provenance` - Data provenance and pedigree information
- `system-card://security-safety` - Security considerations and safety measures
- `system-card://governance` - Governance and reporting instructions
- `system-card://references` - Links and citations

## API Endpoints

- `POST /mcp` - Main MCP JSON-RPC endpoint
- `GET /health` - Health check endpoint
- `GET /` - Server information and configuration

## MCP Client Usage

### Example MCP Request

```bash
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secure-token" \
  -H "MCP-Protocol-Version: 2024-11-05" \
  -H "Origin: http://localhost:3000" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "resources/list"
  }'
```

### List Available Resources

```bash
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secure-token" \
  -H "MCP-Protocol-Version: 2024-11-05" \
  -H "Origin: http://localhost:3000" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "resources/list"
  }'
```

### Read a Resource

```bash
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secure-token" \
  -H "MCP-Protocol-Version: 2024-11-05" \
  -H "Origin: http://localhost:3000" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "resources/read",
    "params": {
      "uri": "system-card://metadata"
    }
  }'
```

## Security Considerations

1. **Token Security**: Use a strong, random authentication token
2. **Origin Validation**: Only allow trusted origins to prevent DNS rebinding
3. **Network Binding**: Bind to localhost only unless specifically needed
4. **HTTPS**: Use HTTPS in production environments
5. **Regular Updates**: Keep dependencies updated for security patches

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Ensure the Bearer token matches the server configuration
2. **Origin Not Allowed**: Check that the Origin header matches allowed origins
3. **Missing Protocol Version**: Include the `MCP-Protocol-Version` header
4. **Schema Validation Failed**: Verify the system card YAML is valid against the schema

### Logs

The server logs important events including:
- System card loading and validation
- Authentication attempts
- MCP request handling
- Error conditions

Check the console output for detailed logging information.

## Integration with MCP Clients

This server is compatible with MCP clients that support HTTP transport. Clients can:

1. Connect to the server using the `/mcp` endpoint
2. Authenticate using Bearer token
3. List available system card resources
4. Read specific system card sections
5. Make informed decisions about using the AI system based on the advertised information

The server strictly adheres to the MCP specification and only exposes system card data as resources, ensuring security and compliance.
