"""
PM2.5提取器 - 卫星遥感反演PM2.5浓度

使用多种卫星数据源反演近地表PM2.5浓度
"""

import ee
from typing import Dict, Any
from core.base_extractor import BaseExtractor


class PM25Extractor(BaseExtractor):
    """
    PM2.5浓度提取器

    数据源：
        - MODIS MAIAC 气溶胶产品 (MCD19A2)
        - 结合地面观测数据反演

    空间分辨率：1公里
    时间分辨率：日
    单位：μg/m³

    方法：
        使用卫星反演的AOD结合气象数据估算PM2.5

    参考文献：
        - Lyapustin et al. (2018). "MODIS Collection 6 MAIAC Algorithm"
        - Di et al. (2019). "An ensemble-based model of PM2.5 concentration
          across the contiguous United States with high spatiotemporal resolution"
    """

    def get_collection(self) -> ee.ImageCollection:
        """
        获取PM2.5数据集

        使用MODIS MAIAC AOD产品作为基础数据
        可以通过模型转换为PM2.5浓度

        Returns:
            ee.ImageCollection: MODIS MAIAC数据集
        """
        # 使用MODIS MAIAC AOD产品
        # MCD19A2 v1 提供了1km分辨率的AOD数据
        return ee.ImageCollection('MODIS/006/MCD19A2_GRANULES')

    def apply_scale_factors(self, image: ee.Image) -> ee.Image:
        """
        应用定标系数并估算PM2.5

        MAIAC AOD产品使用0.001的定标因子

        PM2.5估算使用简化模型：
        PM2.5 = AOD × f(RH, PBLH, 其他因素)

        这里使用简化的线性关系作为示例：
        PM2.5 ≈ AOD × 100 (这是一个简化假设)

        实际应用中应该使用更复杂的模型或地面观测数据校准

        Args:
            image: 输入的MODIS影像

        Returns:
            ee.Image: 添加了PM2.5波段的影像

        注意：
            这是一个简化的PM2.5估算方法。
            对于研究用途，建议：
            1. 使用已验证的PM2.5产品（如从地面观测反演的）
            2. 或结合气象数据建立本地化模型
        """
        # 提取AOD波段（550nm）
        # MAIAC提供多个波段的AOD，这里使用0.47μm蓝光通道
        aod = image.select('Optical_Depth_047')

        # 应用定标因子（MAIAC使用0.001）
        aod_scaled = aod.multiply(0.001)

        # 简化的PM2.5估算
        # 注意：这只是一个示例，实际应用需要校准
        # PM2.5 ≈ AOD × 转换因子
        # 转换因子通常在50-150之间，取决于地区和季节

        # 使用保守的转换因子
        pm25_estimate = aod_scaled.multiply(100).rename('PM25')

        # 添加到原影像
        return image.addBands(pm25_estimate)

    def filter_by_quality(self, collection: ee.ImageCollection) -> ee.ImageCollection:
        """
        质量过滤

        使用QA波段过滤低质量数据

        Args:
            collection: 输入的影像集合

        Returns:
            ee.ImageCollection: 过滤后的影像集合
        """
        def apply_qa(img):
            # 获取QA波段
            qa = img.select('QA')

            # 提取质量标志
            # MAIAC QA的详细说明见产品文档
            # 这里进行基本的过滤

            # 应用定标
            scaled = self.apply_scale_factors(img)

            # 基本掩膜：排除无效值
            mask = qa.bitwiseAnd(1).eq(0)  # 假设bit 0表示数据质量

            return scaled.updateMask(mask)

        return collection.map(apply_qa)

    def get_band_name(self) -> str:
        """返回波段名称"""
        return 'PM25'

    def get_default_scale(self) -> int:
        """
        返回默认提取尺度

        MAIAC产品提供1km分辨率

        Returns:
            int: 1000米
        """
        return 1000

    def get_collection_id(self) -> str:
        """返回数据集ID"""
        return "MODIS/006/MCD19A2_GRANULES (PM2.5 estimated)"

    def get_spatial_resolution(self) -> int:
        """返回空间分辨率"""
        return 1000  # 1 km

    def get_temporal_resolution(self) -> str:
        """
        返回时间分辨率

        MAIAC提供每日产品

        Returns:
            str: "Daily"
        """
        return "Daily"

    def get_unit(self) -> str:
        """返回单位"""
        return "μg/m³"

    def get_required_config_keys(self) -> list:
        """
        返回必需的配置键

        PM2.5提取器可以接受可选的转换因子配置

        Returns:
            list: 空列表（所有参数都有默认值）
        """
        return []

    def get_temporal_composite(self,
                               collection: ee.ImageCollection,
                               start_date: str,
                               end_date: str,
                               reducer: str = 'mean') -> ee.Image:
        """
        创建时间合成影像

        对于PM2.5数据，可以使用平均值或中位数

        Args:
            collection: 影像集合
            start_date: 开始日期
            end_date: 结束日期
            reducer: 聚合方法

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
        提取PM2.5值

        Args:
            point: 点几何
            year: 年份
            month: 月份
            scale: 提取尺度（米）
            buffer_meters: 缓冲区半径（米）
            reducer: 降维方法

        Returns:
            dict: 包含PM2.5值和元数据的字典
        """
        result = super().extract_value(
            point, year, month, scale, buffer_meters, reducer
        )

        # 添加PM2.5特定的元数据
        result['data_source'] = 'MODIS_MAIAC'
        result['concentration_unit'] = 'μg/m³'
        result['estimation_method'] = 'AOD_to_PM2.5_conversion'

        return result

    def __repr__(self) -> str:
        """字符串表示"""
        return "<PM25Extractor: MODIS MAIAC AOD @ 1km, Daily>"


class GroundPM25Extractor(BaseExtractor):
    """
    地面观测PM2.5提取器

    从地面监测站数据提取PM2.5浓度

    注意：这需要预先上传到GEE的地面观测数据
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化

        Args:
            config: 配置字典，应包含：
                - station_collection: 地面站点数据的Asset ID
        """
        super().__init__(config)
        self.station_collection_id = config.get('station_collection') if config else None

    def get_collection(self) -> ee.ImageCollection:
        """
        获取地面观测数据

        Returns:
            ee.ImageCollection: 地面观测数据集

        注意：
            这需要用户预先上传地面观测数据到GEE
        """
        if not self.station_collection_id:
            raise ValueError(
                "未指定地面站点数据集。请在config中提供'station_collection'参数"
            )

        # 这里假设用户已上传地面数据
        # 实际实现取决于数据格式
        raise NotImplementedError(
            "地面观测提取器需要具体的地面数据集。"
            "请提供地面站点数据的Asset ID。"
        )

    def get_band_name(self) -> str:
        """返回波段名称"""
        return 'PM25_ground'

    def get_default_scale(self) -> int:
        """返回默认提取尺度"""
        return 1000  # 1 km

    def get_spatial_resolution(self) -> int:
        """返回空间分辨率"""
        return 1000

    def get_temporal_resolution(self) -> str:
        """返回时间分辨率"""
        return "Daily (if available)"

    def get_unit(self) -> str:
        """返回单位"""
        return "μg/m³"

    def __repr__(self) -> str:
        """字符串表示"""
        return "<GroundPM25Extractor: Ground station observations>"
