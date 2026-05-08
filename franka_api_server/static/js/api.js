class FrankaApiClient {
    constructor() {
        this.baseUrl = window.location.origin;
        this.wsConnections = {};
    }

    getApiKey() {
        return document.getElementById('api-key-input').value;
    }

    async request(method, path, body = null) {
        const headers = {
            'Content-Type': 'application/json',
            'X-API-Key': this.getApiKey()
        };
        
        try {
            const options = { method, headers };
            if (body) options.body = JSON.stringify(body);
            
            const response = await fetch(`${this.baseUrl}${path}`, options);
            const data = await response.json();
            return { ok: response.ok, status: response.status, data };
        } catch (error) {
            console.error("API Request Failed:", error);
            return { ok: false, status: 0, data: { detail: error.message } };
        }
    }

    // Connect WebSocket
    connectWS(endpoint, onMessage, onStatusChange) {
        if (this.wsConnections[endpoint]) {
            this.wsConnections[endpoint].close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${endpoint}?api_key=${this.getApiKey()}`;
        
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log(`WS ${endpoint} connected`);
            if(onStatusChange) onStatusChange(true);
        };
        
        ws.onclose = () => {
            console.log(`WS ${endpoint} disconnected`);
            if(onStatusChange) onStatusChange(false);
            // Simple reconnect logic could go here
        };
        
        ws.onerror = (err) => {
            console.error(`WS ${endpoint} error:`, err);
            if(onStatusChange) onStatusChange(false);
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (e) {
                console.error("Failed to parse WS message", e);
            }
        };

        this.wsConnections[endpoint] = ws;
        return ws;
    }

    // Motion API
    async moveJoints(targetJoints, velocityScaling = 0.5) {
        return this.request('POST', '/api/v1/motion/move_joints', {
            goal_joint_configuration: targetJoints,
            max_velocity_scaling: velocityScaling
        });
    }

    async stopMotion() {
        // We haven't implemented stop in backend yet, just placeholder
        return this.request('POST', '/api/v1/motion/stop'); 
    }

    async errorRecovery() {
        return this.request('POST', '/api/v1/motion/error_recovery');
    }

    // Gripper API
    async grasp(width, speed, force) {
        return this.request('POST', '/api/v1/gripper/grasp', {
            width: parseFloat(width),
            speed: parseFloat(speed),
            force: parseFloat(force)
        });
    }

    async moveGripper(width, speed) {
        return this.request('POST', '/api/v1/gripper/move', {
            width: parseFloat(width),
            speed: parseFloat(speed)
        });
    }

    async homingGripper() {
        return this.request('POST', '/api/v1/gripper/homing');
    }

    // Controllers
    async listControllers() {
        return this.request('GET', '/api/v1/controller/list');
    }
}

window.apiClient = new FrankaApiClient();
