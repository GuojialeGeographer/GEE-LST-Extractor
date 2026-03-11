"""
网格管理器 - 时空网格处理

负责：
1. 创建时空网格
2. 生成唯一ID
3. 网格聚合
4. 去重优化
"""

import pandas as pd
import numpy as np
from uuid import uuid5, UUID, NAMESPACE_DNS
from typing import Optional


class GridManager:
    """
    时空网格管理器

    设计目的：
    1. 减少冗余计算：同一网格的点只需提取一次
    2. 保证一致性：相同时空位置的点获得相同值
    3. 提高效率：大幅减少GEE任务数量

    使用场景：
    - 社交媒体数据：大量点在同一位置
    - 轨迹数据：重复路径
    - 任何有重复位置的数据

    示例：
        # 精度：4位小数 ≈ 11米
        grid_manager = GridManager(precision=4)

        # 创建网格
        gridded_df = grid_manager.create_grids(
            df=social_media_df,
            year=2023,
            month=1,
            city='Beijing'
        )

        # 获取唯一网格（用于GEE提取）
        unique_grids = grid_manager.get_unique_grids(gridded_df)
    """

    def __init__(self, precision: int = 4):
        """
        初始化网格管理器

        Args:
            precision: 经纬度精度（小数位数）
                     3 ≈ 111米
                     4 ≈ 11.1米 (推荐)
                     5 ≈ 1.1米
                     6 ≈ 0.11米

        选择建议：
        - 3位：城市尺度研究（粗略）
        - 4位：街区尺度研究（推荐）✅
        - 5位：建筑物尺度（精细）
        - 6位：厘米级（过于精细，计算量大）
        """
        self.precision = precision
        self.scale_meters = self._precision_to_scale(precision)

    def _precision_to_scale(self, precision: int) -> float:
        """
        将精度转换为米（赤道附近）

        Args:
            precision: 小数位数

        Returns:
            float: 对应的米数
        """
        return 111000 / (10 ** precision)

    def create_grids(self,
                    df: pd.DataFrame,
                    year: int,
                    month: int,
                    city: Optional[str] = None) -> pd.DataFrame:
        """
        为数据创建时空网格

        添加以下列：
        - lng_grid: 经度网格
        - lat_grid: 纬度网格
        - grid_uid: 唯一时空网格ID

        Args:
            df: 输入数据（必须包含lng, lat列）
            year: 年份
            month: 月份
            city: 城市名（可选，用于ID生成）

        Returns:
            pd.DataFrame: 添加了网格列的DataFrame

        示例：
            df = pd.DataFrame({
                'lng': [116.4074, 116.4075, 116.4074],
                'lat': [39.9042, 39.9043, 39.9042]
            })

            # 精度4位小数
            gridded = grid_manager.create_grids(df, 2023, 1)

            # 结果：
            #   lng_grid  lat_grid  grid_uid
            # 0  116.4074   39.9042  abc123...
            # 1  116.4075   39.9043  def456...
            # 2  116.4074   39.9042  abc123...  # 与第0行相同
        """
        result = df.copy()

        # 空间网格化
        result['lng_grid'] = result['lng'].round(self.precision)
        result['lat_grid'] = result['lat'].round(self.precision)

        # 生成唯一时空ID
        result['grid_uid'] = self._generate_grid_uid(
            result,
            year=year,
            month=month,
            city=city
        )

        # 验证唯一性
        n_unique = result['grid_uid'].nunique()
        n_total = len(result)
        reduction_rate = (1 - n_unique / n_total) * 100

        print(f"网格化完成：")
        print(f"  原始点数：{n_total:,}")
        print(f"  唯一网格数：{n_unique:,}")
        print(f"  冗余率：{reduction_rate:.1f}%")
        print(f"  网格精度：~{self.scale_meters:.0f}米")

        return result

    def _generate_grid_uid(self,
                          df: pd.DataFrame,
                          year: int,
                          month: int,
                          city: Optional[str] = None) -> pd.Series:
        """
        生成时空网格唯一ID

        ID包含：
        - 城市（可选）
        - 年份
        - 月份
        - 经度网格
        - 纬度网格

        使用UUID5确保相同输入产生相同输出（确定性）

        Args:
            df: 输入数据
            year: 年份
            month: 月份
            city: 城市名

        Returns:
            pd.Series: UUID字符串序列

        示例：
            # 相同时空 → 相同ID
            uid1 = generate_grid_uid(row1, 2023, 1, 'Beijing')
            uid2 = generate_grid_uid(row2, 2023, 1, 'Beijing')
            # 如果row1和row2在同一网格，uid1 == uid2

            # 不同时间 → 不同ID
            uid3 = generate_grid_uid(row3, 2023, 2, 'Beijing')
            # uid3 != uid1 (不同月份)
        """
        city_part = city if city else 'unknown'

        def make_uid(row):
            key = f"{city_part}_{year}_{month}_{row['lng_grid']}_{row['lat_grid']}"
            return uuid5(NAMESPACE_DNS, key).hex[:12]

        return df.apply(make_uid, axis=1)

    def get_unique_grids(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        获取唯一网格（用于GEE提取）

        对每个唯一网格只提取一次，大幅减少计算量

        Args:
            df: 包含grid_uid的DataFrame

        Returns:
            pd.DataFrame: 唯一网格的数据

        示例：
            # 原始数据：100万点
            # 唯一网格：10万个
            # 减少90%的GEE任务！
        """
        if 'grid_uid' not in df.columns:
            raise ValueError("DataFrame必须包含'grid_uid'列。请先调用create_grids()")

        # 按grid_uid去重，保留第一个出现的
        unique_grids = df.drop_duplicates(subset=['grid_uid'], keep='first')

        return unique_grids

    def aggregate_by_grid(self,
                         df: pd.DataFrame,
                         value_cols: list,
                         agg_func: str = 'mean',
                         preserve_cols: list = None) -> pd.DataFrame:
        """
        按网格聚合数据

        用于从GEE提取后，将网格值映射回所有原始点

        Args:
            df: 输入数据
            value_cols: 要聚合的列名（如['LST', 'NDVI']）
            agg_func: 聚合函数 ('mean', 'median', 'max', 'min', 'first')
            preserve_cols: 保留的列（不经聚合）

        Returns:
            pd.DataFrame: 聚合后的数据

        示例：
            # 假设已从GEE提取了LST值
            # 按网格聚合，得到每个网格的平均LST
            aggregated = grid_manager.aggregate_by_grid(
                df,
                value_cols=['LST'],
                agg_func='mean'
            )
        """
        if 'grid_uid' not in df.columns:
            raise ValueError("DataFrame必须包含'grid_uid'列")

        # 确定聚合字典
        agg_dict = {col: agg_func for col in value_cols}

        if preserve_cols:
            for col in preserve_cols:
                if col in df.columns and col not in value_cols:
                    agg_dict[col] = 'first'

        # 分组聚合
        result = df.groupby('grid_uid').agg(agg_dict).reset_index()

        return result

    def merge_results(self,
                     original_df: pd.DataFrame,
                     grid_results: pd.DataFrame,
                     merge_cols: list = None) -> pd.DataFrame:
        """
        将网格提取结果合并回原始数据

        Args:
            original_df: 原始数据（所有点）
            grid_results: 网格提取结果（唯一网格）
            merge_cols: 要合并的列（默认除grid_uid外的所有列）

        Returns:
            pd.DataFrame: 合并后的数据（所有点都有环境值）

        示例：
            # 从GEE提取了唯一网格的LST值
            grid_lst = pd.DataFrame({
                'grid_uid': ['abc123', 'def456'],
                'LST': [25.3, 28.1]
            })

            # 合并回所有原始点
            final_df = grid_manager.merge_results(
                original_df=social_media_df,
                grid_results=grid_lst
            )
        """
        if merge_cols is None:
            # 自动排除grid_uid
            merge_cols = [col for col in grid_results.columns if col != 'grid_uid']

        # 通过grid_uid合并
        result = original_df.merge(
            grid_results[['grid_uid'] + merge_cols],
            on='grid_uid',
            how='left'
        )

        return result

    def get_grid_info(self) -> dict:
        """
        获取网格管理器的信息

        Returns:
            dict: 包含精度、比例尺等信息的字典
        """
        return {
            'precision': self.precision,
            'scale_meters': self.scale_meters,
            'description': f'~{self.scale_meters:.0f}米精度'
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<GridManager: {self.precision}位小数 (~{self.scale_meters:.0f}m)>"
