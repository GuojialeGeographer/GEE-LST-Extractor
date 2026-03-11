"""
NDVI提取器 - 归一化植被指数

从Landsat 8/9数据计算归一化植被指数（NDVI）
"""

import ee
from typing import Dict, Any
from core.base_extractor import BaseExtractor


class NDVIExtractor(BaseExtractor):
    """
    归一化植被指数提取器

    数据源：
        - Landsat 8 Collection 2 Tier 1 Level 2
        - Landsat 9 Collection 2 Tier 1 Level 2

    空间分辨率：30米
    时间分辨率：16天（单卫星），8天（合并后）
    单位：无（-1到1）

    计算公式：
        NDVI = (NIR - Red) / (NIR + Red)

        Landsat 8/9波段：
        - NIR (近红外): SR_B5
        - Red (红): SR_B4

    取值范围：
        - -1 到 1
        - 负值：水体、雪、云等
        - 0-0.2：裸地、建筑物
        - 0.2-0.5：稀疏植被
        - 0.5-1.0：茂密植被

    参考文献：
        - Tucker, C. J. (1979). "Red and photographic infrared linear
          combinations for monitoring vegetation." Remote Sensing of
          Environment, 8(2), 127-150.
    """

    def get_collection(self) -> ee.ImageCollection:
        """
        获取Landsat 8/9 ImageCollection

        使用Collection 2 Tier 1 Level 2产品

        Returns:
            ee.ImageCollection: Landsat 8/9数据集
        """
        l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')

        if self.config.get('use_landsat_9', True):
            return l8.merge(l9)
        return l8

    def apply_scale_factors(self, image: ee.Image) -> ee.Image:
        """
        计算NDVI

        步骤：
        1. 应用反射率定标系数
        2. 计算NDVI = (NIR - Red) / (NIR + Red)

        定标系数（Collection 2）：
        - Scale factor: 0.0000275
        - Offset: -0.2

        公式：
            Reflectance = DN × 0.0000275 - 0.2

        Args:
            image: 输入的Landsat影像

        Returns:
            ee.Image: 添加了NDVI波段的影像

        参考文献：
            USGS Landsat 8 Level-1 Data Product Guide
        """
        # 应用定标系数，转换为反射率
        nir = image.select('SR_B5').multiply(0.0000275).add(-0.2)
        red = image.select('SR_B4').multiply(0.0000275).add(-0.2)

        # 计算NDVI
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')

        # 添加到原影像
        return image.addBands(ndvi)

    def filter_by_quality(self, collection: ee.ImageCollection) -> ee.ImageCollection:
        """
        去云和云阴影

        与LST使用相同的QA_PIXEL波段进行质量控制

        Args:
            collection: 输入的Landsat影像集合

        Returns:
            ee.ImageCollection: 去云后的影像集合
        """
        def mask_clouds(img):
            # 获取QA波段
            qa = img.select('QA_PIXEL')

            # 云和云阴影的位掩膜
            cloud_bitmask = 1 << 3
            shadow_bitmask = 1 << 4

            # 创建掩膜
            mask = qa.bitwiseAnd(cloud_bitmask).eq(0).And(
                  qa.bitwiseAnd(shadow_bitmask).eq(0))

            # 应用定标和掩膜
            scaled = self.apply_scale_factors(img)
            return scaled.updateMask(mask)

        return collection.map(mask_clouds)

    def get_band_name(self) -> str:
        """返回波段名称"""
        return 'NDVI'

    def get_default_scale(self) -> int:
        """
        返回默认提取尺度

        Landsat反射率波段为30米

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
        """返回时间分辨率"""
        if self.config.get('use_landsat_9', True):
            return "8 days (Landsat 8+9 combined)"
        return "16 days (Landsat 8 only)"

    def get_unit(self) -> str:
        """返回单位"""
        return "unitless (-1 to 1)"

    def get_required_config_keys(self) -> list:
        """返回必需的配置键（无）"""
        return []

    def get_temporal_composite(self,
                               collection: ee.ImageCollection,
                               start_date: str,
                               end_date: str,
                               reducer: str = 'mean') -> ee.Image:
        """
        创建月度NDVI合成影像

        对于NDVI数据，推荐使用中位数（median）而非平均值，
        可以更好地消除云、阴影等异常值的影响。

        Args:
            collection: 影像集合
            start_date: 开始日期
            end_date: 结束日期
            reducer: 聚合方法（'mean', 'median', 'max'）

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
                     reducer: str = 'median') -> Dict[str, Any]:
        """
        提取NDVI值

        默认使用中位数（median）作为聚合方法，
        对异常值更稳健

        Args:
            point: 点几何
            year: 年份
            month: 月份
            scale: 提取尺度（米）
            buffer_meters: 缓冲区半径（米）
            reducer: 降维方法（默认'median'）

        Returns:
            dict: 包含NDVI值和元数据的字典
        """
        result = super().extract_value(
            point, year, month, scale, buffer_meters, reducer
        )

        # 添加NDVI特定的元数据
        result['data_source'] = 'Landsat' if not self.config.get('use_landsat_9', True) else 'Landsat8+9'
        result['index_range'] = '(-1, 1)'
        result['vegetation_threshold'] = '>0.2 indicates vegetation'

        return result

    def __repr__(self) -> str:
        """字符串表示"""
        l9_info = "+L9" if self.config.get('use_landsat_9', True) else ""
        return f"<NDVIExtractor: Landsat8{l9_info} @ 30m, 8-day revisit>"
