"""
Check if a port is in use. Used before starting server to avoid conflict with
reference project (copilot-adk-app uses 3000 + 8000).
"""
import socket


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if something is listening on host:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0
