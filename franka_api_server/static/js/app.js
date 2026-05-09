document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    try {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    } catch (e) {
        console.warn("Lucide icons failed to load:", e);
    }

    // Navigation Logic
    const navLinks = document.querySelectorAll('.nav-link');
    const views = document.querySelectorAll('.view');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('data-target');
            
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            views.forEach(v => {
                v.classList.remove('active');
                if (v.id === targetId) {
                    v.classList.add('active');
                }
            });
        });
    });

    // --- Dashboard Logic ---
    const jointsDisplay = document.getElementById('joints-display');
    const jointSliders = document.getElementById('joint-sliders');
    let currentJoints = [0,0,0,0,0,0,0];

    // Initialize UI elements for 7 joints
    for (let i = 0; i < 7; i++) {
        // Dashboard bars
        jointsDisplay.innerHTML += `
            <div>
                <div class="joint-bar"><div class="joint-fill" id="j-fill-${i}"></div></div>
                <div style="font-size: 0.75rem">J${i+1}</div>
                <div style="font-size: 0.75rem" id="j-val-${i}">0.00</div>
            </div>
        `;
        
        // Motion Control sliders
        jointSliders.innerHTML += `
            <div class="form-group">
                <label>Joint ${i+1}: <span id="j-slider-val-${i}">0.00</span> rad</label>
                <input type="range" id="j-slider-${i}" min="-2.9" max="2.9" step="0.01" value="0">
            </div>
        `;
    }

    // Connect WebSockets
    let isConnected = false;
    const statusIndicator = document.getElementById('connection-status');
    const modeBadge = document.getElementById('robot-mode-badge');

    function updateConnectionStatus(status) {
        isConnected = status;
        statusIndicator.className = 'status-indicator ' + (status ? 'online' : 'offline');
        statusIndicator.title = status ? '已连接' : '离线';
    }

    apiClient.connectWS('robot_state', (msg) => {
        if (msg.type === 'robot_state') {
            const modes = {
                'OTHER': '其他', 'IDLE': '空闲', 'MOVE': '运动中', 
                'GUIDING': '引导模式', 'REFLEX': '反射保护', 
                'USER_STOPPED': '用户停止', 'ERROR_RECOVERY': '错误恢复中'
            };
            const modeName = modes[msg.mode] || msg.mode || '未知';
            modeBadge.textContent = modeName;
            modeBadge.className = 'robot-status-badge';
            if (msg.mode === 'IDLE') modeBadge.classList.add('mode-idle');
            else if (msg.mode === 'MOVE') modeBadge.classList.add('mode-move');
            else modeBadge.classList.add('mode-error');
        }
    }, updateConnectionStatus);

    apiClient.connectWS('joint_states', (msg) => {
        if (msg.type === 'joint_states') {
            currentJoints = msg.data.positions;
            for (let i = 0; i < 7; i++) {
                const val = currentJoints[i];
                document.getElementById(`j-val-${i}`).textContent = val.toFixed(2);
                
                // Map approx -2.9 to 2.9 rad to 0-100%
                let percentage = ((val + 2.9) / 5.8) * 100;
                percentage = Math.max(0, Math.min(100, percentage));
                document.getElementById(`j-fill-${i}`).style.height = `${percentage}%`;
            }
        }
    }, updateConnectionStatus);

    // --- Motion Control Actions ---
    for(let i=0; i<7; i++){
        const slider = document.getElementById(`j-slider-${i}`);
        slider.addEventListener('input', (e) => {
            document.getElementById(`j-slider-val-${i}`).textContent = parseFloat(e.target.value).toFixed(2);
        });
    }

    const velScaleSlider = document.getElementById('vel-scale');
    velScaleSlider.addEventListener('input', (e) => {
        document.getElementById('vel-scale-val').textContent = e.target.value;
    });

    const motionLog = document.getElementById('motion-log');
    function logMotion(msg) {
        motionLog.innerHTML += `<div>[${new Date().toLocaleTimeString()}] ${msg}</div>`;
        motionLog.scrollTop = motionLog.scrollHeight;
    }

    document.getElementById('btn-move-ptp').addEventListener('click', async () => {
        const target = [];
        for(let i=0; i<7; i++){
            target.push(parseFloat(document.getElementById(`j-slider-${i}`).value));
        }
        const velScale = parseFloat(velScaleSlider.value);
        
        logMotion(`发送 PTP 运动指令...`);
        const res = await apiClient.moveJoints(target, velScale);
        if(res.ok) {
            logMotion(`成功: 任务 ID ${res.data.task_id}`);
        } else {
            logMotion(`错误: ${res.data.detail || JSON.stringify(res.data)}`);
        }
    });

    document.getElementById('btn-recover').addEventListener('click', async () => {
        logMotion(`发送错误恢复指令...`);
        const res = await apiClient.errorRecovery();
        logMotion(res.ok ? "成功" : "失败");
    });

    // --- Gripper Actions ---
    const btnGrasp = document.getElementById('btn-grasp');
    const btnMoveGripper = document.getElementById('btn-move-gripper');
    const btnHoming = document.getElementById('btn-homing');

    btnGrasp.addEventListener('click', async () => {
        const w = document.getElementById('grasp-width').value;
        const s = document.getElementById('grasp-speed').value;
        const f = document.getElementById('grasp-force').value;
        const res = await apiClient.grasp(w, s, f);
        if(res.ok) alert("抓取指令已发送");
        else alert("失败: " + JSON.stringify(res.data));
    });

    btnMoveGripper.addEventListener('click', async () => {
        const w = document.getElementById('move-width').value;
        const s = document.getElementById('move-speed').value;
        const res = await apiClient.moveGripper(w, s);
        if(res.ok) alert("移动指令已发送");
    });

    btnHoming.addEventListener('click', async () => {
        const res = await apiClient.homingGripper();
        if(res.ok) alert("回零指令已发送");
    });

    // --- API Tester ---
    document.getElementById('btn-send-api').addEventListener('click', async () => {
        const method = document.getElementById('api-method').value;
        const path = document.getElementById('api-path').value;
        const bodyStr = document.getElementById('api-body').value;
        let body = null;
        if(bodyStr) {
            try { body = JSON.parse(bodyStr); } 
            catch(e) { alert("Invalid JSON body"); return; }
        }
        
        document.getElementById('api-response').textContent = "加载中...";
        const start = Date.now();
        const res = await apiClient.request(method, path, body);
        const elapsed = Date.now() - start;
        
        document.getElementById('api-response').textContent = 
            `状态码: ${res.status} (${elapsed}ms)\n\n` + 
            JSON.stringify(res.data, null, 2);
    });

    // --- Controllers ---
    document.getElementById('btn-refresh-ctrl').addEventListener('click', async () => {
        const res = await apiClient.listControllers();
        const tbody = document.querySelector('#controllers-table tbody');
        tbody.innerHTML = '';
        if(res.ok && res.data.controllers) {
            res.data.controllers.forEach(ctrl => {
                tbody.innerHTML += `
                    <tr>
                        <td>${ctrl.name}</td>
                        <td>
                            <span class="robot-status-badge ${ctrl.state === 'active' ? 'mode-idle' : 'mode-error'}">${ctrl.state === 'active' ? '运行中' : '已停止'}</span>
                        </td>
                        <td><button class="btn btn-secondary">切换</button></td>
                    </tr>
                `;
            });
        }
    });
});
