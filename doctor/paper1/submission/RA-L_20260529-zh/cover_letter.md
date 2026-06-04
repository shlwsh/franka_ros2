# 投稿信（草稿）— RA-L / RCIM

**日期：** 2026-06-04  
**稿件：** *Confidence-Aware Edge Routing for Robotic TCM Tongue Imaging: Edge-IQA and LangGraph Closed-Loop Acquisition*  
（中文：面向机器人中医舌象采集的置信度感知边侧路由：Edge-IQA 与 LangGraph 闭环采集）  
**作者：** 石洪雷、赵涓涓（Honglei Shi, Juanjuan Zhao）  
**单位：** 太原理工大学（Taiyuan University of Technology）  
**通讯作者：** 石洪雷（Honglei Shi），太原理工大学  
**电子邮箱：** shihonglei0042@link.tyut.edu.cn

---

尊敬的编辑：

谨呈本稿件，申请作为 **Regular Paper（常规论文）** 发表于 *IEEE Robotics and Automation Letters*（IEEE 机器人与自动化快报，RA-L），或备选发表于 *Robotics and Computer-Integrated Manufacturing*（机器人与计算机集成制造，RCIM）。本工作针对云–边–端协同场景下，机器人 **中医（TCM）舌象采集过程中的质量门控（acquisition-time quality gating）** 问题。

## 摘要（稿件要点）

远程诊疗流水线常将相机每一帧上传云端，导致模糊或过曝舌象浪费带宽，并抬高往返时延（RTT）。我们在边侧网关上部署轻量级 **Edge-IQA** 打分器与 **LangGraph** 置信度感知路由器（位于 1\,kHz ROS~2 控制环之外），并在公开 **ShezhenV3-COCO** 语料（6{,}719 张图像）及辅助 **Franka** 执行轨上完成验证。

## 贡献

1. **基于 COCO 舌区 ROI 的 Edge-IQA** — $O(HW)$ CPU 可解释模糊/曝光标志；在 572 对验证样本上标定 $\tau_{B2}{=}0.465$（512\,px 下 p95 $\approx$ 9.6\,ms）。
2. **可审计三分支路由** — 在重试预算 $K{=}2$ 下实现 upload / edge resample / fail-safe，并以 JSONL 记录便于复现。
3. **双轨评估** — 离线主矩阵：553 张测试图（500 帧 $\times$ 3 随机种子）；独立 M6 Franka 试验不改变 Table~II 统计。

## 主要结果（Table II，脚本生成）

| 指标 | B0（朴素全上传） | B2（本文方法） |
|------|------------------|----------------|
| M1 RTT p50 | 374.0 ms | **208.3 ms** |
| M2 有效帧率 | 0.560 | **0.604** |

学习型 MobileNet 基线 B3/B4 在重标定阈值下 M2 $\approx 0.93$，但边侧 RTT 更高；我们如实将其作为对照，而非主推部署路径。  
Pareto 图（M2 vs.\ M1 p50）及附录中 BRISQUE / NIQE 类打分器在相同 LangGraph 外壳下的结果，进一步阐明有效帧率与时延的权衡。

## 可复现性与伦理

数据划分、标定 JSON 及一键复现（`scripts/paper1_run_tcm_full.sh`、`REPRODUCE.md`）随 `doctor/paper1/` 提供。  
扩展表、NR-IQA 基线、分层 M2、部署说明与 B2 walkthrough 见 `doctor/paper1/supplementary/SUPPLEMENTARY.md`（RA-L 不允许在 8 页 PDF 之外附加附录正文）。
ShezhenV3 图像仍位于用户配置的数据集根目录。离线实验使用公开语料；**未招募新的人体受试者**；JSONL 日志不含患者标识。生成式 AI 仅辅助英文行文与文档整理；**所有指标均经** `experiments/results/*.json` **核对**。

## 与 RA-L 的契合度

本文将 **机器人采集**、**边侧推理** 与 **闭环策略** 相结合，并在 FR3 上展示硬件在环可行性，同时保持主证据链离线、可审计——符合 RA-L 对严谨机器人系统贡献的侧重。

## 声明

- 稿件为原创，且未同时投往其他期刊。
- 全体作者均已同意投稿。
- **利益冲突：** 无声明项。
- **建议审稿人：** [可选列表]

此致  
敬礼  

石洪雷（Honglei Shi）  
太原理工大学（Taiyuan University of Technology）  
E-mail: shihonglei0042@link.tyut.edu.cn
