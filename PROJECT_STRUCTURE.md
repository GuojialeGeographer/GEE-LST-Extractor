# 📦 项目文件说明

## 完整文件清单

本文档列出了项目的所有文件及其用途，帮助您快速了解项目结构。

---

## 📁 根目录文件

### 核心文档

| 文件名 | 说明 | 必需 |
|--------|------|------|
| `README.md` | 主文档，包含完整的使用说明、技术细节、FAQ | ✅ |
| `QUICKSTART.md` | 10分钟快速开始指南 | ✅ |
| `LICENSE` | MIT开源许可证 | ✅ |
| `.gitignore` | Git忽略文件配置 | ✅ |

### 配置文件

| 文件名 | 说明 | 用途 |
|--------|------|------|
| `environment.yml` | Conda环境配置文件 | `conda env create -f environment.yml` |
| `requirements.txt` | Pip依赖包列表 | `pip install -r requirements.txt` |

### Jupyter Notebooks

| 文件名 | 说明 | 使用场景 |
|--------|------|----------|
| `GEE_LST_提取完整流程.ipynb` | **主Notebook**，包含所有5个阶段 | **推荐** - 一站式完整流程 |
| `阶段0_环境配置.ipynb` | 独立的环境配置和测试 | 首次使用或环境检测 |
| `阶段1_数据预处理.ipynb` | 独立的数据预处理 | 单独运行数据准备 |
| `阶段2_批次规划.ipynb` | 独立的批次规划 | 单独规划任务 |
| `阶段3_GEE算法配置.ipynb` | 独立的算法配置和测试 | 测试LST提取算法 |
| `阶段4_批量任务派发.ipynb` | 独立的任务派发 | 提交GEE任务 |
| `阶段5_数据合并与质检.ipynb` | 独立的数据合并和质量检查 | 合并最终结果 |

### 历史Notebooks（参考）

这些是开发过程中的版本，供参考：

| 文件名 | 说明 |
|--------|------|
| `LST_最终确定方案.ipynb` | 最终方案设计 |
| `修复版_使用高流量API.ipynb` | 高流量API测试 |
| `诊断任务失败.ipynb` | 任务诊断工具 |
| `最终版_LST批量提取.ipynb` | 批量提取版本 |

### 数据文件

| 文件名 | 说明 | 来源 |
|--------|------|------|
| `mobility_locations.csv` | **您的输入数据**（需提供） | 用户自己的数据 |
| `mobility_locations.csv.example` | 示例数据文件 | 项目提供（10行示例） |

### LST结果文件（运行后生成）

| 文件名 | 说明 | 生成时间 |
|--------|------|----------|
| `LST_2023_01_part1of22_*.csv` | 2023年1月第1批LST结果 | GEE处理完成后 |
| `LST_2023_01_part2of22_*.csv` | 2023年1月第2批LST结果 | GEE处理完成后 |
| `...` | 约186个CSV文件 | GEE处理完成后 |

**注意**：这些文件需要从Google Drive下载到`lst_results/`文件夹。

---

## 📁 temp/ 文件夹（自动生成）

运行阶段1后自动创建：

| 文件名 | 说明 | 大小（参考） |
|--------|------|-------------|
| `raw_with_grid_uid.csv` | 原始数据 + grid_uid | ~360 MB |
| `unique_grids.csv` | 去重的唯一时空网格 | ~120 MB |
| `batch_list.csv` | 批次任务清单 | < 1 MB |

**用途**：中间文件，用于阶段4和阶段5。

---

## 📁 lst_results/ 文件夹（需手动创建）

用户需从Google Drive下载LST结果到此文件夹：

```
lst_results/
├── LST_2023_01_part1of22_xxxxxx.csv
├── LST_2023_01_part2of22_xxxxxx.csv
├── ...
└── LST_2023_09_part7of7_xxxxxx.csv
```

**预计**：约186个CSV文件，总计50-100 MB。

---

## 📁 output/ 文件夹（自动生成）

运行阶段5后自动创建：

| 文件名 | 说明 | 用途 |
|--------|------|------|
| `final_data_with_lst.csv` | 完整数据（所有原始点+LST列） | **最终输出** |
| `final_data_with_lst_only.csv` | 仅有效LST数据（无NaN） | 分析使用 |
| `quality_report.txt` | 质量检查报告 | 验证数据质量 |

---

## 📁 docs/ 文件夹

详细文档：

| 文件名 | 说明 | 适合人群 |
|--------|------|----------|
| `METHODOLOGY.md` | 方法学详细文档 | 研究人员、审稿人 |
| `TROUBLESHOOTING.md` | 故障排除指南 | 遇到问题时 |

---

## 🗂️ 完整目录树

```
GEE-LST-Extractor/
│
├── README.md                          # 主文档 ✅
├── QUICKSTART.md                      # 快速开始 ✅
├── LICENSE                            # 许可证 ✅
├── .gitignore                         # Git配置 ✅
│
├── environment.yml                    # Conda环境 ✅
├── requirements.txt                   # Pip依赖 ✅
│
├── GEE_LST_提取完整流程.ipynb         # 主Notebook ✅
│
├── mobility_locations.csv             # 输入数据（用户需提供）
├── mobility_locations.csv.example     # 示例数据 ✅
│
├── temp/                              # 中间文件（自动生成）
│   ├── raw_with_grid_uid.csv
│   ├── unique_grids.csv
│   └── batch_list.csv
│
├── lst_results/                       # LST结果（用户需下载）
│   ├── LST_2023_01_part1of22_*.csv
│   ├── LST_2023_01_part2of22_*.csv
│   └── ...
│
├── output/                            # 最终输出（自动生成）
│   ├── final_data_with_lst.csv
│   ├── final_data_with_lst_only.csv
│   └── quality_report.txt
│
└── docs/                              # 详细文档
    ├── METHODOLOGY.md                 # 方法学 ✅
    └── TROUBLESHOOTING.md             # 故障排除 ✅
```

---

## 📝 使用哪个Notebook？

### 推荐流程

**大多数用户**：
```
使用 GEE_LST_提取完整流程.ipynb
```
- ✅ 包含所有5个阶段
- ✅ 详细的说明和注释
- ✅ 一次性完成整个流程

### 高级用户

**如果想分步运行**：
```
阶段0_环境配置.ipynb
    ↓
阶段1_数据预处理.ipynb
    ↓
阶段2_批次规划.ipynb
    ↓
阶段3_GEE算法配置.ipynb
    ↓
阶段4_批量任务派发.ipynb
    ↓
（等待GEE处理完成，下载CSV）
    ↓
阶段5_数据合并与质检.ipynb
```

**如果需要调试**：
- `诊断任务失败.ipynb` - 诊断GEE任务问题
- `修复版_使用高流量API.ipynb` - 测试网络连接

---

## 📊 文件大小参考

基于90万唯一网格、270万原始点的数据：

| 文件 | 预计大小 |
|------|----------|
| 输入数据 | 270 MB |
| temp/raw_with_grid_uid.csv | 360 MB |
| temp/unique_grids.csv | 120 MB |
| temp/batch_list.csv | < 1 MB |
| lst_results/*.csv (总计) | 50-100 MB |
| output/final_data_with_lst.csv | 500-600 MB |
| output/final_data_with_lst_only.csv | 480-550 MB |

**总计**：约1.5 GB（含所有中间文件）

---

## 🗑️ 哪些文件可以删除？

### 可以安全删除

- `temp/` - 中间文件（如果不需要重新运行阶段4）
- `lst_results/` - 已下载的LST结果（如果已合并）
- `output/` - 可以重新生成

### 不能删除

- `mobility_locations.csv` - 原始数据
- `temp/batch_list.csv` - 任务清单（除非已完成所有任务）

### 删除后恢复

```bash
# 如果删除了temp/，需要重新运行阶段1
jupyter notebook GEE_LST_提取完整流程.ipynb
# 运行阶段1即可重新生成temp/

# 如果删除了output/，需要重新运行阶段5
# 前提是lst_results/文件存在
```

---

## 📦 上传到GitHub前

### 必须上传

✅ README.md
✅ LICENSE
✅ 所有.ipynb文件
✅ environment.yml
✅ requirements.txt
✅ docs/ 文件夹
✅ mobility_locations.csv.example

### 不要上传

❌ mobility_locations.csv（您的真实数据）
❌ temp/ 文件夹（.gitignore已配置）
❌ lst_results/ 文件夹（.gitignore已配置）
❌ output/ 文件夹（.gitignore已配置）
❌ .earthengine/ 文件夹（GEE认证，.gitignore已配置）

### 检查.gitignore

确保`.gitignore`包含：
```
# 数据文件
*.csv
!mobility_locations.csv.example

# 中间文件
temp/
lst_results/
output/

# GEE
.earthengine/
ee-token*

# Jupyter
.ipynb_checkpoints/

# Python
__pycache__/
*.pyc
```

---

## 📋 发布检查清单

上传到GitHub前，请确认：

- [ ] README.md完整，包含安装、使用、FAQ
- [ ] LICENSE存在
- [ ] environment.yml可以成功创建环境
- [ ] 示例数据(mobility_locations.csv.example)存在
- [ ] 所有Notebook可以运行（用示例数据测试）
- [ ] .gitignore配置正确
- [ ] 敏感数据已移除（认证token、真实数据等）
- [ ] 文档链接正确（相对路径）
- [ ] 贡献指南存在（可选）

---

## 🔄 版本控制建议

### 主要版本 (v1.0.0)
- 完整的5阶段流程
- 详细的文档
- 经过测试

### 次要版本 (v1.1.0)
- 新功能（如支持其他卫星）
- 性能优化

### 修订版本 (v1.0.1)
- Bug修复
- 文档更新
- 小改进

---

*最后更新：2026-03-04*
