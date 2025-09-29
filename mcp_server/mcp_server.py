#!/usr/bin/env python3
"""
MCP HTTP Server for AI System Card

This server exposes system card sections as read-only MCP resources over HTTP transport.
It validates system card YAML against the JSON schema and only advertises AI system data.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP Protocol Constants
MCP_PROTOCOL_VERSION = "2024-11-05"
MCP_HEADER_PROTOCOL_VERSION = "MCP-Protocol-Version"

# Security: origin and token restrictions removed per configuration


class MCPRequest(BaseModel):
    """MCP JSON-RPC request model"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP JSON-RPC response model"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class SystemCardMCPServer:
    """MCP HTTP Server that exposes system card sections as resources"""
    
    def __init__(self, system_card_path: Path, schema_path: Path):
        self.system_card_path = system_card_path
        self.schema_path = schema_path
        self.system_card_data: Optional[Dict[str, Any]] = None
        self.schema: Optional[Dict[str, Any]] = None
        
        # Load and validate system card
        self._load_system_card()
        self._load_schema()
        self._validate_system_card()
    
    def _load_system_card(self) -> None:
        """Load system card YAML data"""
        try:
            with self.system_card_path.open("r", encoding="utf-8") as f:
                self.system_card_data = yaml.safe_load(f)
            logger.info(f"Loaded system card from {self.system_card_path}")
        except Exception as e:
            logger.error(f"Failed to load system card: {e}")
            raise
    
    def _load_schema(self) -> None:
        """Load JSON schema"""
        try:
            with self.schema_path.open("r", encoding="utf-8") as f:
                self.schema = json.load(f)
            logger.info(f"Loaded schema from {self.schema_path}")
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            raise
    
    def _validate_system_card(self) -> None:
        """Validate system card against schema"""
        if not self.system_card_data or not self.schema:
            raise ValueError("System card data or schema not loaded")
        
        validator = Draft202012Validator(self.schema)
        errors = sorted(validator.iter_errors(self.system_card_data), key=lambda e: e.path)
        if errors:
            error_lines = ["System card validation failed:"]
            for err in errors:
                location = "/".join([str(p) for p in err.path]) or "<root>"
                error_lines.append(f"- {location}: {err.message}")
            raise ValueError("\n".join(error_lines))
        
        logger.info("System card validation passed")
    
    # Origin and authentication validation removed
    
    def _create_error_response(self, request_id: Optional[str], code: int, message: str) -> MCPResponse:
        """Create MCP error response"""
        return MCPResponse(
            id=request_id,
            error={
                "code": code,
                "message": message
            }
        )
    
    def _create_success_response(self, request_id: Optional[str], result: Dict[str, Any]) -> MCPResponse:
        """Create MCP success response"""
        return MCPResponse(
            id=request_id,
            result=result
        )
    
    def handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP initialize request"""
        return self._create_success_response(request.id, {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "resources": {
                    "subscribe": False,
                    "listChanged": False
                }
            },
            "serverInfo": {
                "name": "ai-system-card-mcp-server",
                "version": "1.0.0"
            }
        })
    
    def handle_resources_list(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP resources/list request - advertise system card sections"""
        if not self.system_card_data:
            return self._create_error_response(request.id, -32603, "System card data not available")
        
        # Define available resources based on system card sections
        resources = [
            {
                "uri": "system-card://metadata",
                "name": "System Metadata",
                "description": "AI system metadata including name, version, developer, and contact information",
                "mimeType": "application/json"
            },
            {
                "uri": "system-card://purpose",
                "name": "System Purpose",
                "description": "Narrative description of the AI system's purpose and intended use",
                "mimeType": "text/plain"
            },
            {
                "uri": "system-card://technical-information",
                "name": "Technical Information",
                "description": "Technical details including AI model, hosting platform, development stack, and guardrails",
                "mimeType": "application/json"
            },
            {
                "uri": "system-card://data-provenance",
                "name": "Data Provenance and Pedigree",
                "description": "Information about base model, augmentation sources, and data lineage",
                "mimeType": "application/json"
            },
            {
                "uri": "system-card://security-safety",
                "name": "Security and Safety",
                "description": "Security considerations, safety measures, and known issues",
                "mimeType": "application/json"
            },
            {
                "uri": "system-card://governance",
                "name": "Governance",
                "description": "Reporting instructions and contact information for governance",
                "mimeType": "application/json"
            },
            {
                "uri": "system-card://references",
                "name": "References",
                "description": "Links and citations referenced in the system card",
                "mimeType": "application/json"
            }
        ]
        
        return self._create_success_response(request.id, {
            "resources": resources
        })
    
    def handle_resources_read(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP resources/read request - return specific system card section"""
        if not self.system_card_data:
            return self._create_error_response(request.id, -32603, "System card data not available")
        
        if not request.params or "uri" not in request.params:
            return self._create_error_response(request.id, -32602, "Missing required parameter: uri")
        
        uri = request.params["uri"]
        
        # Map URIs to system card sections
        section_mapping = {
            "system-card://metadata": self.system_card_data.get("metadata"),
            "system-card://purpose": self.system_card_data.get("purpose"),
            "system-card://technical-information": self.system_card_data.get("technical_information"),
            "system-card://data-provenance": self.system_card_data.get("data_provenance_and_pedigree"),
            "system-card://security-safety": self.system_card_data.get("security_and_safety"),
            "system-card://governance": self.system_card_data.get("governance"),
            "system-card://references": self.system_card_data.get("references")
        }
        
        if uri not in section_mapping:
            return self._create_error_response(request.id, -32602, f"Unknown resource URI: {uri}")
        
        section_data = section_mapping[uri]
        if section_data is None:
            return self._create_error_response(request.id, -32602, f"Resource not found: {uri}")
        
        # Determine content type and format
        if uri == "system-card://purpose":
            content = str(section_data)
            mime_type = "text/plain"
        else:
            content = json.dumps(section_data, indent=2)
            mime_type = "application/json"
        
        return self._create_success_response(request.id, {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": mime_type,
                    "text": content
                }
            ]
        })
    
    def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Route MCP requests to appropriate handlers"""
        method = request.method
        
        if method == "initialize":
            return self.handle_initialize(request)
        elif method == "resources/list":
            return self.handle_resources_list(request)
        elif method == "resources/read":
            return self.handle_resources_read(request)
        else:
            return self._create_error_response(request.id, -32601, f"Method not found: {method}")


def create_app(system_card_path: Path, schema_path: Path) -> FastAPI:
    """Create FastAPI application with MCP server"""
    app = FastAPI(
        title="AI System Card MCP Server",
        description="MCP HTTP server that exposes AI system card sections as resources",
        version="1.0.0"
    )
    
    # Add CORS middleware allowing all origins and headers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize MCP server
    mcp_server = SystemCardMCPServer(system_card_path, schema_path)
    
    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        """Security middleware for protocol version checking on POST /mcp only"""
        if request.url.path == "/mcp" and request.method.upper() == "POST":
            protocol_version = request.headers.get(MCP_HEADER_PROTOCOL_VERSION)
            if not protocol_version:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Missing {MCP_HEADER_PROTOCOL_VERSION} header"}
                )
        response = await call_next(request)
        return response
    
    @app.post("/mcp")
    async def mcp_endpoint(request: Request):
        """Main MCP endpoint for JSON-RPC requests"""
        try:
            # Parse JSON-RPC request
            body = await request.json()
            mcp_request = MCPRequest(**body)
            
            # Handle MCP request
            mcp_response = mcp_server.handle_request(mcp_request)
            
            return mcp_response.dict()
        
        except Exception as e:
            logger.error(f"MCP request handling error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get("/mcp")
    async def mcp_get_hint():
        """Hint for clients hitting GET /mcp in a browser"""
        return {
            "message": "Use POST /mcp with a JSON-RPC 2.0 payload",
            "example": {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "resources/list"
            }
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "system_card_loaded": mcp_server.system_card_data is not None}
    
    @app.get("/")
    async def root():
        """Root endpoint with server information"""
        return {
            "name": "AI System Card MCP Server",
            "version": "1.0.0",
            "protocol": "MCP",
            "transport": "HTTP",
            "endpoints": {
                "mcp": "/mcp",
                "health": "/health"
            },
            "security": {
                "authentication": "none",
                "origin_validation": "disabled",
                "protocol_version_header": "required"
            }
        }
    
    return app


def main(argv=None) -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI System Card MCP HTTP Server")
    parser.add_argument("system_card", type=Path, help="Path to system card YAML file")
    parser.add_argument("schema", type=Path, help="Path to JSON schema file")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    # Token and allowed-origins options removed
    
    args = parser.parse_args(argv)
    
    # Resolve paths: prefer CWD, then project root, then mcp_server dir
    mcp_server_dir = Path(__file__).parent
    project_root = mcp_server_dir.parent

    def resolve_input_path(given: Path) -> Path:
        if given.is_absolute():
            return given
        candidates = [
            (Path.cwd() / given).resolve(),
            (project_root / given).resolve(),
            (mcp_server_dir / given).resolve(),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        # Fallback to CWD resolution even if missing, so error message shows most expected path
        return (Path.cwd() / given).resolve()

    args.system_card = resolve_input_path(args.system_card)
    args.schema = resolve_input_path(args.schema)
    
    # Validate input files
    if not args.system_card.exists():
        print(f"Error: System card file not found: {args.system_card}", file=sys.stderr)
        print(f"Provide a path relative to your current directory, the project root, or an absolute path.", file=sys.stderr)
        return 1
    
    if not args.schema.exists():
        print(f"Error: Schema file not found: {args.schema}", file=sys.stderr)
        print(f"Provide a path relative to your current directory, the project root, or an absolute path.", file=sys.stderr)
        return 1
    
    # No token or origin restrictions to configure
    
    # Create and run FastAPI app
    try:
        app = create_app(args.system_card, args.schema)
        
        print(f"Starting AI System Card MCP Server...")
        print(f"System card: {args.system_card}")
        print(f"Schema: {args.schema}")
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"Authentication: none")
        print(f"Allowed origins: *")
        print(f"MCP endpoint: http://{args.host}:{args.port}/mcp")
        print(f"Health check: http://{args.host}:{args.port}/health")
        
        import uvicorn
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
        
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
