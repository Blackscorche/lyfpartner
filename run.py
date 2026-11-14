"""Entry point to launch the Lyfpartner unified server with dual-stack IPv4/IPv6 support."""
import socket
import asyncio
import uvicorn
from shared.seed_data import seed_database
from services.unified import unified_app

if __name__ == "__main__":
    asyncio.run(seed_database())
    
    # Create dual-stack socket for both localhost (::1) and 127.0.0.1
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.bind(("::", 8000))
    sock.listen(128)
    
    print("Lyfpartner server running on http://localhost:8000 and http://127.0.0.1:8000")
    uvicorn.run(unified_app, fd=sock.fileno())
