"""Entry point to launch the Lyfpartner unified server with dynamic port and dual-stack IPv4/IPv6 support."""
import os
import socket
import asyncio
import uvicorn
from shared.seed_data import seed_database
from services.unified import unified_app

if __name__ == "__main__":
    asyncio.run(seed_database())
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"Lyfpartner unified server starting on port {port}...")
    try:
        # Dual-stack socket for both localhost (::1) and 127.0.0.1
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        sock.bind(("::", port))
        sock.listen(128)
        print(f"Bound dual-stack IPv4/IPv6 socket on port {port}")
        uvicorn.run(unified_app, fd=sock.fileno())
    except Exception as e:
        print(f"Falling back to standard host binding ({host}:{port}): {e}")
        uvicorn.run(unified_app, host=host, port=port)
