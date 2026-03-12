# LST数据提取工具 - 完整使用指南

> **最后更新**: 2026-03-13
> **版本**: v1.0
> **适用场景**: 学术研究、城市规划、环境监测

---

## 📑 目录

1. [快速开始](#快速开始)
2. [功能说明](#功能说明)
3. [安装指南](#安装指南)
4. [使用教程](#使用教程)
5. [API参考](#api参考)
6. [常见问题](#常见问题)
7. [最佳实践](#最佳实践)
8. [开发计划](#开发计划)
9. [故障排除](#故障排除)

---

## 快速开始

### 5分钟上手

```python
# 1. 导入必要的库
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# 2. 创建采样点（以北京为例）
points = []
for lon in range(116, 117, 1):
    for lat in range(39, 41, 1):
        points.append({'geometry': Point(lon, lat)})
points_df = gpd.GeoDataFrame(points, crs='EPSG:4326')

# 3. 提取地表温度
import ee
ee.Initialize()

# 使用GEE提取数据
collection = ee.ImageCollection('MODIS/006/MOD11A2')\
    .filterDate('2023-01-01', '2023-12-31')\
    .select('LST_Day_1km')

# 获取平均温度
lst_mean = collection.mean()

# 提取点数据
features = [ee.Feature(Point(p.geometry.x, p.geometry.y)) for p in points]
fc = ee.FeatureCollection(features)

results = lst_mean.sampleRegions(collection=fc, scale=1000)
data = results.getInfo()

# 4. 查看结果
print(f"成功提取 {len(data['features'])} 个数据点")
```

---

## 功能说明

### 核心功能

#### 1. 数据提取
- **支持数据源**：
  - LST（地表温度）
  - NDVI（归一化植被指数）
  - EVI（增强植被指数）
  - Albedo（反照率）
  - PM2.5（颗粒物浓度）

- **时间范围**：
  - 支持任意时间段
  - 月度、季度、年度统计
  - 时间序列提取

- **空间范围**：
  - 单点提取
  - 批量点提取
  - 网格化提取
  - 自定义区域

#### 2. 数据处理
- 质量控制
  - 自动标记缺失值
  - 缺失值填充策略
  - 异常值检测

- 数据转换
  - 单位转换
  - 坐标系转换
  - 格式转换

#### 3. 批量处理
- 多城市并行处理
- 多时段连续提取
- 自动进度跟踪
- 失败任务重试

#### 4. 可视化
- 空间分布图
- 时间序列图
- 统计直方图
- 相关性分析图

#### 5. 数据导出
- CSV格式
- Excel格式
- GeoJSON格式
- Shapefile格式

---

## 安装指南

### 环境要求

- Python 3.7+
- 操作系统：Windows/Mac/Linux
- 内存：建议8GB+
- 网络：需要访问Google Earth Engine

### 安装步骤

#### 1. 克隆仓库

```bash
git clone https://github.com/your-repo/LST-Tools.git
cd LST-Tools
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置GEE

```python
import ee
ee.Authenticate()  # 首次使用需要认证
ee.Initialize()    # 初始化
```

#### 4. 验证安装

```bash
python test_installation.py
```

---

## 使用教程

### 教程1：提取单个城市的LST数据

```python
# 导入必要的库
from shapely.geometry import Point
import geopandas as gpd
import ee

# 初始化GEE
ee.Initialize()

# 定义研究区域（北京）
bbox = {
    'min_lon': 116.0,
    'min_lat': 39.7,
    'max_lon': 116.8,
    'max_lat': 40.2
}

# 创建采样点
def create_points(bbox, spacing=0.05):
    points = []
    lon = bbox['min_lon']
    while lon < bbox['max_lon']:
        lat = bbox['min_lat']
        while lat < bbox['max_lat']:
            points.append({'geometry': Point(lon, lat)})
            lat += spacing
        lon += spacing
    return gpd.GeoDataFrame(points, crs='EPSG:4326')

points_df = create_points(bbox)

# 提取LST数据
collection = ee.ImageCollection('MODIS/006/MOD11A2')\
    .filterDate('2023-01-01', '2023-12-31')\
    .select('LST_Day_1km')

lst_mean = collection.mean()

# 创建FeatureCollection
features = []
for idx, row in points_df.iterrows():
    point = ee.Geometry.Point([row.geometry.x, row.geometry.y])
    feature = ee.Feature(point, {'id': idx})
    features.append(feature)

fc = ee.FeatureCollection(features)

# 提取数据
results = lst_mean.sampleRegions(
    collection=fc,
    scale=1000
)

# 转换为DataFrame
data = results.getInfo()['features']
extracted_data = []
for item in data:
    props = item['properties']
    extracted_data.append({
        'id': props.get('id'),
        'LST': props.get('LST_Day_1km')
    })

df = pd.DataFrame(extracted_data)

# 转换为摄氏度
df['LST_Celsius'] = df['LST'] * 0.02 - 273.15

print(df.describe())
```

### 教程2：批量提取多城市数据

```python
# 定义多个城市
cities = {
    '北京': {'min_lon': 116.0, 'min_lat': 39.7, 'max_lon': 116.8, 'max_lat': 40.2},
    '上海': {'min_lon': 121.0, 'min_lat': 31.0, 'max_lon': 121.8, 'max_lat': 31.5},
    '广州': {'min_lon': 113.0, 'min_lat': 23.0, 'max_lon': 113.5, 'max_lat': 23.5}
}

# 批量提取
results = {}
for city_name, bbox in cities.items():
    print(f"处理 {city_name}...")
    points_df = create_points(bbox)

    # 提取数据
    # ... (同教程1)

    results[city_name] = df

# 比较不同城市
for city_name, df in results.items():
    print(f"{city_name} 平均温度: {df['LST_Celsius'].mean():.2f}°C")
```

### 教程3：时间序列分析

```python
# 提取多年数据
years = [2019, 2020, 2021, 2022, 2023]
time_series = []

for year in years:
    print(f"提取 {year} 年数据...")

    collection = ee.ImageCollection('MODIS/006/MOD11A2')\
        .filterDate(f'{year}-01-01', f'{year}-12-31')\
        .select('LST_Day_1km')

    lst_mean = collection.mean()

    # 提取数据
    # ... (同教程1)

    time_series.append({
        'year': year,
        'mean_temp': df['LST_Celsius'].mean()
    })

ts_df = pd.DataFrame(time_series)

# 绘制时间序列
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
plt.plot(ts_df['year'], ts_df['mean_temp'], marker='o')
plt.title('地表温度年际变化')
plt.xlabel('年份')
plt.ylabel('平均温度 (°C)')
plt.grid(True)
plt.show()
```

---

## API参考

### GEEDataExtractor

主要的GEE数据提取类。

#### 初始化

```python
extractor = GEEDataExtractor()
```

#### 方法

##### extract_data()

提取指定类型的数据。

**参数**：
- `points_df` (GeoDataFrame): 采样点
- `data_type` (str): 数据类型（LST/NDVI/EVI等）
- `start_date` (str): 开始日期 (YYYY-MM-DD)
- `end_date` (str): 结束日期 (YYYY-MM-DD)
- `band_name` (str, optional): 波段名称
- `scale` (int, optional): 分辨率（米）
- `reducer` (str): 聚合方法（mean/median/max/min）

**返回**：
- DataFrame with extracted values

**示例**：
```python
result = extractor.extract_data(
    points_df=points,
    data_type='LST',
    start_date='2023-01-01',
    end_date='2023-12-31'
)
```

##### extract_time_series()

提取时间序列数据。

**参数**：
- `points_df` (GeoDataFrame): 采样点
- `data_type` (str): 数据类型
- `start_date` (str): 开始日期
- `end_date` (str): 结束日期
- `time_step` (str): 时间步长（month/week/day）

**返回**：
- DataFrame with time series

---

### BatchProcessor

批量处理器。

#### 方法

##### add_task()

添加提取任务。

**参数**：
- `city_name` (str): 城市名称
- `points_df` (GeoDataFrame): 采样点
- `data_type` (str): 数据类型
- `start_date` (str): 开始日期
- `end_date` (str): 结束日期
- `task_id` (str, optional): 任务ID

##### run_all()

运行所有任务。

**参数**：
- `save_results` (bool): 是否保存结果

**返回**：
- dict with all results

---

### 工具函数

#### create_sampling_points()

创建规则采样点。

```python
points = create_sampling_points(bbox, spacing=0.05)
```

#### quality_check()

检查数据质量。

```python
report = quality_check(data['LST_Celsius'], threshold=0.3)
```

#### fill_missing()

填充缺失值。

```python
filled_data = fill_missing(data['LST_Celsius'], method='interpolate')
```

---

## 常见问题

### Q1: GEE认证失败

**问题**：提示"Authentication failed"

**解决方案**：
1. 确保网络连接正常
2. 运行 `ee.Authenticate()` 重新认证
3. 检查Google账户权限

### Q2: 提取数据超时

**问题**：大数据量提取时超时

**解决方案**：
1. 减少采样点数量（<5000个）
2. 缩短时间范围
3. 使用批量处理分批提取

### Q3: 缺失值过多

**问题**：提取的数据有很多缺失值

**解决方案**：
1. 检查云层覆盖情况
2. 使用不同的聚合方法
3. 应用填充策略

### Q4: 坐标系不匹配

**问题**：点位偏移

**解决方案**：
1. 确保使用WGS84坐标系
2. 检查坐标顺序（经度、纬度）
3. 使用GeoDataFrame确保空间参考正确

### Q5: 内存不足

**问题**：处理大量数据时内存溢出

**解决方案**：
1. 分批处理数据
2. 使用chunk读取
3. 增加系统内存

---

## 最佳实践

### 1. 数据提取

- **批量提取**：对于大量点位，使用批量处理功能
- **合理采样**：根据研究需求确定采样密度
- **缓存结果**：保存中间结果避免重复提取

### 2. 质量控制

- **检查缺失值**：始终检查数据缺失情况
- **验证结果**：与已知数据源进行对比验证
- **记录元数据**：记录提取参数和数据来源

### 3. 性能优化

- **使用并行处理**：充分利用多核CPU
- **合理设置分辨率**：避免不必要的过高分辨率
- **分块处理**：大数据集分块处理

### 4. 数据管理

- **规范命名**：使用有意义的文件名
- **版本控制**：使用Git管理代码和文档
- **备份数据**：定期备份重要数据

---

## 开发计划

### Phase 1: 核心功能 ✅

- [x] GEE集成基础
- [x] LST数据提取
- [x] NDVI数据提取
- [x] 批量处理功能

### Phase 2: 扩展功能 🔄

- [ ] PM2.5数据提取
- [ ] 降水数据提取
- [ ] 人口密度数据
- [ ] 夜间灯光数据

### Phase 3: 用户体验 ⏳

- [ ] 交互式界面
- [ ] 在线文档
- [ ] 视频教程
- [ ] 案例库

### Phase 4: 高级功能 ⏳

- [ ] 机器学习集成
- [ ] 自动化报告
- [ ] API接口
- [ ] 云端部署

---

## 故障排除

### 错误：Earth Engine quota exceeded

**原因**：超出了GEE配额限制

**解决方案**：
1. 等待配额重置（通常每月重置）
2. 减少请求次数
3. 使用更高效的数据提取方法

### 错误：Invalid GeoJSON

**原因**：GeoJSON格式不正确

**解决方案**：
1. 检查几何类型
2. 验证坐标范围
3. 使用GeoJSON验证工具

### 错误：Memory Error

**原因**：内存不足

**解决方案**：
1. 减少数据量
2. 使用分块处理
3. 增加系统内存

### 错误：Connection Timeout

**原因**：网络连接问题

**解决方案**：
1. 检查网络连接
2. 增加超时时间
3. 重试请求

---

## 技术支持

### 获取帮助

1. **查看文档**：先查阅相关文档
2. **搜索问题**：在GitHub Issues中搜索类似问题
3. **提交问题**：创建新的Issue详细描述问题
4. **联系作者**：通过邮箱联系

### 报告问题

报告问题时请包含：
- 错误信息
- 复现步骤
- 代码片段
- 环境信息（Python版本、操作系统等）

---

## 许可证

MIT License

---

## 致谢

- Google Earth Engine团队
- MODIS数据团队
- 开源社区贡献者

---

*完整使用指南 - 最后更新: 2026-03-13*
