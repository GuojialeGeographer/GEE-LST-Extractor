"""
GEE通用环境数据提取框架 - 抽象基类

所有数据源提取器的基类，定义统一接口和通用方法
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import ee


class BaseExtractor(ABC):
    """
    所有数据源提取器的抽象基类

    设计原则：
    1. 定义所有数据源必须实现的接口
    2. 提供默认实现的通用方法
    3. 允许子类覆盖特定行为以适应特殊需求

    使用方法：
        继承此类并实现所有抽象方法：
        - get_collection()
        - apply_scale_factors()
        - filter_by_quality()
        - get_band_name()
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化提取器

        Args:
            config: 配置字典，包含数据源特定的参数
        """
        self.config = config
        self.name = self.__class__.__name__
        self._validate_config()

    def _validate_config(self):
        """
        验证配置是否包含必需的键

        可被子类覆盖以添加自定义验证逻辑
        """
        required_keys = self.get_required_config_keys()
        for key in required_keys:
            if key not in self.config:
                raise ValueError(
                    f"{self.name}: 缺少必需的配置键 '{key}'"
                )

    # ========== 必须实现的抽象方法 ==========

    @abstractmethod
    def get_collection(self) -> ee.ImageCollection:
        """
        返回GEE ImageCollection

        这是提取器的核心方法，每个数据源必须指定使用的GEE数据集

        Returns:
            ee.ImageCollection: GEE影像集合

        示例：
            def get_collection(self):
                return ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        """
        pass

    @abstractmethod
    def apply_scale_factors(self, image: ee.Image) -> ee.Image:
        """
        应用定标系数，将DN值转换为物理量

        大多数遥感数据的原始值是数字量化值（DN），需要转换为物理量。
        例如：
        - LST: DN → 开尔文 → 摄氏度
        - 反射率: DN → 表观反射率
        - 辐射亮度: DN → 辐射值

        Args:
            image: 输入的原始影像

        Returns:
            ee.Image: 添加了定标后波段的影像

        示例：
            def apply_scale_factors(self, image):
                lst_kelvin = image.select('ST_B10').multiply(0.00341802).add(149.0)
                lst_celsius = lst_kelvin.subtract(273.15).rename('LST')
                return image.addBands(lst_celsius)
        """
        pass

    @abstractmethod
    def filter_by_quality(self, collection: ee.ImageCollection) -> ee.ImageCollection:
        """
        根据质量控制条件过滤影像

        对影像集合应用质量控制，常见的包括：
        - 去除云和云阴影
        - 去除低质量像素
        - 基于QA波段过滤

        Args:
            collection: 输入的影像集合

        Returns:
            ee.ImageCollection: 过滤后的影像集合

        示例：
            def filter_by_quality(self, collection):
                def mask_clouds(img):
                    qa = img.select('QA_PIXEL')
                    mask = qa.bitwiseAnd(1<<3).eq(0)  # 去云
                    return self.apply_scale_factors(img).updateMask(mask)
                return collection.map(mask_clouds)
        """
        pass

    @abstractmethod
    def get_band_name(self) -> str:
        """
        返回要提取的波段名称

        这个名称将用于：
        1. 结果DataFrame的列名
        2. 质量标记前缀
        3. 文档和日志输出

        Returns:
            str: 波段名称

        示例：
            def get_band_name(self):
                return 'LST'
        """
        pass

    # ========== 可选覆盖的方法（提供默认实现） ==========

    def get_required_config_keys(self) -> list:
        """
        返回必需的配置键列表

        可被子类覆盖以指定必需的配置参数

        Returns:
            list: 必需配置键的列表

        示例：
            def get_required_config_keys(self):
                return ['data_source', 'resolution']
        """
        return []

    def get_temporal_composite(self,
                               collection: ee.ImageCollection,
                               start_date: str,
                               end_date: str,
                               reducer: str = 'mean') -> ee.Image:
        """
        创建时间合成影像

        将多时相的影像集合合成为单幅影像，常用的聚合方法包括：
        - mean: 平均值（默认，适用于LST、NDVI等）
        - median: 中位数（更稳健，对异常值不敏感）
        - max: 最大值（适用于峰值数据）
        - min: 最小值（适用于谷值数据）
        - mosaic: 按时间顺序镶嵌（最后像元优先）

        Args:
            collection: 影像集合
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            reducer: 聚合方法 ('mean', 'median', 'max', 'min', 'mosaic')

        Returns:
            ee.Image: 时间合成影像

        示例：
            # 月度均值
            composite = extractor.get_temporal_composite(
                collection, '2023-01-01', '2023-01-31', 'mean'
            )

            # 月度中位数（更稳健）
            composite = extractor.get_temporal_composite(
                collection, '2023-01-01', '2023-01-31', 'median'
            )
        """
        if reducer == 'mean':
            return collection.filterDate(start_date, end_date).mean()
        elif reducer == 'median':
            return collection.filterDate(start_date, end_date).median()
        elif reducer == 'max':
            return collection.filterDate(start_date, end_date).max()
        elif reducer == 'min':
            return collection.filterDate(start_date, end_date).min()
        elif reducer == 'mosaic':
            return collection.filterDate(start_date, end_date).mosaic()
        else:
            raise ValueError(
                f"不支持的聚合方法: {reducer}. "
                "支持的选项: 'mean', 'median', 'max', 'min', 'mosaic'"
            )

    def get_spatial_buffer(self,
                          point: ee.Geometry.Point,
                          buffer_meters: int = 0) -> ee.Geometry:
        """
        获取点或缓冲区

        用于提取区域统计值而不仅是单点值。

        Args:
            point: 点几何
            buffer_meters: 缓冲区半径（米），0表示不创建缓冲区

        Returns:
            ee.Geometry: 点或缓冲区

        示例：
            # 提取单点值
            region = extractor.get_spatial_buffer(point, buffer_meters=0)

            # 提取1km缓冲区内的平均值
            region = extractor.get_spatial_buffer(point, buffer_meters=1000)
        """
        if buffer_meters > 0:
            return point.buffer(buffer_meters)
        return point

    def extract_value(self,
                     point: ee.Geometry.Point,
                     year: int,
                     month: int,
                     scale: int = None,
                     buffer_meters: int = 0,
                     reducer: str = 'mean') -> Dict[str, Any]:
        """
        提取单个点的值（通用方法）

        这是核心的提取方法，封装了完整的提取流程：
        1. 构建时间范围
        2. 获取数据集
        3. 质量过滤和定标
        4. 时间聚合
        5. 空间提取

        Args:
            point: 点几何
            year: 年份
            month: 月份
            scale: 提取尺度（米），None表示使用默认尺度
            buffer_meters: 空间缓冲区半径（米）
            reducer: 值提取时的降维方法（'mean', 'median', 'mode'等）

        Returns:
            dict: 包含值和元数据的字典
                {
                    'value': 提取的值,
                    'year': 年份,
                    'month': 月份,
                    'source': 提取器名称,
                    'scale': 提取尺度,
                    'buffer': 缓冲区大小
                }

        示例：
            point = ee.Geometry.Point([116.4074, 39.9042])
            result = extractor.extract_value(point, 2023, 1)
            print(result['value'])  # 提取的LST值
        """
        # 构建日期范围
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-28"

        # 获取数据集
        collection = self.get_collection()

        # 质量过滤和定标
        filtered = self.filter_by_quality(collection)

        # 时间聚合
        composite = self.get_temporal_composite(
            filtered, start_date, end_date,
            reducer=self.config.get('temporal_reducer', 'mean')
        )

        # 空间缓冲
        region = self.get_spatial_buffer(point, buffer_meters)

        # 设置默认尺度
        if scale is None:
            scale = self.get_default_scale()

        # 选择波段并提取值
        band_name = self.get_band_name()

        # 使用reducer提取值
        if reducer == 'mean':
            ee_reducer = ee.Reducer.mean()
        elif reducer == 'median':
            ee_reducer = ee.Reducer.median()
        elif reducer == 'mode':
            ee_reducer = ee.Reducer.mode()
        else:
            ee_reducer = ee.Reducer.mean()

        value = composite.select(band_name).reduceRegion(
            reducer=ee_reducer,
            geometry=region,
            scale=scale,
            maxPixels=1e9
        ).get(band_name)

        return {
            'value': value,
            'year': year,
            'month': month,
            'source': self.name,
            'scale': scale,
            'buffer': buffer_meters,
            'reducer': reducer
        }

    def get_default_scale(self) -> int:
        """
        返回默认提取尺度（米）

        默认值为30米（Landsat分辨率）。
        可被子类覆盖以指定数据集的固有分辨率。

        Returns:
            int: 默认尺度（米）

        示例：
            def get_default_scale(self):
                return 1000  # MODIS数据
        """
        return 30

    def get_collection_id(self) -> str:
        """
        返回数据集ID（用于文档和引用）

        Returns:
            str: 数据集ID

        示例：
            def get_collection_id(self):
                return "LANDSAT/LC08/C02/T1_L2"
        """
        return "Unknown Dataset"

    def get_spatial_resolution(self) -> int:
        """
        返回数据集的空间分辨率（米）

        Returns:
            int: 空间分辨率（米）
        """
        return self.get_default_scale()

    def get_temporal_resolution(self) -> str:
        """
        返回数据集的时间分辨率

        Returns:
            str: 时间分辨率描述

        示例：
            return "16 days"  # Landsat
            return "1 day"    # MODIS
            return "Monthly"  # 静态数据
        """
        return "Unknown"

    def get_unit(self) -> str:
        """
        返回数据的单位

        Returns:
            str: 单位描述

        示例：
            return "Celsius"       # LST
            return "unitless"      # NDVI
            return "µg/m³"        # PM2.5
            return "mm"           # 降水
        """
        return "Unknown"

    def get_info(self) -> Dict[str, Any]:
        """
        返回数据源的完整信息

        用于文档生成和数据源说明

        Returns:
            dict: 包含所有元数据的字典
        """
        return {
            'name': self.name,
            'collection_id': self.get_collection_id(),
            'spatial_resolution': self.get_spatial_resolution(),
            'temporal_resolution': self.get_temporal_resolution(),
            'unit': self.get_unit(),
            'band_name': self.get_band_name(),
            'config': self.config
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.name}: {get_collection_id()} @ {self.get_spatial_resolution()}m>"
