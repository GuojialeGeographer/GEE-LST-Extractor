# GEE通用环境数据提取框架

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![GEE](https://img.shields.io/badge/GEE-Landsat%208%2F9-orange.svg)](https://earthengine.google.com/)

一个通用的、可扩展的Google Earth Engine环境数据提取框架，支持从地理位置点提取多种环境感知数据。

## ✨ 核心特性

- 🔄 **一次配置，多数据源** - 通过配置文件轻松切换数据源
- 🔌 **插件化架构** - 添加新数据源无需修改核心代码
- 🎯 **共享基础设施** - 所有数据源共享网格化、批次管理、质量标记
- 📊 **统一输出格式** - 所有数据源输出一致的格式和元数据
- 📈 **高覆盖率** - 智能填充策略确保95%+的数据覆盖率
- 🏷️ **质量透明** - 完整的质量标记和处理方法记录

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/GuojialeGeographer/GEE-LST-Extractor.git
cd GEE-LST-Extractor

# 安装依赖
pip install -r requirements.txt

# 认证GEE
import ee
ee.Authenticate()
```

### 基本使用

```python
import pandas as pd
from core.universal_extractor import UniversalExtractor

# 读取数据
df = pd.read_csv('social_media_points.csv')

# 初始化提取器
extractor = UniversalExtractor(config_path='config/data_sources.yaml')

# 提取环境数据（一行代码！）
results = extractor.extract(
    points_df=df,
    year=2023,
    month=1,
    city='Beijing'
)

# 保存结果
results.to_csv('social_media_with_environment.csv', index=False)
```

### 配置数据源

编辑 `config/data_sources.yaml`：

```yaml
data_sources:
  LST:
    enabled: true   # 启用LST
  NDVI:
    enabled: true   # 启用NDVI
  PM25:
    enabled: false  # 禁用PM2.5
```

## 📊 支持的数据源

| 数据源 | 描述 | 分辨率 | 状态 |
|-------|------|--------|------|
| **LST** | 地表温度 | 30m | ✅ 已实现 |
| **NDVI** | 植被指数 | 30m | ✅ 已实现 |
| PM2.5 | PM2.5浓度 | 1km | 📝 计划中 |
| 降水 | 降水量 | 10km | 📝 计划中 |
| 人口密度 | 人口分布 | 100m | 📝 计划中 |
| 夜间灯光 | 夜间光强度 | 500m | 📝 计划中 |
| 高程 | 地形高程 | 30m | 📝 计划中 |
| 土地覆盖 | 土地利用类型 | 10m | 📝 计划中 |

## 🏗️ 架构设计

```
用户配置 (YAML)
    ↓
UniversalExtractor (主入口)
    ↓
加载多个提取器插件 (BaseExtractor子类)
    ↓
共享核心服务
    ├─ GridManager (网格管理)
    ├─ BatchManager (批次管理)
    └─ QualityTracker (质量标记)
    ↓
统一输出 (DataFrame)
```

## 🔌 添加新数据源

只需3步：

### 1. 创建提取器类

```python
# extractors/my_extractor.py

from core.base_extractor import BaseExtractor
import ee

class MyExtractor(BaseExtractor):
    def get_collection(self):
        return ee.ImageCollection('MY/DATASET')

    def apply_scale_factors(self, image):
        # 定标逻辑
        return image

    def filter_by_quality(self, collection):
        # 质量控制
        return collection

    def get_band_name(self):
        return 'MyBand'
```

### 2. 添加配置

```yaml
# config/data_sources.yaml

data_sources:
  MyData:
    enabled: true
    extractor: my_extractor.MyExtractor
    output:
      column_name: "MyVariable"
```

### 3. 使用

```python
extractor = UniversalExtractor('config/data_sources.yaml')
results = extractor.extract(df, 2023, 1)
```

完成！无需修改任何核心代码。

## 📖 文档

- [API文档](docs/API_REFERENCE.md) - 详细的API参考
- [教程](notebooks/) - Jupyter notebook教程
- [贡献指南](docs/CONTRIBUTING.md) - 如何贡献代码

## 🤝 贡献

欢迎贡献！请参阅 [贡献指南](docs/CONTRIBUTING.md)

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🙏 致谢

- Google Earth Engine团队
- Landsat团队
- 所有贡献者

---

**注意**：本项目仍在积极开发中，API可能会有变化。
