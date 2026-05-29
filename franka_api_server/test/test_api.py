import pytest
import httpx

def test_api_unauthorized(api_server_url):
    """Test that requests without API key are rejected"""
    client = httpx.Client(base_url=api_server_url)
    response = client.get("/api/v1/status/joints")
    assert response.status_code == 401

def test_api_status_joints(api_client):
    """Test the joint status endpoint"""
    response = api_client.get("/api/v1/status/joints")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data or "joint_positions" in data

def test_api_controller_list(api_client):
    """Test the mock controller list endpoint"""
    response = api_client.get("/api/v1/controller/list")
    assert response.status_code == 200
    data = response.json()
    assert "controllers" in data
    assert isinstance(data["controllers"], list)
    assert len(data["controllers"]) > 0
    assert data["controllers"][0]["name"] == "joint_state_broadcaster"

def test_api_motion_ptp(api_client):
    """Test PTP motion endpoint"""
    payload = {
        "goal_joint_configuration": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
        "goal_tolerance": 0.01,
        "max_velocity_scaling": 0.5
    }
    response = api_client.post("/api/v1/motion/move_joints", json=payload)
    # The action server might not be available in a pure test env,
    # so we just check if it returns a 200 or handles the missing action server cleanly
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "status" in data
    
def test_api_motion_skills_list(api_client):
    response = api_client.get('/api/v1/motion/skills')
    assert response.status_code == 200
    data = response.json()
    assert 'go_to_tongue_pose' in data['skills']
    assert 'go_to_face_pose' in data['skills']


def test_api_motion_skill_execute(api_client):
    response = api_client.post('/api/v1/motion/skills/go_to_tongue_pose')
    assert response.status_code == 200
    data = response.json()
    assert 'task_id' in data
    assert data['task_id'].startswith('skill_')


def test_api_motion_skill_unknown(api_client):
    response = api_client.post('/api/v1/motion/skills/unknown_pose')
    assert response.status_code == 404


def test_api_gripper_grasp(api_client):
    """Test gripper grasp endpoint"""
    payload = {
        "width": 0.05,
        "speed": 0.1,
        "force": 40.0
    }
    response = api_client.post("/api/v1/gripper/grasp", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
