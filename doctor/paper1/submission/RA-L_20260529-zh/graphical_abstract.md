# 图形摘要（RA-L 可选）— 论文 I

**标题：** Confidence-Aware Edge Routing for Robotic TCM Tongue Imaging  
（面向机器人中医舌象采集的置信度感知边侧路由）

## 版式（单幅横版）

```
[ FR3 机械臂 + 相机 ] --> [ 边侧网关 ]
                              |
                    Edge-IQA (Q_img, flags)
                              |
                    LangGraph 路由器
                     /      |      \
            upload_cloud  resample_edge  fail_safe
                              |
                    [ 云端 TCM 分析 ]
```

## 关键数字（Table II，仿真 RTT）

| | B0 | B2 |
|---|-----|-----|
| M1 p50 | 374 ms | **208 ms** |
| M2 | 0.560 | **0.604** |

## 图注（≤ 80 英文词；投稿系统常用英文，以下为中文对照）

**英文投稿用（与英文包一致）：**

Robotic tongue imaging for TCM tele-diagnosis couples FR3 acquisition with edge-side Edge-IQA and LangGraph routing.
Low-quality frames are filtered or re-captured before cloud upload, cutting median RTT under a documented latency model while improving valid-frame rate on ShezhenV3-COCO.

**中文对照：**

面向 TCM 远程诊疗的机器人舌象采集将 FR3 采集与边侧 Edge-IQA、LangGraph 路由相结合。低质量帧在上云前被过滤或触发边侧重采，在文档化延迟模型下降低中位 RTT，并在 ShezhenV3-COCO 上提高有效帧率。

## 素材

投稿时可导出 `figures/fig1_system_overview.svg`，或由 Fig.1 + Pareto 插图（`fig7_pareto_m2_m1.pdf`）合成 1200×600 PNG。
