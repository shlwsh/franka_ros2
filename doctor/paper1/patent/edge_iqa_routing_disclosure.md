# 专利交底提纲（可选）— Edge-IQA + 置信度路由

> **更新**：2026-06-04 · 与定稿论文 B0–B4、物理重采、负分离度披露一致

## 发明要点

1. 一种边侧舌象采集质量评价方法，融合 Laplacian 清晰度与曝光适宜度得到 $Q_{img}$，输出可解释 `flags`（blur / underexposed / overexposed）。  
2. 一种基于 $Q_{img}$ 与阈值 $\tau$、重试预算 $K$ 的三向路由方法（上传云 / 边缘重拍 / 失败安全），$\tau$ 由验证集 clear/blur **组中位数**标定（允许分数区间重叠）。  
3. 一种云–边–端协同采集闭环系统，边侧 FastAPI 网关通过子进程调用 IQA，LangGraph 状态机记录 JSONL 审计轨迹。  
4. 重拍通过**物理 Skill 等价变换**（曝光校正、模糊半径递减）更新 $Q_{img}$，禁止随机分数 uplift。  
5. 可选二级门控：Tier-A 可解释 Edge-IQA + Tier-B 学习 IQA（MobileNet）混合路由（对应论文 B4 Hybrid）。

## 实施例数据（ShezhenV3，非权利要求限制）

| 项 | 值 |
|----|-----|
| τ_B2 | 0.465 |
| separation_min_clear_max_blur | −0.541 |
| B2 M2 / M1 p50 vs B0 | 0.604 / 208 ms vs 0.560 / 374 ms |

## 从属权利要求方向

- $\tau$ 由 ROI 舌区验证集标定；COCO bbox + 8% padding。  
- 重拍通过预定义 FR3 关节 Skills（`go_to_tongue_pose`）或离线同构图像变换执行。  
- 主统计来自离线矩阵；机器人辅轨仅验证执行栈可行性。  

（正式文本待法务/导师审核）
