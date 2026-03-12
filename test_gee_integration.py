"""
GEE集成测试 - 验证真正的数据提取

测试LST和NDVI的GEE数据提取
"""

import sys
sys.path.append('.')

import pandas as pd
import numpy as np
import ee
from core.universal_extractor import UniversalExtractor

print("="*60)
print("GEE集成测试")
print("="*60)

# 初始化GEE
try:
    ee.Initialize()
    print("✓ GEE初始化成功")
except Exception as e:
    print(f"✗ GEE初始化失败：{e}")
    print("\n请先运行:")
    print("  import ee")
    print("  ee.Authenticate()")
    sys.exit(1)

# ============================================================================
# 创建测试数据
# ============================================================================

print("\n创建测试数据...")

# 创建北京区域的测试点
np.random.seed(42)
n_points = 20

test_df = pd.DataFrame({
    'user_id': range(1, n_points + 1),
    'lng': np.random.uniform(116.3, 116.5, n_points),
    'lat': np.random.uniform(39.8, 40.0, n_points)
})

print(f"✓ 创建了 {n_points} 个测试点")
print(test_df.head())

# ============================================================================
# 测试1：单个提取器测试
# ============================================================================

print("\n" + "="*60)
print("测试1：单个提取器")
print("="*60)

from extractors.lst_extractor import LSTExtractor
from core.gee_helper import GEEHelper

# 测试LST提取器
print("\n测试LST提取器...")
lst_extractor = LSTExtractor({})

# 提取前10个点
test_points = test_df.head(10).copy()

try:
    lst_result = GEEHelper.batch_extract(
        extractor=lst_extractor,
        points_df=test_points,
        year=2023,
        month=1,
        batch_size=10
    )

    print(f"✓ LST提取成功")
    print(f"  提取点数：{len(lst_result)}")
    print(f"  有效值数：{lst_result['LST'].notna().sum()}")
    print(f"  覆盖率：{lst_result['LST'].notna().sum() / len(lst_result) * 100:.1f}%")

    if lst_result['LST'].notna().sum() > 0:
        valid_values = lst_result['LST'].dropna()
        print(f"  均值：{valid_values.mean():.2f}°C")
        print(f"  范围：[{valid_values.min():.2f}, {valid_values.max():.2f}]")

except Exception as e:
    print(f"✗ LST提取失败：{e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# 测试2：完整流程测试
# ============================================================================

print("\n" + "="*60)
print("测试2：完整流程")
print("="*60)

try:
    # 创建配置（只启用LST和NDVI）
    config = {
        'data_sources': {
            'LST': {
                'enabled': True,
                'extractor': 'lst_extractor.LSTExtractor',
                'parameters': {},
                'output': {'column_name': 'LST', 'unit': 'Celsius'}
            },
            'NDVI': {
                'enabled': True,
                'extractor': 'ndvi_extractor.NDVIExtractor',
                'parameters': {},
                'output': {'column_name': 'NDVI', 'unit': 'unitless'}
            }
        },
        'global_settings': {
            'batch': {'points_per_task': 10, 'delay_between_tasks': 1},
            'output': {'include_quality_flags': True},
            'quality': {'apply_filling_strategies': False}  # 先禁用填充
        }
    }

    print("\n初始化UniversalExtractor...")
    extractor = UniversalExtractor(config_dict=config)

    print(f"✓ 已加载 {len(extractor.list_data_sources())} 个数据源")

    print("\n开始提取...")
    results = extractor.extract(
        points_df=test_df,
        year=2023,
        month=1,
        city='Beijing'
    )

    print("\n✓ 提取完成")
    print(results.head())

    # 统计
    print("\n数据统计:")
    for source in extractor.list_data_sources():
        col_name = extractor.get_config().get_data_source_config(source)['output']['column_name']
        if col_name in results.columns:
            valid = results[col_name].notna().sum()
            print(f"\n{source}:")
            print(f"  有效值：{valid}/{len(results)}")
            print(f"  覆盖率：{valid/len(results)*100:.1f}%")

            if valid > 0:
                values = results[col_name].dropna()
                print(f"  均值：{values.mean():.2f}")
                print(f"  标准差：{values.std():.2f}")

    # 保存结果
    output_file = 'test_results/gee_integration_test.csv'
    results.to_csv(output_file, index=False)
    print(f"\n✓ 结果已保存到：{output_file}")

except Exception as e:
    print(f"\n✗ 测试失败：{e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# 总结
# ============================================================================

print("\n" + "="*60)
print("测试完成")
print("="*60)

print("\n如果看到'✓'标记，说明GEE集成成功！")
print("下一步：")
print("  1. 增加测试点数（100, 1000）")
print("  2. 测试更多数据源")
print("  3. 优化性能")
