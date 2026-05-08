"""
Playwright 验证脚本：验证前端页面通过指令控制机械臂运动
通过浏览器自动化操作前端 UI，发送 PTP 运动指令，并验证关节位置是否真正变化。
"""
from playwright.sync_api import sync_playwright
import subprocess
import time
import json

def get_joint_positions():
    """通过 ROS 2 获取当前关节位置"""
    result = subprocess.run(
        ['bash', '-c', 
         'source /opt/ros/jazzy/setup.bash && '
         'source install/setup.bash && '
         'ros2 topic echo /joint_states --once 2>/dev/null'],
        capture_output=True, text=True, timeout=10,
        cwd='/home/smz/projects/franka_ros2'
    )
    positions = []
    in_positions = False
    for line in result.stdout.split('\n'):
        if 'position:' in line:
            in_positions = True
            continue
        if in_positions:
            line = line.strip()
            if line.startswith('-'):
                positions.append(float(line[2:]))
            else:
                break
    return positions[:7]  # 只取前7个关节（不含手指）

def run():
    print("=" * 60)
    print("Playwright 前端控制机械臂运动验证")
    print("=" * 60)
    
    # 1. 记录初始关节位置
    print("\n[步骤 1] 获取运动前关节位置...")
    before = get_joint_positions()
    print(f"  初始位置: {[f'{v:.4f}' for v in before]}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 2. 打开前端页面
        print("\n[步骤 2] 打开前端 Dashboard (http://localhost:8080)...")
        page.goto("http://localhost:8080", wait_until="networkidle")
        title = page.title()
        print(f"  页面标题: {title}")
        assert title == "Franka API Dashboard", f"页面标题不匹配: {title}"
        
        # 3. 输入 API Key
        print("\n[步骤 3] 输入 API Key...")
        page.fill("#api-key-input", "franka-api-default-key")
        
        # 4. 导航到 Motion Control
        print("\n[步骤 4] 导航到 Motion Control 页面...")
        page.click("a[data-target='motion-view']")
        page.wait_for_selector("#joint-sliders input[type='range']", timeout=5000)
        print("  Joint Sliders 已加载")
        
        # 5. 设置目标关节角度（改变 J1 到 -0.5）
        target_j1 = -0.5
        print(f"\n[步骤 5] 设置 Joint 1 目标角度为 {target_j1} rad...")
        slider = page.locator("#j-slider-0")
        slider.evaluate(f"el => {{ el.value = {target_j1}; el.dispatchEvent(new Event('input')) }}")
        display_val = page.locator("#j-slider-val-0").inner_text()
        print(f"  前端显示值: {display_val} rad")
        
        # 6. 点击执行 PTP 运动按钮
        print("\n[步骤 6] 点击 'Execute PTP Motion' 按钮...")
        page.click("#btn-move-ptp")
        
        # 7. 等待前端日志更新
        print("  等待前端反馈...")
        page.wait_for_function(
            'document.getElementById("motion-log").innerText.includes("Success") || '
            'document.getElementById("motion-log").innerText.includes("Error")',
            timeout=10000
        )
        log_text = page.locator("#motion-log").inner_text()
        print(f"  前端日志: {log_text.strip()}")
        
        # 8. 等待 MoveIt 执行完毕
        print("\n[步骤 7] 等待机械臂运动执行完毕 (8秒)...")
        time.sleep(8)
        
        browser.close()
    
    # 9. 检查运动后关节位置
    print("\n[步骤 8] 获取运动后关节位置...")
    after = get_joint_positions()
    print(f"  最终位置: {[f'{v:.4f}' for v in after]}")
    
    # 10. 验证
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)
    
    j1_moved = abs(after[0] - before[0]) > 0.01
    j1_close_to_target = abs(after[0] - target_j1) < 0.1
    
    print(f"  Joint 1 运动前:  {before[0]:.4f} rad")
    print(f"  Joint 1 运动后:  {after[0]:.4f} rad")
    print(f"  Joint 1 目标值:  {target_j1:.4f} rad")
    print(f"  Joint 1 是否移动: {'✅ 是' if j1_moved else '❌ 否'}")
    print(f"  Joint 1 到达目标: {'✅ 是' if j1_close_to_target else '❌ 否'}")
    
    if j1_moved and j1_close_to_target:
        print("\n🎉 验证通过！前端页面成功通过指令控制了机械臂运动！")
        return True
    else:
        print("\n❌ 验证失败！机械臂没有正确移动。")
        return False

if __name__ == "__main__":
    success = run()
    exit(0 if success else 1)
