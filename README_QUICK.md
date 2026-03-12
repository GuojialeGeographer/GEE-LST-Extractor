# LST数据提取工具 🌍

> 快速、便捷地提取地表温度和环境数据
> 适用于学术研究、城市规划、环境监测

---

## 🚀 5分钟快速开始

### 1. 打开Master Notebook

```bash
jupyter notebook LST_Tools_Master.ipynb
```

### 2. 运行第一个单元格

设置环境和导入库。

### 3. 提取数据

```python
# 创建采样点
from shapely.geometry import Point
import geopandas as gpd

points = gpd.GeoDataFrame([
    {'geometry': Point(116.4, 39.9)},  # 北京
], crs='EPSG:4326')

# 提取地表温度
result = extractor.extract_data(
    points_df=points,
    data_type='LST',
    start_date='2023-01-01',
    end_date='2023-12-31'
)
```

### 4. 查看结果

```python
print(result)
```

---

## 📚 完整文档

查看 **[COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)** 获取：
- 详细功能说明
- 完整教程
- API参考
- 常见问题

---

## ✨ 主要功能

- **多数据源**：LST、NDVI、PM2.5、EVI、Albedo
- **批量处理**：多城市、多时段并行提取
- **质量控制**：自动检测和填充缺失值
- **可视化**：空间分布图、时间序列图
- **多种导出**：CSV、Excel、GeoJSON

---

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/LST-Tools.git
cd LST-Tools

# 安装依赖
pip install -r requirements.txt

# 认证GEE（首次使用）
python -c "import ee; ee.Authenticate()"
```

---

## 🎯 支持的数据类型

| 数据类型 | 说明 | 分辨率 |
|---------|------|--------|
| LST | 地表温度 | 30m-1km |
| NDVI | 植被指数 | 250m |
| PM2.5 | 颗粒物浓度 | 1km |
| EVI | 增强植被指数 | 250m |
| Albedo | 反照率 | 500m |

---

## 💡 使用示例

### 提取北京2023年地表温度

```python
# 定义边界
beijing_bbox = {
    'min_lon': 116.0, 'min_lat': 39.7,
    'max_lon': 116.8, 'max_lat': 40.2
}

# 创建采样点
points = create_sampling_points(beijing_bbox)

# 提取数据
lst_data = extractor.extract_data(
    points_df=points,
    data_type='LST',
    start_date='2023-01-01',
    end_date='2023-12-31'
)
```

### 批量处理多个城市

```python
processor = BatchProcessor(extractor)

processor.add_task('北京', beijing_points, 'LST', '2023-01-01', '2023-12-31')
processor.add_task('上海', shanghai_points, 'NDVI', '2023-01-01', '2023-12-31')

results = processor.run_all()
```

---

## 📖 文档导航

- **[LST_Tools_Master.ipynb](LST_Tools_Master.ipynb)** - 主Notebook（所有代码）
- **[COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)** - 完整使用指南
- **[PROGRESS_LOG.md](PROGRESS_LOG.md)** - 开发进度日志

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
4. 查看完整文档的故障排除部分

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

## 🤝 贡献

欢迎提交问题和拉取请求！

---

## 📄 许可证

MIT License

---

## 📞 获取帮助

- 📖 查看 [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)
- 🐛 提交 [GitHub Issues](https://github.com/your-repo/LST-Tools/issues)
- 📧 联系作者

---

**快速上手 → 打开 `LST_Tools_Master.ipynb` 开始使用！**

*最后更新: 2026-03-13*
