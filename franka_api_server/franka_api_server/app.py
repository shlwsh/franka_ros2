from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .config import settings
from .ros_bridge import RosBridge

app = FastAPI(title="Franka ROS2 API Server", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routers import status, ws, motion, gripper, controller

app.include_router(status.router, prefix="/api/v1")
app.include_router(ws.router)
app.include_router(motion.router, prefix="/api/v1")
app.include_router(gripper.router, prefix="/api/v1")
app.include_router(controller.router, prefix="/api/v1")

import os
from ament_index_python.packages import get_package_share_directory

@app.on_event("startup")
async def startup_event():
    # Initialize the ROS2 Bridge singleton on startup
    RosBridge.get_instance()

@app.on_event("shutdown")
async def shutdown_event():
    RosBridge.shutdown_instance()

# Mount static files for the dashboard
try:
    pkg_share_dir = get_package_share_directory('franka_api_server')
    static_dir = os.path.join(pkg_share_dir, 'static')
except Exception as e:
    # Fallback to local directory for direct script execution
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    print(f"Warning: Static directory not found at {static_dir}")
