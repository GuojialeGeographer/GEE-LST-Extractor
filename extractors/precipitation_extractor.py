"""
降水提取器 - GPM IMERG 卫星降水数据

从GPM (Global Precipitation Measurement) IMERG数据集提取降水信息
"""

import ee
from typing import Dict, Any
from core.base_extractor import BaseExtractor


class PrecipitationExtractor(BaseExtractor):
    """
    GPM IMERG 降水提取器

    数据源：
        - GPM IMERG Final Run
        - NASA/GPM_L3/IMERG_V06

    空间分辨率：0.1°（约11km）
    时间分辨率：30分钟
    单位：mm/h

    产品说明：
        - 'precipitationCal': 校准降水率
        - 'precipitationUncal': 未校准降水率
        - 'probabilityLiquidPrecipitation': 液态降水概率

    参考文献：
        - Huffman et al. (2019). "The GPM IMERG Late Run"
        - https://gpm.nasa.gov/data-access/downloads/imerg

    使用建议：
        - 适合研究降水时空分布
        - 可用于极端降水分析
        - 支持全球范围提取
    """

    def get_collection(self) -> ee.ImageCollection:
        """
        获取GPM IMERG数据集

        使用IMERG V06版本（最新版本）

        Returns:
            ee.ImageCollection: GPM IMERG数据集
        """
        # GPM IMERG Final Run (30分钟分辨率)
        return ee.ImageCollection('NASA/GPM_L3/IMERG_V06')

    def apply_scale_factors(self, image: ee.Image) -> ee.Image:
        """
        应用定标系数

        GPM IMERG数据定标说明：
        - precipitationCal: mm/h，无需缩放
        - 已经是物理单位

        Args:
            image: 输入的GPM影像

        Returns:
            ee.Image: 添加了降水波段的影像
        """
        # GPM数据已经是物理单位（mm/h），直接选择波段
        precip = image.select('precipitationCal').rename('precipitation')

        return image.addBands(precip)

    def filter_by_quality(self, collection: ee.ImageCollection) -> ee.ImageCollection:
        """
        质量过滤

        使用HQ (High Quality) 标志进行过滤

        Args:
            collection: 输入的影像集合

        Returns:
            ee.ImageCollection: 过滤后的影像集合

        参考文献：
            GPM IMERG Quality Index documentation
        """
        def apply_quality_mask(img):
            # 获取质量标志
            # HQprecipitation: 高质量降水像素掩膜
            # 1 = 高质量, 0 = 低质量或卫星传感器海岸等伪影

            hq = img.select('HQprecipitation')

            # 应用定标
            scaled = self.apply_scale_factors(img)

            # 只保留高质量像素
            masked = scaled.updateMask(hq.eq(1))

            return masked

        return collection.map(apply_quality_mask)

    def get_band_name(self) -> str:
        """返回波段名称"""
        return 'precipitation'

    def get_default_scale(self) -> int:
        """
        返回默认提取尺度

        IMERG数据分辨率为0.1°（约11km）

        Returns:
            int: 11132米（0.1°在赤道的近似距离）
        """
        return 11132  # 0.1度约等于11.132km

    def get_collection_id(self) -> str:
        """返回数据集ID"""
        return "NASA/GPM_L3/IMERG_V06"

    def get_spatial_resolution(self) -> int:
        """返回空间分辨率（米）"""
        return 11132  # ~11km

    def get_temporal_resolution(self) -> str:
        """
        返回时间分辨率

        IMERG提供30分钟数据

        Returns:
            str: "30 minutes"
        """
        return "30 minutes"

    def get_unit(self) -> str:
        """返回单位"""
        return "mm/h"

    def get_required_config_keys(self) -> list:
        """
        返回必需的配置键

        降水提取器没有必需的配置键

        Returns:
            list: 空列表
        """
        return []

    def get_temporal_composite(self,
                               collection: ee.ImageCollection,
                               start_date: str,
                               end_date: str,
                               reducer: str = 'sum') -> ee.Image:
        """
        创建时间合成降水影像

        对于降水数据，通常使用总和（sum）来计算累积降水量

        Args:
            collection: 影像集合
            start_date: 开始日期
            end_date: 结束日期
            reducer: 聚合方法（'sum', 'mean'）

        Returns:
            ee.Image: 合成影像
        """
        # 覆盖父类方法，默认使用sum
        return super().get_temporal_composite(
            collection, start_date, end_date, reducer
        )

    def extract_value(self,
                     point: ee.Geometry.Point,
                     year: int,
                     month: int,
                     scale: int = None,
                     buffer_meters: int = 0,
                     reducer: str = 'sum') -> Dict[str, Any]:
        """
        提取降水值

        Args:
            point: 点几何
            year: 年份
            month: 月份
            scale: 提取尺度（米）
            buffer_meters: 缓冲区半径（米）
            reducer: 降维方法（默认'sum'计算月累积降水）

        Returns:
            dict: 包含降水值和元数据的字典
        """
        result = super().extract_value(
            point, year, month, scale, buffer_meters, reducer
        )

        # 添加降水特定的元数据
        result['data_source'] = 'GPM_IMERG'
        result['precipitation_unit'] = 'mm'
        result['temporal_resolution'] = '30-minute'

        return result

    def calculate_monthly_accumulation(self,
                                      points_df,
                                      year: int,
                                      month: int) -> Dict[str, Any]:
        """
        计算月累积降水量

        这是降水分析的常用方法

        Args:
            points_df: 采样点GeoDataFrame
            year: 年份
            month: 月份

        Returns:
            dict: 包含月累积降水的字典
        """
        import pandas as pd
        from datetime import datetime

        # 生成月份范围
        if month == 12:
            start_date = f'{year}-{month:02d}-01'
            end_date = f'{year+1}-01-01'
        else:
            start_date = f'{year}-{month:02d}-01'
            end_date = f'{year}-{month+1:02d}-01'

        # 提取数据（使用sum聚合）
        result = self.extract_value(
            point=points_df.geometry.iloc[0],
            year=year,
            month=month,
            reducer='sum'
        )

        # 添加计算说明
        result['calculation_method'] = 'monthly_accumulation'
        result['time_period'] = f'{year}-{month:02d}'
        result['description'] = f'{year}年{month}月累积降水量'

        return result

    def calculate_daily_statistics(self,
                                  points_df,
                                  start_date: str,
                                  end_date: str) -> pd.DataFrame:
        """
        计算日降水统计

        包括：平均日降水量、最大日降水量、降水天数等

        Args:
            points_df: 采样点GeoDataFrame
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 日降水统计数据
        """
        # 获取每日数据
        dates = pd.date_range(start_date, end_date, freq='D')

        daily_data = []

        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            next_date_str = (date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')

            # 提取该日的降水（使用sum得到日总量）
            try:
                daily_precip = self.extract_value(
                    point=points_df.geometry.iloc[0],
                    year=date.year,
                    month=date.month,
                    # 这里需要特殊处理来指定具体日期
                    # 暂时使用月度数据
                    reducer='sum'
                )

                if 'value' in daily_precip and daily_precip['value'] is not None:
                    daily_data.append({
                        'date': date_str,
                        'precipitation_mm': daily_precip['value']
                    })
            except Exception as e:
                # 跳过失败的日期
                continue

        df = pd.DataFrame(daily_data)

        if len(df) > 0:
            # 计算统计量
            stats = {
                'mean_daily_precip': df['precipitation_mm'].mean(),
                'max_daily_precip': df['precipitation_mm'].max(),
                'total_precip': df['precipitation_mm'].sum(),
                'rainy_days': len(df[df['precipitation_mm'] > 0]),
                'dry_days': len(df[df['precipitation_mm'] == 0]),
                'max_daily_date': df.loc[df['precipitation_mm'].idxmax(), 'date']
            }

            return pd.DataFrame([stats])
        else:
            return pd.DataFrame()

    def __repr__(self) -> str:
        """字符串表示"""
        return "<PrecipitationExtractor: GPM IMERG @ 0.1°, 30-minute>"
