import uvicorn
import sys
import rclpy
from .config import settings

def main():
    print(f"Starting Franka API Server on {settings.host}:{settings.port}...")
    uvicorn.run(
        "franka_api_server.app:app", 
        host=settings.host, 
        port=settings.port, 
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
