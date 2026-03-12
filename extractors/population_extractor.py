"""
人口密度提取器 - WorldPop 人口数据

从WorldPop数据集提取人口密度信息
"""

import ee
from typing import Dict, Any
from core.base_extractor import BaseExtractor


class PopulationExtractor(BaseExtractor):
    """
    WorldPop 人口密度提取器

    数据源：
        - WorldPop 100m分辨率人口数据
        - WorldPop/GP/100m/pop/xxx (根据国家代码不同)

    空间分辨率：100m（约3弧秒）
    时间分辨率：年度
    单位：人/100m x 100m (人/平方公里)

    产品说明：
        - 不同国家有不同的人口栅格数据集
        - 数据格式为GeoTIFF
        - 需要根据国家代码选择正确的数据集

    应用场景：
        - 人口分布研究
        - 城市规划分析
        - 公共设施选址
        - 社会经济研究

    参考文献：
        - WorldPop (www.worldpop.org)
        - Linard et al. (2012). "Modelling population distribution..."

    使用建议：
        - 适合社会科学研究
        - 可用于城市规划
        - 注意数据年份（通常有1-2年延迟）
    """

    # 常见国家/地区的WorldPop数据集ID
    DATASETS = {
        '中国': 'WorldPop/GP/100m/pop/CNV_2015',
        '北京': 'WorldPop/GP/100m/pop/CNV_2015',  # 使用国家数据
        '上海': 'WorldPop/GP/100m/pop/CNV_2015',
        '广州': 'WorldPop/GP/100m/pop/CNV_2015',
        '美国': 'WorldPop/GP/100m/pop/USA_2015',
        '印度': 'WorldPop/GP/100m/pop/IND_2015',
        '全球': 'WorldPop/GP/100m/pop/global_2015',  # 如果有全球数据集
    }

    def get_collection(self) -> ee.ImageCollection:
        """
        获取WorldPop人口数据集

        注意：WorldPop数据集是静态影像，不是影像集合
        因此这里返回一个单帧影像的集合

        Returns:
            ee.ImageCollection: WorldPop人口数据集
        """
        # 默认使用中国数据
        # 实际使用时应该根据研究区域选择合适的数据集
        return ee.ImageCollection(self.DATASETS['中国'])

    def apply_scale_factors(self, image: ee.Image) -> ee.Image:
        """
        应用定标系数

        WorldPop人口数据说明：
        - 数据已经是人口数量（人/100m x 100m）
        - 无需缩放因子
        - 可选：转换为每平方公里（乘以100）

        Args:
            image: 输入的WorldPop影像

        Returns:
            ee.Image: 添加了人口波段的影像
        """
        # 选择第一个波段（人口数量）
        # WorldPop数据集的波段名称通常是'b1'或'population'
        band_names = image.bandNames().getInfo()

        if 'population' in band_names:
            pop = image.select('population')
        elif 'b1' in band_names:
            pop = image.select('b1')
        else:
            # 使用第一个波段
            pop = image.select(0)

        # 重命名
        pop_renamed = pop.rename('population')

        return image.addBands(pop_renamed)

    def filter_by_quality(self, collection: ee.ImageCollection) -> ee.ImageCollection:
        """
        质量过滤

        WorldPop数据通常是经过质量控制的高质量数据
        这里进行基本的过滤

        Args:
            collection: 输入的影像集合

        Returns:
            ee.ImageCollection: 过滤后的影像集合
        """
        def apply_basic_filter(img):
            # 应用定标
            scaled = self.apply_scale_factors(img)

            # 基本掩膜：排除非正值
            mask = scaled.select('population').gt(0)

            return scaled.updateMask(mask)

        return collection.map(apply_basic_filter)

    def get_band_name(self) -> str:
        """返回波段名称"""
        return 'population'

    def get_default_scale(self) -> int:
        """
        返回默认提取尺度

        WorldPop数据分辨率为100m

        Returns:
            int: 100米
        """
        return 100

    def get_collection_id(self) -> str:
        """返回数据集ID"""
        return "WorldPop/GP/100m/pop"

    def get_spatial_resolution(self) -> int:
        """返回空间分辨率（米）"""
        return 100

    def get_temporal_resolution(self) -> str:
        """
        返回时间分辨率

        WorldPop提供年度数据

        Returns:
            str: "Annual"
        """
        return "Annual"

    def get_unit(self) -> str:
        """
        返回单位

        WorldPop原始数据单位是 人/100m x 100m
        """
        return "people/100m²"

    def get_required_config_keys(self) -> list:
        """
        返回必需的配置键

        人口提取器可以接受可选的国家代码配置

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

        对于人口数据，通常使用最新的可用数据

        Args:
            collection: 影像集合
            start_date: 开始日期（忽略，人口数据是静态的）
            end_date: 结束日期（忽略，人口数据是静态的）
            reducer: 聚合方法（忽略）

        Returns:
            ee.Image: 人口数据影像
        """
        # 人口数据是静态的，直接返回第一幅影像
        return collection.first()

    def extract_value(self,
                     point: ee.Geometry.Point,
                     year: int,
                     month: int = None,
                     scale: int = None,
                     buffer_meters: int = 0,
                     reducer: str = 'mean') -> Dict[str, Any]:
        """
        提取人口值

        Args:
            point: 点几何
            year: 年份（用于选择合适的数据集）
            month: 月份（人口数据忽略）
            scale: 提取尺度（米）
            buffer_meters: 缓冲区半径（米）
            reducer: 降维方法（对于人口，通常使用mean或sum）

        Returns:
            dict: 包含人口值和元数据的字典
        """
        # 人口数据是静态的，忽略月份
        result = super().extract_value(
            point, year, month or 1, scale, buffer_meters, reducer
        )

        # 添加人口特定的元数据
        result['data_source'] = 'WorldPop'
        result['population_unit'] = 'people/100m²'
        result['temporal_resolution'] = 'annual'
        result['spatial_resolution'] = '100m'

        # 可选：转换为每平方公里
        if 'value' in result and result['value'] is not None:
            result['population_per_km2'] = result['value'] * 100

        return result

    def extract_population_for_area(self,
                                   region: ee.Geometry,
                                   year: int = 2020) -> Dict[str, Any]:
        """
        提取区域总人口

        计算给定区域内的总人口

        Args:
            region: 研究区域几何
            year: 年份

        Returns:
            dict: 包含总人口和统计信息的字典

        示例:
            result = extractor.extract_population_for_area(city_geometry, 2020)
        """
        # 获取人口数据
        collection = self.get_collection()
        pop_image = self.get_temporal_composite(
            collection, f'{year}-01-01', f'{year}-12-31'
        )

        # 应用定标
        pop_scaled = self.apply_scale_factors(pop_image)

        # 计算区域内的总人口
        stats = pop_scaled.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=region,
            scale=100,
            maxPixels=1e9
        )

        # 获取结果
        try:
            total_pop = stats.getInfo()
            return {
                'total_population': total_pop.get('population', 0),
                'area_km2': region.area().getInfo() / 1e6,
                'year': year,
                'description': f'{year}年区域总人口'
            }
        except Exception as e:
            return {
                'error': str(e),
                'description': '人口提取失败'
            }

    def calculate_population_density(self,
                                    points_df,
                                    year: int = 2020) -> pd.DataFrame:
        """
        计算人口密度

        Args:
            points_df: 采样点GeoDataFrame
            year: 年份

        Returns:
            DataFrame: 包含人口密度信息

        注意：
            - 人口密度 = 人口数量 / 面积
            - 原始单位：人/100m²
            - 可转换为：人/km² (乘以100)
        """
        import pandas as pd

        # 创建FeatureCollection
        features = []
        for idx, row in points_df.iterrows():
            geom = row.geometry
            point = ee.Geometry.Point([geom.x, geom.y])
            feature = ee.Feature(point, {'id': idx})
            features.append(feature)

        fc = ee.FeatureCollection(features)

        # 获取人口数据
        collection = self.get_collection()
        pop_image = self.get_temporal_composite(
            collection, f'{year}-01-01', f'{year}-12-31'
        )

        # 应用定标
        pop_scaled = self.apply_scale_factors(pop_image)

        # 提取数据
        results = pop_scaled.sampleRegions(
            collection=fc,
            scale=100
        )

        # 转换为DataFrame
        data = results.getInfo()['features']

        extracted_data = []
        for item in data:
            props = item['properties']
            pop_value = props.get('population', 0)

            extracted_data.append({
                'id': props.get('id'),
                'population': pop_value,
                'population_per_100m2': pop_value,
                'population_per_km2': pop_value * 100 if pop_value else 0
            })

        df = pd.DataFrame(extracted_data)

        return df

    def compare_population_year_over_year(self,
                                       region: ee.Geometry,
                                       start_year: int,
                                       end_year: int) -> Dict[str, Any]:
        """
        比较不同年份的人口变化

        Args:
            region: 研究区域
            start_year: 起始年份
            end_year: 结束年份

        Returns:
            dict: 包含人口变化信息的字典

        注意：
            WorldPop数据可能不是每年都有
            需要根据实际可用数据调整
        """
        # 提取起始年和结束年的人口
        start_data = self.extract_population_for_area(region, start_year)
        end_data = self.extract_population_for_area(region, end_year)

        if 'error' not in start_data and 'error' not in end_data:
            start_pop = start_data['total_population']
            end_pop = end_data['total_population']

            # 计算变化
            absolute_change = end_pop - start_pop
            relative_change = (absolute_change / start_pop * 100) if start_pop > 0 else 0
            annual_change = relative_change / (end_year - start_year) if end_year > start_year else 0

            return {
                'start_year': start_year,
                'end_year': end_year,
                'start_population': start_pop,
                'end_population': end_pop,
                'absolute_change': absolute_change,
                'relative_change_percent': relative_change,
                'annual_change_percent': annual_change,
                'trend': 'increasing' if absolute_change > 0 else 'decreasing'
            }
        else:
            return {
                'error': 'Unable to compare populations',
                'start_data': start_data,
                'end_data': end_data
            }

    def __repr__(self) -> str:
        """字符串表示"""
        return "<PopulationExtractor: WorldPop @ 100m, Annual>"
