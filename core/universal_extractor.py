"""
通用环境数据提取器 - 主入口

这是用户主要使用的类，整合所有核心组件，提供统一的API
"""

import pandas as pd
import ee
from typing import Dict, Any, Optional, List
from importlib import import_module

from core.config_manager import ConfigManager
from core.grid_manager import GridManager
from core.batch_manager import BatchManager
from core.quality_tracker import QualityTracker
from core.base_extractor import BaseExtractor
from core.gee_helper import GEEHelper
import numpy as np


class UniversalExtractor:
    """
    通用环境数据提取器（主入口）

    这是框架的主要接口，负责：
    1. 加载和管理配置
    2. 动态加载数据源提取器
    3. 协调提取流程
    4. 合并多数据源结果
    5. 提供简洁的用户API

    使用示例：
        # 初始化（从配置文件）
        extractor = UniversalExtractor(config_path='config/data_sources.yaml')

        # 或（从配置字典）
        config = {'data_sources': {...}}
        extractor = UniversalExtractor(config_dict=config)

        # 提取数据（一行代码）
        results = extractor.extract(
            points_df=social_media_df,
            year=2023,
            month=1,
            city='Beijing'
        )

        # 结果包含所有启用的数据源列
        # social_media_df + LST + NDVI + ...
    """

    def __init__(self,
                 config_path: Optional[str] = None,
                 config_dict: Optional[Dict[str, Any]] = None):
        """
        初始化通用提取器

        Args:
            config_path: 配置文件路径（YAML）
            config_dict: 配置字典（与config_path二选一）

        Raises:
            ValueError: 如果既没提供config_path也没提供config_dict
            Exception: 如果GEE初始化失败

        示例：
            # 从文件加载
            extractor = UniversalExtractor(config_path='config/data_sources.yaml')

            # 从字典加载
            config = {'data_sources': {'LST': {...}}}
            extractor = UniversalExtractor(config_dict=config)
        """
        # 加载配置
        self.config_manager = ConfigManager(
            config_path=config_path,
            config_dict=config_dict
        )

        # 验证配置
        self.config_manager.validate()

        # 初始化GEE
        self._init_gee()

        # 初始化核心组件
        self.grid_manager = GridManager()
        self.batch_manager = BatchManager(
            points_per_task=self.config_manager.get_global_config()
                         ['batch']['points_per_task'],
            delay_between_tasks=self.config_manager.get_global_config()
                                ['batch']['delay_between_tasks']
        )
        self.quality_tracker = QualityTracker(
            self.config_manager.to_dict()
        )

        # 加载数据源提取器
        self.extractors = self._load_extractors()

    def _init_gee(self):
        """初始化Google Earth Engine"""
        try:
            ee.Initialize()
            print("✓ GEE初始化成功")
        except Exception as e:
            print(f"✗ GEE初始化失败: {e}")
            print("请先运行:")
            print("  import ee")
            print("  ee.Authenticate()")
            raise

    def _load_extractors(self) -> Dict[str, BaseExtractor]:
        """
        动态加载启用的数据源提取器

        Returns:
            dict: {数据源名: 提取器实例}

        Raises:
            ImportError: 如果提取器类无法导入
            Exception: 如果提取器初始化失败
        """
        extractors = {}
        enabled_sources = self.config_manager.get_enabled_data_sources()

        print(f"\n加载提取器...")

        for name in enabled_sources:
            try:
                # 获取配置
                config = self.config_manager.get_data_source_config(name)

                # 动态导入提取器类
                module_path, class_name = config['extractor'].rsplit('.', 1)
                module = import_module(f'extractors.{module_path}')
                extractor_class = getattr(module, class_name)

                # 创建实例
                parameters = config.get('parameters', {})
                extractor = extractor_class(parameters)

                extractors[name] = extractor

                # 显示信息
                info = extractor.get_info()
                print(f"  ✓ {name}: {info['collection_id']} @ {info['spatial_resolution']}m")

            except Exception as e:
                print(f"  ✗ {name}: 加载失败 - {e}")
                raise

        print(f"\n已加载 {len(extractors)} 个数据源提取器")

        return extractors

    def extract(self,
               points_df: pd.DataFrame,
               year: int,
               month: int,
               city: Optional[str] = None,
               progress_callback: Optional[callable] = None) -> pd.DataFrame:
        """
        提取所有启用的数据源

        这是主要的使用方法，一行代码完成多数据源提取

        Args:
            points_df: 点数据（必须包含lng, lat列）
            year: 年份
            month: 月份
            city: 城市名（可选，用于grid_uid生成）
            progress_callback: 进度回调函数 callback(current, total, source_name)

        Returns:
            pd.DataFrame: 包含所有数据源列的DataFrame

        返回的DataFrame包含：
        - 所有原始列
        - 每个数据源的值列
        - 每个数据源的质量标记列（如果启用）

        示例：
            # 社交媒体数据
            df = pd.DataFrame({
                'user_id': [1, 2, 3],
                'lng': [116.407, 116.408, 116.409],
                'lat': [39.904, 39.905, 39.906]
            })

            # 提取环境数据
            extractor = UniversalExtractor('config/data_sources.yaml')
            results = extractor.extract(df, 2023, 1, 'Beijing')

            # 结果：
            #   user_id  lng    lat    LST    NDVI    LST_quality_flag
            # 0  1        116.4  39.9   25.3   0.65    direct
            # 1  2        116.4  39.9   25.4   0.67    direct
            # 2  3        116.4  39.9   25.2   0.63    direct
        """
        print(f"\n{'='*60}")
        print(f"开始提取：{year}年{month}月")
        if city:
            print(f"城市：{city}")
        print(f"点数：{len(points_df):,}")
        print(f"数据源：{', '.join(self.extractors.keys())}")
        print(f"{'='*60}\n")

        # 创建时空网格
        print("步骤1：创建时空网格...")
        gridded_df = self.grid_manager.create_grids(
            points_df,
            year=year,
            month=month,
            city=city
        )

        # 获取唯一网格
        unique_grids = self.grid_manager.get_unique_grids(gridded_df)
        print(f"唯一网格数：{len(unique_grids):,}\n")

        # 初始化结果DataFrame
        results = gridded_df.copy()

        # 对每个数据源进行提取
        for i, (name, extractor) in enumerate(self.extractors.items()):
            if progress_callback:
                progress_callback(i, len(self.extractors), name)

            print(f"\n步骤2.{i+1}：提取 {name}...")

            # 提取数据
            extracted = self._extract_single_source(
                extractor=extractor,
                points_df=unique_grids,
                year=year,
                month=month,
                city=city
            )

            # 获取输出列名
            col_name = self.config_manager.get_data_source_config(name)['output']['column_name']

            # 合并结果到唯一网格
            unique_grids[col_name] = extracted[col_name]

            # 添加质量标记（如果启用）
            if self.config_manager.get_output_config().get('include_quality_flags', True):
                unique_grids[f'{col_name}_quality_flag'] = extracted.get(f'{col_name}_quality_flag', 'direct')
                unique_grids[f'{col_name}_extraction_method'] = extracted.get(f'{col_name}_extraction_method', 'exact')

            print(f"  ✓ {name} 提取完成")

        # 步骤3：将网格结果合并回所有原始点
        print(f"\n步骤3：合并结果...")
        merge_cols = []
        for name in self.extractors.keys():
            col_name = self.config_manager.get_data_source_config(name)['output']['column_name']
            merge_cols.append(col_name)
            if self.config_manager.get_output_config().get('include_quality_flags', True):
                merge_cols.extend([
                    f'{col_name}_quality_flag',
                    f'{col_name}_extraction_method'
                ])

        # 通过grid_uid合并
        results = self.grid_manager.merge_results(
            original_df=results,
            grid_results=unique_grids,
            merge_cols=merge_cols
        )

        # 生成质量报告
        print(f"\n步骤4：生成质量报告...")
        for name in self.extractors.keys():
            col_name = self.config_manager.get_data_source_config(name)['output']['column_name']
            report = self.quality_tracker.generate_report(results, col_name)

            print(f"\n{name}:")
            print(f"  覆盖率：{report['coverage']:.1f}%")
            print(f"  有效值：{report['valid_points']:,} / {report['total_points']:,}")

        print(f"\n{'='*60}")
        print(f"提取完成！")
        print(f"{'='*60}\n")

        return results

    def _extract_single_source(self,
                              extractor: BaseExtractor,
                              points_df: pd.DataFrame,
                              year: int,
                              month: int,
                              city: Optional[str] = None) -> pd.DataFrame:
        """
        提取单个数据源（真正的GEE集成）

        包括：
        1. 使用GEEHelper进行批量提取
        2. 质量标记
        3. 填充策略

        Args:
            extractor: 提取器实例
            points_df: 点数据（唯一网格）
            year: 年份
            month: 月份
            city: 城市名

        Returns:
            pd.DataFrame: 提取结果
        """
        print(f"  正在提取{extractor.get_band_name()}...")

        # 使用GEEHelper进行真正的数据提取
        result_df = GEEHelper.batch_extract(
            extractor=extractor,
            points_df=points_df,
            year=year,
            month=month,
            batch_size=100  # 每批100个点，避免超时
        )

        col_name = extractor.get_band_name()

        # 添加质量标记
        if self.config_manager.get_output_config().get('include_quality_flags', True):
            result_df = self.quality_tracker.add_quality_flags(result_df, col_name)

        # 应用填充策略（如果启用）
        if self.config_manager.get_quality_config().get('apply_filling_strategies', True):
            result_df = self.quality_tracker.apply_filling_strategies(
                data=result_df,
                extractor=extractor,
                year=year,
                month=month,
                city=city
            )

        return result_df

    def get_extractor(self, source_name: str) -> BaseExtractor:
        """
        获取特定数据源的提取器

        Args:
            source_name: 数据源名称

        Returns:
            BaseExtractor: 提取器实例

        示例：
            lst_extractor = extractor.get_extractor('LST')
            info = lst_extractor.get_info()
        """
        if source_name not in self.extractors:
            raise KeyError(f"数据源'{source_name}'未加载")
        return self.extractors[source_name]

    def list_data_sources(self) -> List[str]:
        """
        列出所有已加载的数据源

        Returns:
            list: 数据源名称列表

        示例：
            sources = extractor.list_data_sources()
            # ['LST', 'NDVI', 'PM25']
        """
        return list(self.extractors.keys())

    def get_config(self) -> ConfigManager:
        """
        获取配置管理器

        Returns:
            ConfigManager: 配置管理器实例
        """
        return self.config_manager

    def __repr__(self) -> str:
        """字符串表示"""
        return (f"<UniversalExtractor: {len(self.extractors)}个数据源 "
                f"({', '.join(self.extractors.keys())})>")
