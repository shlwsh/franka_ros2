# TCM-FD / 跨数据集：下载与导入指南

> **更新**：2026-05-30  
> **对照**：[PaperI_改进方案.md](./PaperI_改进方案.md) §2.2、[论文I_科研任务优化安排_20260530.md](./论文I_科研任务优化安排_20260530.md) Phase 3

---

## 1. 先分清三个名字（避免混淆）

| 名称 | 是什么 | 本仓库状态 |
|------|--------|------------|
| **ShezhenV3-COCO / TCM-Tongue v3** | 主实验数据集（6719 张，COCO 标注） | ✅ 已用 `import_shezhenv3.py` |
| **TCM-FD**（规划路径） | 跨数据集泛化（曝光/环境差异） | ❌ **尚无** `doctor/datasets/vision/tcm-fd/` 与 import 脚本 |
| **`cross_tcm_fd.csv`** | M5 指标文件名 | ⚠️ **当前**仅对 **ShezhenV3 val** 算 Spearman，不是真实第二数据集 |

当前 `experiments/cross_dataset_report.py` 读取的是 `calibration_val.csv`（主集 val 标定结果），文件名历史遗留。真正跨集需**另下载数据集 + 新 import + 重跑标定**。

---

## 2. 主集（若尚未下载）：ShezhenV3 / TCM-Tongue

与跨集无关，但 Phase 3 前主集须就绪。

### 2.1 官方来源

| 渠道 | 链接 |
|------|------|
| GitHub（网盘链接在 README） | https://github.com/btbuIntelliSense/Intelligent-tongue-diagnosis-detection-dataset |
| Dryad（学术归档，~2.34 GB） | https://doi.org/10.5061/dryad.1c59zw48r |
| 论文 | arXiv:2507.18288（TCM-Tongue） |

README 内提供 **百度网盘** 下载；解压后目录结构应含 `train/val/test`，每 split 下有 `images/` 与 `annotations/*.json`（COCO）。

### 2.2 本机路径（WSL 示例）

与 `experiments/configs/tcm_paths.yaml` 一致：

```yaml
dataset_root: /mnt/d/BaiduNetdiskDownload/shezhenv3-coco/shezhenv3-coco
```

Windows 下载后可在 WSL 用 `/mnt/d/...` 挂载访问。

### 2.3 导入主集

```bash
cd /home/ros/work/franka_ros2/doctor/paper1
python3 scripts/import_shezhenv3.py --config experiments/configs/tcm_paths.yaml
```

产出：`experiments/splits/tcm_{train,val,test}.json`

---

## 3. 跨数据集选哪个？（改进方案 §2.2）

改进方案列出两类辅集，**仓库尚未绑定唯一官方「TCM-FD」压缩包**，需择一或组合使用：

| 优先级 | 数据集 | 特点 | 下载难度 |
|--------|--------|------|----------|
| **A（推荐）** | **Tongue Image Dataset with Inquiry Data** | 与方案文档名称一致；含问诊信息 | ScienceDB 注册下载 |
| **B** | **FDU-TCMSU**（FDU/SHUTCM） | 非专业环境拍摄，域差异大；V18 规划目录名 `tcm-fd` 常指此类 | GitHub 写明需联系作者 |
| **C** | **TongueDx** | 4650 人、自然场景 | Google 表单申请，约 1 小时～1 周 |
| **D** | **IEEE/Harvard 老年舌象** | 668 张、专家标注 | Dataverse 需登录 |

论文中可写：**「跨集：Inquiry Data（主）+ FDU 环境差异（辅）」**，不必拘泥缩写 TCM-FD 字面。

---

## 4. 各跨集下载步骤

### 4.1 Tongue Image Dataset with Inquiry Data（方案直称）

1. 打开 ScienceDB 数据集页：  
   https://www.scidb.cn/en/detail?dataSetId=8417299de5ef4f3db5ec62e01a969d54  
2. 注册/登录 ScienceDB，按页面 **Download** 获取压缩包。  
3. 解压到本仓库规划目录（建议）：

```text
doctor/datasets/vision/tcm-inquiry/raw/    # 原始图像
doctor/datasets/vision/tcm-inquiry/meta/   # 标签/问诊 CSV（若有）
```

4. 阅读压缩包内 README，确认：图像格式（jpg/png）、是否有 **train/val/test** 或需自行划分。

> 若页面仅中文，可用同一 dataSetId 在 https://www.scidb.cn 检索。

### 4.2 FDU-TCMSU（对应 V18 路径 `tcm-fd`）

1. 仓库：https://github.com/FDUXilly/FDU-TCMSU  
2. README 中 **How to get the Dataset** 曾为 “Updating”——需：  
   - 在 GitHub 提 Issue，或  
   - 邮件联系作者（论文：Li et al., BIBM 2019）申请 **非商业科研** 使用。  
3. 获得链接后，约 **5600 张 JPG** 下载到：

```text
doctor/datasets/vision/tcm-fd/raw/
```

4. 该集**无标准 COCO 框**时，跨集实验可 `use_roi: false` 全图 Edge-IQA，或在论文中说明域差异实验不设舌框 ROI。

### 4.3 TongueDx（可选补充）

1. 仓库：https://github.com/tonguedx/tonguedx  
2. 填写申请表：https://forms.gle/GJfuYKZwjYTRUdJH6（建议 Gmail）  
3. 收到邮件链接后下载，解压至 `doctor/datasets/vision/tonguedx/raw/`  
4. 许可：**CC-BY-NC-SA 4.0**（注意非商业条款与论文投稿一致性）。

### 4.4 IEEE 老年舌象（小样本快速试点）

1. 页面：https://ieee-dataport.org/open-access/annotated-dataset-tongue-images  
2. 注册 IEEE 账号后下载；或 DOI 镜像：  
   https://doi.org/10.7910/DVN/COJZMQ  
3. 规模较小（668 张），适合 **M5 快速试点**，再换大集做定稿。

---

## 5. 推荐目录结构（与 V18/V19 一致）

在 `franka_ros2` 根目录创建（当前仓库**无** `doctor/datasets/`，需手动建）：

```text
doctor/datasets/
├── vision/
│   ├── tcm-fd/              # FDU-TCMSU 或你认定的「TCM-FD」
│   │   ├── raw/
│   │   └── reports/download_log.md
│   ├── tcm-inquiry/         # Inquiry Data
│   │   ├── raw/
│   │   └── splits/          # 自建 val/test JSON
│   └── tcm-tongue/          # 可选：与 shezhenv3 镜像同数据
└── manifests/
    └── cross_datasets.yaml    # 记录路径、许可、下载日期
```

`download_log.md` 建议记录：来源 URL、条数、MD5、许可、下载日期（审稿可追溯）。

---

## 6. 导入与跨集验证流程（待实现 → 你可按此验收）

主集已有模板 `scripts/import_shezhenv3.py`。跨集建议新增（**尚未入库**，Phase 3 开发项）：

| 步骤 | 命令（规划） | 产出 |
|------|--------------|------|
| 1. 配置路径 | `experiments/configs/tcm_fd_paths.yaml` | `dataset_root` 指向跨集 raw |
| 2. 生成 split JSON | `python3 scripts/import_tcm_fd.py` | `experiments/splits/tcm_fd_val.json` |
| 3. 构造 clear/blur 标签 | 物理退化或数据集自带质量标签 | 供 τ 标定 |
| 4. 标定 τ（跨集） | `calibrate_tau_tcm.py --split tcm_fd_val` | `recommended_tau_fd.json` |
| 5. M5 Spearman | 扩展 `cross_dataset_report.py --csv <跨集标定>` | `cross_tcm_fd.csv`（真实跨集） |
| 6. 可选：小矩阵 | `run_matrix_tcm.py` + 跨集 test JSON | 跨集 M2 表 |

### 6.1 跨集标签从哪来？

Edge-IQA 标定需要 **clear vs blur**（或二值「可上传/不可上传」）：

| 来源 | 做法 |
|------|------|
| 无标签 | 与主集相同：对清晰图做 `blur_bytes` 合成模糊对（`run_matrix_tcm` 已支持） |
| 有质量/清晰度字段 | 直接映射为 label |
| Inquiry/FDU 仅有病理类 | **不能**直接当 IQA 标签；需另选代理任务或抽样人工 |

### 6.2 最小跨集试点（不下载大集时）

若下载受阻，改进方案允许 **「合成跨集」**（V18 P5-T02）：

```bash
cd doctor/paper1
python3 scripts/synth_degrade.py
python3 experiments/edge_iqa/calibrate_tau.py
python3 experiments/cross_dataset_report.py
```

此时 M5 反映的是**合成退化 cohort**，论文需写明「真实 TCM-FD 待补」。

---

## 7. 配置示例（跨集 import 完成后）

`experiments/configs/tcm_fd_paths.yaml`（示例，路径按本机修改）：

```yaml
dataset_root: /mnt/d/datasets/tcm-fd/raw
dataset_name: tcm-fd-fdu
splits: [val, test]
use_roi: false
roi_padding: 0.08
```

WSL 访问 Windows 盘：`/mnt/d/...`；纯 Linux 则 `/home/ros/datasets/...`。

---

## 8. 检查清单

- [ ] 主集 `tcm_test.json` 存在且 `dataset_root` 可读  
- [ ] 跨集 raw 图像数 ≥ 200（M5 建议抽样 ≥200）  
- [ ] `download_log.md` 记录许可与来源  
- [ ] 跨集 `calibration_val_*.csv` 与主集 **分开** 标定 τ  
- [ ] 论文 Table/正文区分「主集 ShezhenV3」与「跨集名称」  
- [ ] 更新 `cross_dataset_report.py` 数据源字段（勿再用主集冒充 `cross_tcm_fd`）

---

## 9. 相关命令速查

```bash
# 主集导入（已有）
python3 scripts/import_shezhenv3.py

# 主集标定 + 当前 M5（实为同集 val）
python3 experiments/edge_iqa/calibrate_tau_tcm.py
python3 experiments/cross_dataset_report.py

# 跨集（待 import 脚本完成后）
# python3 scripts/import_tcm_fd.py --config experiments/configs/tcm_fd_paths.yaml
# python3 experiments/edge_iqa/calibrate_tau_tcm.py --config ... --max-val 400
# python3 experiments/cross_dataset_report.py --calibration experiments/results/calibration_val_fd.csv
```

---

## 10. 常见问题

**Q：TCM-FD 和 TCM-Tongue 是同一个吗？**  
A：不是。主实验用的是 **TCM-Tongue v3（ShezhenV3-COCO）**；**TCM-FD** 在规划里指**另一个**跨域舌象来源（常为 FDU 非控环境集或 Inquiry Data）。

**Q：我已经有 shezhenv3-coco，还要下载吗？**  
A：主集不必重复；跨集仍需**另下** §4 中 A/B/C/D 之一。

**Q：下载要多久？**  
A：主集网盘约 **2–3 GB**，视网速 10–60 分钟；FDU/Inquiry 视作者回复，**0.5–3 天**不等。

**Q：谁来实现 `import_tcm_fd.py`？**  
A：Phase 3 开发项；格式确定后可仿 `import_shezhenv3.py` 写 COCO/文件夹扫描版。
