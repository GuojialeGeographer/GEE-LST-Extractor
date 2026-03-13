# 🤖 智能数据更新系统 - 快速开始

## 📚 简介

智能数据更新系统是LST数据提取工具的新功能，可以自动发现和更新GEE数据集到最新版本。

**主要特性**：
- ✅ 自动发现最新数据集
- ✅ 一键更新所有数据源
- ✅ 智能推荐最佳版本
- ✅ 自动备份和回滚
- ✅ 详细的更新报告

## 🚀 快速开始（3步）

### 方式1：使用交互式Notebook（推荐）

#### 第1步：打开Notebook
```bash
jupyter notebook SMART_UPDATE.ipynb
```

#### 第2步：运行单元格
依次运行所有单元格

#### 第3步：查看结果
查看可用的更新并决定是否应用

### 方式2：使用命令行

```python
from core.smart_update_manager import SmartUpdateManager

# 创建管理器
manager = SmartUpdateManager('config/datasets_config.json')

# 检查更新
updates = manager.check_updates()

# 应用更新
if updates:
    result = manager.update_all(auto_apply=True, create_backup=True)
```

## 📊 支持的数据类型

| 数据类型 | 当前版本 | 最新版本 | 状态 |
|---------|---------|---------|------|
| LST | 061 | 061 | ✅ 最新 |
| NDVI | 061 | 061 | ✅ 最新 |
| EVI | 061 | 061 | ✅ 最新 |
| Albedo | 061 | 061 | ✅ 最新 |
| PM2.5 | 006 | 006 | ✅ 最新 |

## 📁 文件说明

### 核心模块
- `core/smart_dataset_discoverer.py` - 智能发现模块
- `core/smart_update_manager.py` - 更新管理器
- `core/update_report_generator.py` - 报告生成器

### 配置文件
- `config/datasets_config.json` - 数据集配置
- `dataset_versions.json` - 版本历史（自动生成）

### 用户界面
- `SMART_UPDATE.ipynb` - 交互式更新Notebook
- `SMART_UPDATE_PLAN.md` - 实现方案文档

## 💡 使用技巧

### 定期检查更新
建议每月或每季度运行一次更新检查。

### 安全更新
1. 总是开启自动备份（默认开启）
2. 先测试再应用到生产环境
3. 查看更新报告了解详情

### 回滚配置
如果更新后出现问题，可以回滚：
```python
manager.rollback_update()
```

## 🔧 高级功能

### 查看数据集详细信息
```python
from core.smart_dataset_discoverer import SmartDatasetDiscoverer

discoverer = SmartDatasetDiscoverer()
metadata = discoverer.get_dataset_metadata('MODIS/061/MOD11A2')
```

### 比较数据集版本
```python
comparison = discoverer.compare_datasets(
    'MODIS/061/MOD11A2',
    'MODIS/006/MOD11A2'
)
```

### 生成更新报告
```python
from core.update_report_generator import generate_all_reports

reports = generate_all_reports(update_data, 'output')
# 生成 HTML、JSON、Markdown 三种格式
```

## 📞 获取帮助

- 详细文档：查看 `SMART_UPDATE_PLAN.md`
- 交互教程：打开 `SMART_UPDATE.ipynb`
- 完整指南：查看 `COMPLETE_USER_GUIDE.md`

## ⚠️ 注意事项

1. **GEE认证**：首次使用需要认证GEE
   ```python
   import ee
   ee.Authenticate()
   ```

2. **网络连接**：需要稳定的网络连接访问GEE

3. **API限制**：避免频繁调用，建议批量处理

4. **数据备份**：重要数据请提前备份

## 🎉 总结

智能数据更新系统让数据源更新变得简单：

- ✅ **自动化** - 无需手动查找和更新
- ✅ **智能化** - 自动推荐最佳版本
- ✅ **安全化** - 自动备份，支持回滚
- ✅ **可视化** - 详细的报告和历史记录

**开始使用**：
```bash
jupyter notebook SMART_UPDATE.ipynb
```

---

*智能数据更新系统 v1.0 | 更新日期: 2026-03-13*
