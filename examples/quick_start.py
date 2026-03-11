"""
GEE通用环境数据提取框架 - 快速开始示例

演示如何使用框架提取环境数据
"""

import pandas as pd
import numpy as np
from core.universal_extractor import UniversalExtractor

# ============================================================================
# 1. 准备数据
# ============================================================================

print("="*60)
print("步骤1：准备数据")
print("="*60)

# 创建示例数据（社交媒体点位）
np.random.seed(42)
n_points = 100

# 北京范围内的随机点
beijing_box = {
    'lng_min': 116.3,
    'lng_max': 116.5,
    'lat_min': 39.8,
    'lat_max': 40.0
}

df = pd.DataFrame({
    'user_id': range(1, n_points + 1),
    'lng': np.random.uniform(beijing_box['lng_min'], beijing_box['lng_max'], n_points),
    'lat': np.random.uniform(beijing_box['lat_min'], beijing_box['lat_max'], n_points),
    'timestamp': pd.date_range('2023-01-01', periods=n_points, freq='H')
})

print(f"✓ 创建了 {len(df)} 个示例点")
print(df.head())

# ============================================================================
# 2. 初始化提取器
# ============================================================================

print("\n" + "="*60)
print("步骤2：初始化提取器")
print("="*60)

# 从配置文件初始化
extractor = UniversalExtractor(config_path='config/data_sources.yaml')

print(f"✓ 已加载 {len(extractor.list_data_sources())} 个数据源")
print(f"  数据源：{', '.join(extractor.list_data_sources())}")

# ============================================================================
# 3. 提取环境数据
# ============================================================================

print("\n" + "="*60)
print("步骤3：提取环境数据")
print("="*60)

# 提取数据
results = extractor.extract(
    points_df=df,
    year=2023,
    month=1,
    city='Beijing'
)

# ============================================================================
# 4. 查看结果
# ============================================================================

print("\n" + "="*60)
print("步骤4：查看结果")
print("="*60)

print(f"\n结果形状：{results.shape}")
print(f"\n列名：{list(results.columns)}")

print("\n前10行：")
print(results.head(10))

# ============================================================================
# 5. 统计分析
# ============================================================================

print("\n" + "="*60)
print("步骤5：统计分析")
print("="*60)

for source in extractor.list_data_sources():
    col_name = extractor.get_config().get_data_source_config(source)['output']['column_name']

    if col_name in results.columns:
        values = results[col_name].dropna()

        if len(values) > 0:
            print(f"\n{source}:")
            print(f"  覆盖率：{len(values) / len(results) * 100:.1f}%")
            print(f"  均值：{values.mean():.2f}")
            print(f"  标准差：{values.std():.2f}")
            print(f"  范围：[{values.min():.2f}, {values.max():.2f}]")

# ============================================================================
# 6. 保存结果
# ============================================================================

print("\n" + "="*60)
print("步骤6：保存结果")
print("="*60)

output_file = 'examples_output.csv'
results.to_csv(output_file, index=False)
print(f"✓ 结果已保存到：{output_file}")

print("\n" + "="*60)
print("完成！")
print("="*60)

# ============================================================================
# 额外：动态配置示例
# ============================================================================

print("\n" + "="*60)
print("额外：动态配置示例")
print("="*60)

# 获取配置管理器
config_manager = extractor.get_config()

# 查看启用的数据源
enabled = config_manager.get_enabled_data_sources()
print(f"当前启用的数据源：{enabled}")

# 动态禁用NDVI
# config_manager.set_data_source_enabled('NDVI', False)
# print("已禁用NDVI")

# 重新初始化提取器
# extractor_new = UniversalExtractor(config_dict=config_manager.to_dict())
