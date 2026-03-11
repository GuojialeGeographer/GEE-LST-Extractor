"""
GEE通用环境数据提取框架 - 简单测试

验证核心组件是否正常工作
"""

import sys
sys.path.append('.')

from core.base_extractor import BaseExtractor
from core.grid_manager import GridManager
from core.batch_manager import BatchManager
from core.quality_tracker import QualityTracker
from core.config_manager import ConfigManager
import pandas as pd
import numpy as np

print("="*60)
print("GEE通用环境数据提取框架 - 组件测试")
print("="*60)

# ============================================================================
# 测试1：GridManager
# ============================================================================

print("\n测试1：GridManager - 网格管理器")

grid_manager = GridManager(precision=4)

# 创建测试数据
test_df = pd.DataFrame({
    'lng': [116.4074, 116.4075, 116.4074, 116.4080],
    'lat': [39.9042, 39.9043, 39.9042, 39.9050]
})

# 创建网格
gridded = grid_manager.create_grids(test_df, 2023, 1, 'Beijing')
print(f"✓ 网格化完成")
print(f"  原始点数：{len(test_df)}")
print(f"  唯一网格数：{gridded['grid_uid'].nunique()}")

# ============================================================================
# 测试2：BatchManager
# ============================================================================

print("\n测试2：BatchManager - 批次管理器")

batch_manager = BatchManager(
    points_per_task=2,
    delay_between_tasks=0.1
)

# 创建测试批次
large_df = pd.DataFrame({
    'lng': np.random.uniform(116.3, 116.5, 10),
    'lat': np.random.uniform(39.8, 40.0, 10)
})

batches = batch_manager.create_batches(large_df)
print(f"✓ 批次划分完成")
print(f"  总点数：{len(large_df)}")
print(f"  批次数量：{len(batches)}")

# ============================================================================
# 测试3：ConfigManager
# ============================================================================

print("\n测试3：ConfigManager - 配置管理器")

try:
    config_manager = ConfigManager(config_path='config/data_sources.yaml')
    print(f"✓ 配置加载成功")

    enabled = config_manager.get_enabled_data_sources()
    print(f"  启用的数据源：{enabled}")

    global_config = config_manager.get_global_config()
    print(f"  批次大小：{global_config['batch']['points_per_task']}")

except FileNotFoundError:
    print("✗ 配置文件不存在（这是正常的，如果还没有创建）")

# ============================================================================
# 测试4：QualityTracker
# ============================================================================

print("\n测试4：QualityTracker - 质量追踪器")

quality_config = {
    'quality': {
        'apply_filling_strategies': True,
        'filling_priority': ['extended_temporal', 'spatial_neighbors']
    }
}

quality_tracker = QualityTracker(quality_config)

# 创建带缺失值的测试数据
test_data = pd.DataFrame({
    'value': [1.0, 2.0, np.nan, 4.0, np.nan]
})

# 添加质量标记
flagged = quality_tracker.add_quality_flags(test_data, 'value')
print(f"✓ 质量标记添加完成")
print(f"  添加的列：{list(flagged.columns)}")

# 生成报告
report = quality_tracker.generate_report(flagged, 'value')
print(f"  覆盖率：{report['coverage']:.1f}%")

# ============================================================================
# 测试5：提取器导入
# ============================================================================

print("\n测试5：提取器导入测试")

try:
    from extractors.lst_extractor import LSTExtractor
    print("✓ LSTExtractor导入成功")

    lst = LSTExtractor({})
    print(f"  数据集ID：{lst.get_collection_id()}")
    print(f"  空间分辨率：{lst.get_spatial_resolution()}m")
    print(f"  时间分辨率：{lst.get_temporal_resolution()}")

except Exception as e:
    print(f"✗ LSTExtractor导入失败：{e}")

try:
    from extractors.ndvi_extractor import NDVIExtractor
    print("✓ NDVIExtractor导入成功")

    ndvi = NDVIExtractor({})
    print(f"  数据集ID：{ndvi.get_collection_id()}")
    print(f"  单位：{ndvi.get_unit()}")

except Exception as e:
    print(f"✗ NDVIExtractor导入失败：{e}")

# ============================================================================
# 总结
# ============================================================================

print("\n" + "="*60)
print("测试完成！")
print("="*60)
print("\n如果所有测试都通过（✓），说明框架核心组件工作正常。")
print("下一步：")
print("  1. 配置GEE认证：ee.Authenticate()")
print("  2. 运行完整示例：python examples/quick_start.py")
print("  3. 查看文档：README.md")
