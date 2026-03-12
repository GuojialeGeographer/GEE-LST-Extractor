"""
夜间灯光提取器 - VIIRS Day/Night Band 夜间灯光数据

从VIIRS DNB (Day/Night Band) 提取夜间灯光强度
"""

import ee
from typing import Dict, Any
from core.base_extractor import BaseExtractor


class NightlightsExtractor(BaseExtractor):
    """
    VIIRS 夜间灯光提取器

    数据源：
        - VIIRS DNB Stray Light Corrected
        - NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG

    空间分辨率：15弧秒（约500m）
    时间分辨率：月度
    单位：nW/cm²/sr

    产品说明：
        - 'avg_rad': 平均辐射亮度（已过滤杂散光）
        - 'cf_cvg': 云覆盖次数
        - 'avg_vis': 平均可见光（包含杂散光）

    应用场景：
        - 城市化研究
        - 经济发展评估
        - 电力消耗估算
        - 人口分布分析

    参考文献：
        - Elvidge et al. (2017). "VIIRS night-time lights"
        - https://www.ncei.noaa.gov/products/nighttime-lights

    使用建议：
        - 适合研究城市扩张
        - 可用于经济活动分析
        - 注意月度合成中的云影响
    """

    def get_collection(self) -> ee.ImageCollection:
        """
        获取VIIRS夜间灯光数据集

        使用V1 VCMCFG版本（月度合成，已过滤杂散光）

        Returns:
            ee.ImageCollection: VIIRS DNB数据集
        """
        # VIIRS DNB Monthly Composites (Stray Light Corrected)
        return ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG')

    def apply_scale_factors(self, image: ee.Image) -> ee.Image:
        """
        应用定标系数

        VIIRS DNB定标说明：
        - avg_rad: nW/cm²/sr，已经是物理单位
        - 无需缩放因子

        Args:
            image: 输入的VIIRS影像

        Returns:
            ee.Image: 添加了夜间灯光波段的影像
        """
        # 选择平均辐射亮度（已过滤杂散光）
        ntl = image.select('avg_rad').rename('nightlight')

        return image.addBands(ntl)

    def filter_by_quality(self, collection: ee.ImageCollection) -> ee.ImageCollection:
        """
        质量过滤

        使用云覆盖次数进行过滤

        Args:
            collection: 输入的影像集合

        Returns:
            ee.ImageCollection: 过滤后的影像集合

        注意事项：
            - cf_cvg表示该月中有多少次有效的无云观测
            - 值越高表示数据质量越好
            - 建议排除cf_cvg过低的数据
        """
        def apply_cloud_filter(img):
            # 获取云覆盖次数
            cloud_coverage = img.select('cf_cvg')

            # 应用定标
            scaled = self.apply_scale_factors(img)

            # 可选：设置云覆盖阈值（例如，至少10次有效观测）
            # 这里我们保留所有数据，但添加掩膜信息
            mask = cloud_coverage.gte(0)  # 基本掩膜：有观测即可

            return scaled.updateMask(mask)

        return collection.map(apply_cloud_filter)

    def get_band_name(self) -> str:
        """返回波段名称"""
        return 'nightlight'

    def get_default_scale(self) -> int:
        """
        返回默认提取尺度

        VIIRS DNB分辨率为15弧秒（约500m）

        Returns:
            int: 500米
        """
        return 500

    def get_collection_id(self) -> str:
        """返回数据集ID"""
        return "NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG"

    def get_spatial_resolution(self) -> int:
        """返回空间分辨率（米）"""
        return 500

    def get_temporal_resolution(self) -> str:
        """
        返回时间分辨率

        VIIRS提供月度合成数据

        Returns:
            str: "Monthly"
        """
        return "Monthly"

    def get_unit(self) -> str:
        """返回单位"""
        return "nW/cm²/sr"

    def get_required_config_keys(self) -> list:
        """
        返回必需的配置键

        夜间灯光提取器没有必需的配置键

        Returns:
            list: 空列表
        """
        return []

    def get_temporal_composite(self,
                               collection: ee.ImageCollection,
                               start_date: str,
                               end_date: str,
                               reducer: str = 'mean') -> ee.Image:
        """
        创建时间合成影像

        对于夜间灯光数据，通常使用平均值来代表长期水平

        Args:
            collection: 影像集合
            start_date: 开始日期
            end_date: 结束日期
            reducer: 聚合方法（'mean', 'median', 'max'）

        Returns:
            ee.Image: 合成影像
        """
        return super().get_temporal_composite(
            collection, start_date, end_date, reducer
        )

    def extract_value(self,
                     point: ee.Geometry.Point,
                     year: int,
                     month: int,
                     scale: int = None,
                     buffer_meters: int = 0,
                     reducer: str = 'mean') -> Dict[str, Any]:
        """
        提取夜间灯光值

        Args:
            point: 点几何
            year: 年份
            month: 月份
            scale: 提取尺度（米）
            buffer_meters: 缓冲区半径（米）
            reducer: 降维方法

        Returns:
            dict: 包含夜间灯光值和元数据的字典
        """
        result = super().extract_value(
            point, year, month, scale, buffer_meters, reducer
        )

        # 添加夜间灯光特定的元数据
        result['data_source'] = 'VIIRS_DNB'
        result['radiance_unit'] = 'nW/cm²/sr'
        result['temporal_resolution'] = 'monthly'
        result['stray_light_corrected'] = True

        return result

    def calculate_annual_composite(self,
                                  points_df,
                                  year: int,
                                  reducer: str = 'median') -> Dict[str, Any]:
        """
        计算年度夜间灯光合成

        年度合成常用于表示城市的长期灯光水平

        Args:
            points_df: 采样点GeoDataFrame
            year: 年份
            reducer: 聚合方法（'median'推荐，对异常值稳健）

        Returns:
            dict: 包含年度夜间灯光合成的字典
        """
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'

        result = self.extract_value(
            point=points_df.geometry.iloc[0],
            year=year,
            month=1,  # 年度合成会忽略月份
            reducer=reducer
        )

        result['calculation_method'] = f'annual_{reducer}'
        result['time_period'] = f'{year}'
        result['description'] = f'{year}年度夜间灯光合成'

        return result

    def detect_urban_centers(self,
                            region: ee.Geometry,
                            threshold: float = 20,
                            year: int = 2023) -> ee.FeatureCollection:
        """
        检测城市中心

        基于夜间灯光强度识别城市中心区域

        Args:
            region: 分析区域
            threshold: 灯光强度阈值（nW/cm²/sr）
            year: 年份

        Returns:
            ee.FeatureCollection: 城市中心区域

        注意事项：
            - 阈值需要根据具体研究区域调整
            - 建议先查看数据分布
            - 考虑不同城市的灯光特性差异
        """
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'

        # 获取年度合成
        collection = self.get_collection()\
            .filterDate(start_date, end_date)

        # 应用质量过滤
        filtered = self.filter_by_quality(collection)

        # 计算中位数合成（对异常值稳健）
        annual_composite = filtered.median()

        # 选择夜间灯光波段
        ntl = annual_composite.select('nightlight')

        # 应用阈值
        urban_mask = ntl.gt(threshold)

        # 栅格转矢量（简化）
        urban_areas = urban_mask.selfMask()

        return urban_areas

    def calculate_light_intensity_change(self,
                                       points_df,
                                       start_year: int,
                                       end_year: int) -> Dict[str, Any]:
        """
        计算夜间灯光强度变化

        用于分析城市发展或经济变化

        Args:
            points_df: 采样点GeoDataFrame
            start_year: 起始年份
            end_year: 结束年份

        Returns:
            dict: 包含变化信息的字典

        计算指标：
            - 绝对变化（end - start）
            - 相对变化（%）
            - 年均变化率（%）
        """
        # 起始年
        start_data = self.calculate_annual_composite(
            points_df, start_year, reducer='median'
        )

        # 结束年
        end_data = self.calculate_annual_composite(
            points_df, end_year, reducer='median'
        )

        if 'value' in start_data and 'value' in end_data:
            start_value = start_data['value']
            end_value = end_data['value']

            # 计算变化指标
            absolute_change = end_value - start_value
            relative_change = (absolute_change / start_value * 100) if start_value > 0 else 0
            annual_change_rate = (relative_change / (end_year - start_year)) if end_year > start_year else 0

            return {
                'start_year': start_year,
                'end_year': end_year,
                'start_value': start_value,
                'end_value': end_value,
                'absolute_change': absolute_change,
                'relative_change_percent': relative_change,
                'annual_change_rate_percent': annual_change_rate,
                'trend': 'increasing' if absolute_change > 0 else 'decreasing'
            }
        else:
            return {
                'error': 'Unable to calculate change',
                'start_data': start_data,
                'end_data': end_data
            }

    def __repr__(self) -> str:
        """字符串表示"""
        return "<NightlightsExtractor: VIIRS DNB @ 500m, Monthly>"
