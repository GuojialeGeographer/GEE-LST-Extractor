# GEE环境数据提取工具 - 完整使用指南

## 🎯 系统概述

这是一个**生产级的、Notebook驱动的、一键运行**的GEE环境数据提取工具。

### 核心特点

✅ **Notebook-First** - 所有操作通过Jupyter Notebook完成
✅ **一键运行** - 最少用户干预
✅ **断点续传** - 支持中断后恢复
✅ **大规模友好** - 支持百万级数据点
✅ **智能调度** - 自动遵守GEE配额限制
✅ **进度可视化** - 实时显示进度

---

## 🚀 快速开始（3步）

### Step 1: 打开Notebook

```bash
# 进入项目目录
cd LST-Tools

# 启动Jupyter
jupyter notebook

# 打开 GEE_Extractor_Master.ipynb
```

### Step 2: 修改数据文件路径

在Notebook的Step 5中，修改数据文件路径：

```python
# 将这行：
data_file = "../data/your_data.csv"

# 改为你的数据文件路径：
data_file = "/path/to/your/social_media_data.csv"
```

### Step 3: 运行所有Cell

**菜单** → **Run All**（或按 `Shift + Enter` 逐个运行）

完成！

---

## 📖 详细使用流程

### 阶段1：准备数据

#### 数据格式要求

你的数据文件（CSV）必须包含以下列：

```csv
user_id,lng,lat,create_time,location,city
12345,116.4074,39.9042,2023-01-15 14:30:00,Beijing
12346,116.3972,39.9165,2023-01-16 15:20:00,Shanghai
```

**必需列**：
- `lng`: 经度
- `lat`: 纬度

**可选列**：
- `user_id`: 用户ID
- `timestamp`: 时间戳
- `location`: 位置名称
- `city`: 城市名

#### 数据规模建议

| 数据点数 | 预计时间 | 批次数 |
|---------|---------|--------|
| 100 | 10分钟 | 1 |
| 1,000 | 30分钟 | 1 |
| 10,000 | 1小时 | 2 |
| 100,000 | 3-5小时 | 20 |
| 1,000,000 | 1天 | 200 |

---

### 阶段2：配置数据源

编辑 `config/data_sources.yaml`：

```yaml
data_sources:
  LST:
    enabled: true    # 启用LST

  NDVI:
    enabled: true    # 启用NDVI

  PM25:
    enabled: false   # 暂时禁用（需要时启用）
```

---

### 阶段3：运行提取

#### 3.1 打开Notebook

```bash
jupyter notebook GEE_Extractor_Master.ipynb
```

#### 3.2 检查GEE认证

运行Step 2，会自动检查GEE认证状态。

如果未认证，会提示运行：
```python
import ee
ee.Authenticate()
```

#### 3.3 恢复或新建会话

运行Step 3，系统会：
- 自动检测是否有之前的会话
- 显示会话摘要
- 询问是否恢复

**恢复会话**：
- 从中断点继续
- 保留已完成的进度

**新建会话**：
- 清除之前的进度
- 从头开始

#### 3.4 一键运行

**方法1：Run All（推荐）**
- 菜单：Cell → Run All
- 所有Cell会自动运行

**方法2：逐个运行**
- 按 `Shift + Enter`
- 逐个Cell运行
- 可以看到每步的输出

#### 3.5 监控进度

系统会自动显示：
```
============================================================
执行 186 个任务
============================================================
并发限制：3
速率限制：10 任务/分钟
============================================================

[1/186] 任务 lst_batch0...
  ✓ 任务 lst_batch0 已提交

[2/186] 任务 lst_batch1...
  ✓ 任务 lst_batch1 已提交

...

进度：10/186 (5.4%)
```

---

## 🔧 高级功能

### 断点续传

#### 场景：Notebook意外关闭

1. 重新打开Notebook
2. 运行Step 3
3. 选择"恢复之前的会话"
4. 从Step 9继续执行

#### 自动保存

系统会自动保存：
- 每10个批次保存一次
- 每个阶段完成后保存
- 会话状态持续更新

### 批量处理多个月份

如果需要处理多个月份，可以：

**方法1：循环处理**
```python
# 在Step 8中添加循环
months = [(2023, 1), (2023, 2), (2023, 3)]

for year, month in months:
    print(f"\n处理 {year}年{month}月...")
    # 提取该月数据
    # 保存结果
```

**方法2：创建多个月份配置**
```yaml
# config/batch_config.yaml

months:
  - year: 2023
    month: 1
  - year: 2023
    month: 2
  - year: 2023
    month: 3
```

### 自定义提取参数

#### 修改时间窗口

在 `config/data_sources.yaml` 中：

```yaml
LST:
  parameters:
    time_windows: [0, 7, 15, 30]  # 天数
  quality:
    temporal_windows: [0, 7, 15, 30]
```

#### 修改网格精度

在Notebook的Step 6中：

```python
# 修改精度
grid_manager = GridManager(precision=4)  # 4位小数 ≈ 11米
# grid_manager = GridManager(precision=5)  # 5位小数 ≈ 1米
```

#### 修改批次大小

在Notebook的Step 7中：

```python
batch_size = 5000  # 默认（推荐）
# batch_size = 10000  # 更大（可能超时）
# batch_size = 1000   # 更小（更稳定）
```

---

## 📊 结果文件

### 输出文件

提取完成后，会在 `output/` 目录生成：

```
output/
├── final_results_2023_01.csv           # CSV格式
├── final_results_2023_01.parquet       # Parquet格式（更快）
└── quality_report_2023_01.txt         # 质量报告
```

### CSV格式

```csv
user_id,lng,lat,create_time,...,LST,LST_quality_flag,LST_extraction_method
12345,116.407,39.904,2023-01-15,...,9.16,direct,exact
12346,116.397,39.916,2023-01-16,...,8.92,extended_window,extended_window
```

### 质量报告

```
质量报告
========================================

LST:
  覆盖率：95.2%
  均值：18.50
  标准差：8.30
  范围：[-5.2, 35.8]

NDVI:
  覆盖率：93.8%
  均值：0.65
  标准差：0.12
  范围：[0.12, 0.89]
```

---

## 🎯 使用场景示例

### 场景1：单个城市，单个月份

```python
# 直接运行Notebook
# 修改数据文件路径
# 运行所有Cell
```

### 场景2：单个城市，多个月份

```python
# 创建循环
cities = ['Beijing', 'Shanghai']
months = [(2023, m) for m in range(1, 13)]

for city in cities:
    for year, month in months:
        print(f"\n处理：{city} {year}-{month:02d}")
        # 运行提取
        # 保存结果
```

### 场景3：多个城市，多个月份

创建配置文件 `config/multi_cities.yaml`：

```yaml
cities:
  Beijing:
    bbox: [116.0, 40.0, 117.0, 41.0]
    center: [116.4, 40.2]
  Shanghai:
    bbox: [121.0, 31.0, 122.0, 32.0]
    center: [121.5, 31.2]

months:
  - year: 2023
    months: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
```

---

## ⚠️ 常见问题

### Q1: Notebook运行很慢怎么办？

**A**: 这是正常的！
- GEE任务需要时间
- 大数据集需要几小时
- 建议：
  - 让Notebook后台运行
  - 定期检查进度
  - 利用断点续传功能

### Q2: 如何知道任务完成？

**A**: 系统会自动显示：
- 实时进度
- 完成百分比
- 每个批次的状态

### Q3: 中间可以关闭Notebook吗？

**A**: 可以！
- 系统会自动保存进度
- 重新打开时选择"恢复会话"
- 从中断点继续

### Q4: 如何处理失败的任务？

**A**: 系统会：
- 自动识别失败任务
- 自动重试（最多3次）
- 标记最终失败的任务

你可以：
- 查看失败任务列表
- 手动重试特定任务
- 调整参数后重新运行

---

## 📚 相关文档

- [README.md](README.md) - 项目概述
- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - 开发计划
- [docs/METHODOLOGY.md](docs/METHODOLOGY.md) - 方法学文档

---

## 🎓 最佳实践

### 1. 数据准备

✅ **确保数据格式正确**
- 必需：lng, lat列
- 检查经纬度范围
- 移除重复数据

### 2. 配置优化

✅ **根据数据规模调整**
- 小数据（<1000）：批次大小1000
- 中等数据（1万-10万）：批次大小5000
- 大数据（>10万）：批次大小10000

✅ **选择合适的数据源**
- 从1-2个数据源开始
- 验证结果后再添加更多

### 3. 运行策略

✅ **分阶段运行**
- 先用小数据集测试
- 验证结果后运行完整数据
- 分批处理多个月份

✅ **监控和维护**
- 定期检查进度
- 保存中间结果
- 记录日志

---

## 🚀 立即开始

1. 打开 `GEE_Extractor_Master.ipynb`
2. 修改数据文件路径
3. 运行所有Cell
4. 等待完成

就这么简单！🎉

---

*更新日期：2026-03-12*
*版本：v1.0*
