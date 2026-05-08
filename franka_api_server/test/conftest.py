import pytest
import subprocess
import time
import httpx
import os
from contextlib import closing
import socket

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

@pytest.fixture(scope="session")
def api_server_url():
    """
    Start the FastAPI server as a subprocess for the entire test session.
    It dynamically finds a free port to avoid conflict with a running instance.
    """
    port = find_free_port()
    host = "127.0.0.1"
    
    # Environment variables to pass to the server
    env = os.environ.copy()
    env["FRANKA_API_HOST"] = host
    env["FRANKA_API_PORT"] = str(port)
    env["FRANKA_API_AUTH_ENABLED"] = "true"
    env["FRANKA_API_KEY"] = "test-secret-key"
    
    # We use uvicorn directly to start the app
    process = subprocess.Popen(
        ["uvicorn", "franka_api_server.app:app", "--host", host, "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    url = f"http://{host}:{port}"
    
    # Wait for the server to be ready
    max_retries = 30
    ready = False
    for _ in range(max_retries):
        try:
            with socket.create_connection((host, port), timeout=1.0):
                ready = True
                break
        except OSError:
            pass
        time.sleep(0.5)
        
    if not ready:
        process.terminate()
        out, err = process.communicate()
        raise RuntimeError(f"Test server failed to start. STDERR: {err.decode('utf-8')}")
        
    yield url
    
    # Teardown
    process.terminate()
    process.wait()

@pytest.fixture
def api_client(api_server_url):
    """
    Provides a configured httpx.AsyncClient with the correct Base URL and API Key.
    """
    import asyncio
    
    # Creating synchronous client wrapper for easier testing
    client = httpx.Client(
        base_url=api_server_url,
        headers={"X-API-Key": "test-secret-key"}
    )
    yield client
    client.close()
