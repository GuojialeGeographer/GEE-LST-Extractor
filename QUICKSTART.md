# 🚀 快速开始指南

本指南帮助您在10分钟内完成环境配置并运行第一个测试。

---

## 📋 前置条件

在开始之前，请确保您有：

- ✅ **Anaconda或Miniconda**已安装
  - 下载：https://www.anaconda.com/ 或 https://docs.conda.io/en/latest/miniconda.html
  - 验证：在终端运行 `conda --version`

- ✅ **Google账号**
  - 用于访问Google Earth Engine
  - 如果没有，注册：https://accounts.google.com/

- ✅ **网络连接**
  - 能够访问Google服务
  - 如果在海外，可能需要VPN

- ✅ **数据文件**
  - 您的轨迹数据CSV文件
  - 包含列：lng, lat, create_time

---

## 步骤1：创建项目目录（5分钟）

### 1.1 下载项目

```bash
# 如果从GitHub克隆
git clone https://github.com/yourusername/GEE-LST-Extractor.git
cd GEE-LST-Extractor

# 或直接下载ZIP并解压
```

### 1.2 创建Conda环境

```bash
# 使用提供的配置文件
conda env create -f environment.yml

# 激活环境
conda activate geelst

# 验证
python --version  # 应显示 Python 3.10.x
```

**如果environment.yml不可用，手动创建**：
```bash
# 创建环境
conda create -n geelst python=3.10 -y

# 激活
conda activate geelst

# 安装核心包
conda install -c conda-forge earthengine-api pandas numpy jupyter -y
pip install geemap
```

---

## 步骤2：GEE认证（3分钟）

### 2.1 启动Python

```bash
python
```

### 2.2 运行认证

```python
import ee
ee.Authenticate()
```

### 2.3 完成认证

1. 会看到一个URL，点击它
2. 登录您的Google账号
3. 授予GEE访问权限
4. 复制显示的授权码
5. 粘贴到终端，按回车

成功后会看到：
```
Successfully saved authorization token.
```

### 2.4 测试连接

```python
# 初始化（使用高流量API）
ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')

# 测试查询
test_point = ee.Geometry.Point([116.4, 39.9])
print("✅ GEE连接成功！")

# 退出Python
exit()
```

---

## 步骤3：准备数据（2分钟）

### 3.1 检查数据格式

您的CSV文件必须包含以下列：

| 列名 | 类型 | 说明 | 示例 |
|------|------|------|------|
| lng | float | 经度 | 116.4074 |
| lat | float | 纬度 | 39.9042 |
| create_time | str | 时间戳 | 2023-01-15 14:30:00 |

其他可选列：
- city：城市名
- user_id：用户ID
- location：地点名
- gender：性别

### 3.2 放置数据文件

```bash
# 方法1：使用默认文件名
cp your_data.csv mobility_locations.csv

# 方法2：在代码中修改路径
# 打开 GEE_LST_提取完整流程.ipynb
# 修改：INPUT_CSV = 'your_file_name.csv'
```

### 3.3 检查数据（可选）

```bash
# 查看前几行
head -20 mobility_locations.csv

# 查看行数
wc -l mobility_locations.csv
```

---

## 步骤4：运行代码（5分钟测试）

### 4.1 启动Jupyter

```bash
jupyter notebook
```

浏览器会自动打开Jupyter界面。

### 4.2 打开主Notebook

找到并打开 `GEE_LST_提取完整流程.ipynb`

### 4.3 运行阶段0（环境检查）

点击"阶段0：环境配置"下的第一个Cell，点击"Run"按钮。

**预期输出**：
```
============================================================
环境配置检查
============================================================

Python版本: 3.10.x
✅ Python版本符合要求

依赖包检查:
  ✅ Earth Engine API
  ✅ Pandas
  ✅ NumPy
  ...
✅ 所有依赖包已安装
```

如果看到错误，参考[故障排除指南](docs/TROUBLESHOOTING.md)。

### 4.4 运行阶段1（数据预处理）

继续运行阶段1的所有Cell。

**预期输出**：
```
============================================================
阶段1：数据预处理
============================================================

正在读取数据...
✅ 数据读取成功
  总行数: 2,730,950
  列数: 7

数据清洗...
✅ 数据清洗完成
  原始行数: 2,730,950
  清洗后: 2,730,950

时空网格化...
✅ 网格创建完成

生成grid_uid...
✅ grid_uid生成完成: 903,155 个唯一ID

保存中间文件...
✅ 已保存: temp/raw_with_grid_uid.csv (362.5 MB)
✅ 已保存: temp/unique_grids.csv (123.9 MB)

✅ 阶段1完成！
```

### 4.5 测试小批量（可选）

如果想先测试，可以在阶段2修改：

```python
# 在阶段2的Cell中
MAX_POINTS_PER_TASK = 100  # 改为小批量测试
```

然后在阶段4只处理前几个批次。

---

## 步骤5：提交GEE任务（2-6小时）

### 5.1 运行阶段3（GEE算法配置）

这会定义LST提取算法并测试。

**预期输出**：
```
============================================================
阶段3：GEE算法配置
============================================================

✅ GEE初始化成功（使用高流量API）

算法说明:
  数据源: Landsat 8 + Landsat 9
  波段: ST_B10 (热红外传感器)
  去云: QA_PIXEL 波段
  ...
✅ 算法定义完成

测试算法...
  ✅ LST提取成功: 9.16°C

✅ 阶段3完成！
```

### 5.2 运行阶段4（批量任务派发）

**重要**：这会提交约180个任务，需要10分钟。

```python
# 确认配置
总批次数: 186
预计提交时间: 9.3 分钟

# 开始派发
[  1/186] ✅ 2023年01月 (1/22) (5000 点) - ETA: 9.2分钟
[  2/186] ✅ 2023年01月 (2/22) (5000 点) - ETA: 9.1分钟
...
[186/186] ✅ 2023年09月 (7/7) (3090 点) - ETA: 0.0分钟

✅ 派发完成！
成功: 186/186 个任务
失败: 0/186 个任务

📂 结果文件夹: LST_Final_Results

⏰ 监控地址:
   https://code.earthengine.google.com/
```

### 5.3 监控任务进度

1. 访问 https://code.earthengine.google.com/
2. 点击右上角"Tasks"按钮
3. 查看任务状态

**状态说明**：
- `READY`：准备运行
- `RUNNING`：正在运行
- `COMPLETED`：已完成 ✅
- `FAILED`：失败 ❌

**预计时间**：2-6小时（取决于数据量和GEE负载）

---

## 步骤6：下载结果（10-20分钟）

### 6.1 等待任务完成

确保所有（或大部分）任务状态为`COMPLETED`。

### 6.2 下载CSV文件

1. 访问 https://drive.google.com/
2. 找到文件夹：`LST_Final_Results`
3. 选择所有CSV文件（Ctrl+A 或 Cmd+A）
4. 右键 → 下载

**提示**：
- 文件数量：约186个
- 总大小：约50-100 MB
- 可以多选批量下载

### 6.3 放到本地文件夹

```bash
# 创建结果文件夹
mkdir lst_results

# 将下载的CSV文件移动到此文件夹
# Windows: 直接拖拽或剪切粘贴
# Mac/Linux:
mv ~/Downloads/LST_*.csv lst_results/
```

---

## 步骤7：数据合并（5分钟）

### 7.1 检查文件

```bash
# 检查文件数量
ls lst_results/*.csv | wc -l

# 应显示约186
```

### 7.2 运行阶段5

回到Jupyter Notebook，运行阶段5的所有Cell。

**预期输出**：
```
============================================================
阶段5：数据合并与质检
============================================================

LST结果文件夹: lst_results/
找到CSV文件: 186 个

合并LST结果...
✅ 成功读取 186 个文件

合并结果:
  总行数: 903,155
  唯一grid_uid数: 903,155
  有LST值的行数: 857,998

关联LST到原始数据...
  总行数: 2,730,950
  有LST值的行数: 2,643,120
  覆盖率: 96.82%

质量检查...
1. LST值范围检查:
  最小值: -15.32°C
  最大值: 42.18°C
  平均值: 18.45°C
  ✅ 未发现明显异常值

保存最终结果...
✅ 已保存: output/final_data_with_lst.csv (520.3 MB)
✅ 已保存有效LST: output/final_data_with_lst_only.csv (498.7 MB)
✅ 质量报告: output/quality_report.txt

✅ 全部完成！
```

---

## 🎉 恭喜！完成！

### 您现在拥有：

1. **final_data_with_lst.csv** - 完整数据（含所有原始点+LST列）
2. **final_data_with_lst_only.csv** - 仅有效LST数据
3. **quality_report.txt** - 质量报告

### 下一步：

1. **数据分析**
   ```python
   import pandas as pd
   df = pd.read_csv('output/final_data_with_lst.csv')

   # 查看LST统计
   print(df['LST'].describe())

   # 按月统计
   monthly = df.groupby('month')['LST'].mean()
   print(monthly)
   ```

2. **可视化**
   ```python
   import matplotlib.pyplot as plt

   # 月度LST变化
   df.groupby('month')['LST'].mean().plot(kind='bar')
   plt.title('Monthly Average LST')
   plt.ylabel('Temperature (°C)')
   plt.show()
   ```

3. **论文撰写**
   - 参考：[方法论文档](docs/METHODOLOGY.md)
   - 引用Landsat数据
   - 说明处理流程

---

## ❓ 常见问题

### Q: 任务失败怎么办？

**A**: 参考[故障排除指南](docs/TROUBLESHOOTING.md)或查看日志。

### Q: 可以跳过某些阶段吗？

**A**:
- 阶段0：如果已配置环境，可跳过
- 阶段1-3：必须运行，生成中间文件
- 阶段4：如果任务已提交，可跳过
- 阶段5：必须运行，合并最终数据

### Q: 可以中断后继续吗？

**A**: 可以！所有中间文件都保存在`temp/`文件夹。
```python
# 例如：从阶段5开始
# 直接运行阶段5的Cell即可
# 前提是temp/和lst_results/文件已存在
```

### Q: 需要多长时间？

**A**:
- 环境配置：10-15分钟（首次）
- 数据处理：5-10分钟
- 任务提交：10分钟
- GEE处理：2-6小时（等待）
- 数据下载：10-20分钟
- 数据合并：5-10分钟
- **总计**：首次约3-7小时（大部分是等待时间）

### Q: 需要付费吗？

**A**: 不需要！学术研究完全在GEE免费配额内。详见[README](README.md)中的成本分析。

---

## 📞 获取帮助

- **文档**：
  - [README.md](README.md) - 完整文档
  - [docs/METHODOLOGY.md](docs/METHODOLOGY.md) - 方法学
  - [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - 故障排除

- **社区**：
  - 提交Issue：https://github.com/yourusername/GEE-LST-Extractor/issues
  - GEE社区：https://developers.google.com/earth-engine/community

---

## 🎯 检查清单

完成快速开始后，您应该能够：

- [ ] 创建并激活geelst环境
- [ ] 完成GEE认证
- [ ] 运行阶段0-3（测试成功）
- [ ] 提交至少1个测试任务
- [ ] 在GEE页面看到任务
- [ ] 下载结果CSV文件
- [ ] 运行阶段5（数据合并）
- [ ] 查看最终输出文件

---

**祝研究顺利！** 🎓📊
