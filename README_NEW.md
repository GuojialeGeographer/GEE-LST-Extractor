# 🌍 LST数据提取工具

> **快速、便捷地提取地表温度和环境数据**
>
> 适用于学术研究、城市规划、环境监测

---

## ⚡ 5分钟快速开始

### 第1步：打开Notebook

```bash
jupyter notebook LST_Tools_Master.ipynb
```

### 第2步：运行示例代码

在Notebook中运行示例单元格，提取数据

### 第3步：查看结果

```python
print(result)
```

---

## ✨ 主要功能

- **📊 多数据源**: LST、NDVI、PM2.5、EVI、Albedo
- **🚀 批量处理**: 多城市、多时段并行提取
- **✅ 质量控制**: 自动检测和填充缺失值
- **📈 可视化**: 空间分布图、时间序列图
- **💾 多格式导出**: CSV、Excel、GeoJSON

---

## 📖 文档导航

| 文档 | 说明 |
|-----|------|
| 📗 [README_QUICK.md](README_QUICK.md) | **快速入门**（5分钟） |
| 📘 [LST_Tools_Master.ipynb](LST_Tools_Master.ipynb) | **主Notebook**（所有代码） |
| 📙 [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md) | **完整指南**（详细文档） |
| 📊 [PROJECT_STATUS.md](PROJECT_STATUS.md) | **项目状态**（75%完成） |
| 📝 [SESSION_2026_03_13.md](SESSION_2026_03_13.md) | **会话总结** |

---

## 🚀 快速示例

### 提取地表温度

```python
# 创建采样点
from shapely.geometry import Point
import geopandas as gpd

points = gpd.GeoDataFrame([
    {'geometry': Point(116.4, 39.9)},  # 北京
], crs='EPSG:4326')

# 提取数据
result = extractor.extract_data(
    points_df=points,
    data_type='LST',
    start_date='2023-01-01',
    end_date='2023-12-31'
)
```

### 批量处理

```python
processor = BatchProcessor(extractor)

processor.add_task('北京', beijing_points, 'LST', '2023-01-01', '2023-12-31')
processor.add_task('上海', shanghai_points, 'NDVI', '2023-01-01', '2023-12-31')

results = processor.run_all()
```

---

## 📦 安装

```bash
# 克隆项目
git clone https://github.com/your-repo/LST-Tools.git
cd LST-Tools

# 安装依赖
pip install -r requirements.txt

# 认证GEE（首次使用）
python -c "import ee; ee.Authenticate()"
```

---

## 🎯 支持的数据类型

| 数据类型 | 说明 | 分辨率 | 状态 |
|---------|------|--------|------|
| 🌡️ LST | 地表温度 | 30m | ✅ |
| 🌿 NDVI | 植被指数 | 250m | ✅ |
| 💨 PM2.5 | 颗粒物浓度 | 1km | ✅ |
| 🍃 EVI | 增强植被指数 | 250m | ✅ |
| ☀️ Albedo | 反照率 | 500m | ✅ |

---

## 💡 为什么选择这个工具？

### ✅ 简单易用
- 所有代码在一个Notebook中
- 丰富的示例和文档
- 无需深入了解遥感

### ✅ 功能完整
- 支持5种数据类型
- 批量处理能力
- 质量控制机制

### ✅ 学术友好
- 详细的数据来源说明
- 支持引用和溯源
- 可重复的研究流程

---

## ❓ 常见问题

### Q: 如何认证GEE？

```python
import ee
ee.Authenticate()  # 首次使用
ee.Initialize()
```

### Q: 提取失败怎么办？

1. 检查网络连接
2. 确认GEE已认证
3. 减少采样点数量（<5000）
4. 查看 [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md) 的故障排除部分

### Q: 如何转换数据格式？

```python
# CSV
df.to_csv('output.csv')

# Excel
df.to_excel('output.xlsx')

# GeoJSON
gdf.to_file('output.geojson', driver='GeoJSON')
```

---

## 📚 学习路径

### 新手（第1天）
1. 阅读 [README_QUICK.md](README_QUICK.md)
2. 打开 `LST_Tools_Master.ipynb`
3. 运行示例代码

### 进阶（第2-3天）
1. 阅读 [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)
2. 尝试修改参数
3. 提取自己的数据

### 高级（第4天+）
1. 批量处理
2. 质量控制
3. 数据可视化

---

## 🤝 贡献

欢迎贡献代码、报告问题、提出建议！

---

## 📞 获取帮助

- 📖 查看 [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)
- 🐛 提交 [GitHub Issues](https://github.com/your-repo/LST-Tools/issues)
- 📧 联系作者

---

## 📄 许可证

MIT License - 自由使用和修改

---

## 🏆 项目状态

- **完成度**: 75%
- **状态**: ✅ 可用于学术研究和实际应用
- **推荐指数**: ⭐⭐⭐⭐⭐

---

**🚀 立即开始 → 打开 `LST_Tools_Master.ipynb`**

*最后更新: 2026-03-13*
