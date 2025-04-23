# server.py
import logging
import os
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

# Init
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
mcp = FastMCP("JarvisLite")

@mcp.tool()
async def read_file(file_path: str) -> str:
    """Read and return file content."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"❌ File read error: {str(e)}"

# ───────────────────────────────────────────── RUN ─────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
