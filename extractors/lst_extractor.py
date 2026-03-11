"""
LST提取器 - Landsat 8/9 地表温度

从Landsat 8和Landsat 9 Collection 2 Tier 1 Level 2数据集提取地表温度
"""

import ee
from typing import Dict, Any
from core.base_extractor import BaseExtractor


class LSTExtractor(BaseExtractor):
    """
    Landsat 8/9 地表温度提取器

    数据源：
        - Landsat 8 Collection 2 Tier 1 Level 2
        - Landsat 9 Collection 2 Tier 1 Level 2

    空间分辨率：30米（重采样后）
    时间分辨率：16天（单个卫星），8天（合并后）
    单位：摄氏度 (°C)

    定标公式：
        LST (°C) = ST_B10 × 0.00341802 + 149.0 - 273.15

    参考文献：
        - USGS Landsat 8-9 Level-2 Data Product Guide
        - https://www.usgs.gov/landsat-missions/landsat-8-9-level-2-data-product-guide
    """

    def get_collection(self) -> ee.ImageCollection:
        """
        获取Landsat 8/9 ImageCollection

        使用Collection 2 Tier 1 Level 2产品（已地形校正）

        Returns:
            ee.ImageCollection: Landsat 8/9数据集
        """
        l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')

        # 根据配置决定是否使用Landsat 9
        if self.config.get('use_landsat_9', True):
            return l8.merge(l9)
        return l8

    def apply_scale_factors(self, image: ee.Image) -> ee.Image:
        """
        应用LST定标系数

        USGS官方定标公式（Collection 2）：
        1. 转换为开尔文温度：
           LST_K = ST_B10 × 0.00341802 + 149.0

        2. 转换为摄氏度：
           LST_C = LST_K - 273.15

        Args:
            image: 输入的Landsat影像

        Returns:
            ee.Image: 添加了LST波段的影像

        参考：
            USGS Landsat 8 Level-1 Data Product Guide
        """
        # 转换为开尔文
        lst_kelvin = image.select('ST_B10').multiply(0.00341802).add(149.0)

        # 转换为摄氏度
        lst_celsius = lst_kelvin.subtract(273.15).rename('LST')

        # 添加到原影像
        return image.addBands(lst_celsius)

    def filter_by_quality(self, collection: ee.ImageCollection) -> ee.ImageCollection:
        """
        去云和云阴影

        使用QA_PIXEL波段进行质量控制：
        - Bit 3: 云
        - Bit 4: 云阴影

        Args:
            collection: 输入的Landsat影像集合

        Returns:
            ee.ImageCollection: 去云后的影像集合

        参考文献：
            Foga et al. (2017). "Cloud detection in Landsat 8 OLI using the QA band"
            Remote Sensing, 9(7), 677.
        """
        def mask_clouds(img):
            # 获取QA波段
            qa = img.select('QA_PIXEL')

            # 云和云阴影的位掩膜
            cloud_bitmask = 1 << 3
            shadow_bitmask = 1 << 4

            # 创建掩膜：无云且无云阴影的像素为True
            mask = qa.bitwiseAnd(cloud_bitmask).eq(0).And(
                  qa.bitwiseAnd(shadow_bitmask).eq(0))

            # 应用定标和掩膜
            scaled = self.apply_scale_factors(img)
            return scaled.updateMask(mask)

        return collection.map(mask_clouds)

    def get_band_name(self) -> str:
        """返回波段名称"""
        return 'LST'

    def get_default_scale(self) -> int:
        """
        返回默认提取尺度

        Landsat热红外波段原始分辨率为100米，
        但已重采样到30米以匹配其他波段。

        Returns:
            int: 30米
        """
        return 30

    def get_collection_id(self) -> str:
        """返回数据集ID"""
        if self.config.get('use_landsat_9', True):
            return "LANDSAT/LC08/C02/T1_L2 + LANDSAT/LC09/C02/T1_L2"
        return "LANDSAT/LC08/C02/T1_L2"

    def get_spatial_resolution(self) -> int:
        """返回空间分辨率"""
        return 30

    def get_temporal_resolution(self) -> str:
        """
        返回时间分辨率

        - Landsat 8: 16天
        - Landsat 9: 16天
        - 合并后: 8天

        Returns:
            str: 时间分辨率描述
        """
        if self.config.get('use_landsat_9', True):
            return "8 days (Landsat 8+9 combined)"
        return "16 days (Landsat 8 only)"

    def get_unit(self) -> str:
        """返回单位"""
        return "Celsius (°C)"

    def get_required_config_keys(self) -> list:
        """
        返回必需的配置键

        LST提取器没有必需的配置键（所有参数都有默认值）

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
        创建月度LST合成影像

        对于LST数据，通常使用平均值作为月度代表值。
        中位数也是一种选择，对极端值更稳健。

        Args:
            collection: 影像集合
            start_date: 开始日期
            end_date: 结束日期
            reducer: 聚合方法（'mean' 或 'median'）

        Returns:
            ee.Image: 月度合成影像
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
        提取LST值

        扩展了父类方法，添加LST特定的元数据

        Args:
            point: 点几何
            year: 年份
            month: 月份
            scale: 提取尺度（米）
            buffer_meters: 缓冲区半径（米）
            reducer: 降维方法

        Returns:
            dict: 包含LST值和元数据的字典
        """
        result = super().extract_value(
            point, year, month, scale, buffer_meters, reducer
        )

        # 添加LST特定的元数据
        result['data_source'] = 'Landsat' if not self.config.get('use_landsat_9', True) else 'Landsat8+9'
        result['temperature_unit'] = 'Celsius'

        return result

    def __repr__(self) -> str:
        """字符串表示"""
        l9_info = "+L9" if self.config.get('use_landsat_9', True) else ""
        return f"<LSTExtractor: Landsat8{lg9_info} @ 30m, 8-day revisit>"
