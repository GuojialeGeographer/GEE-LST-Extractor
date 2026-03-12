"""
GEE辅助函数 - 处理GEE任务的派发、监控和下载
"""

import ee
import time
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path


class GEEHelper:
    """
    GEE辅助工具类

    负责：
    1. 创建GEE FeatureCollection
    2. 派发导出任务
    3. 监控任务状态
    4. 下载结果
    """

    @staticmethod
    def create_feature_collection(points_df: pd.DataFrame,
                                  lng_col: str = 'lng',
                                  lat_col: str = 'lat',
                                  properties: Dict[str, Any] = None) -> ee.FeatureCollection:
        """
        从DataFrame创建GEE FeatureCollection

        Args:
            points_df: 包含坐标点的DataFrame
            lng_col: 经度列名
            lat_col: 纬度列名
            properties: 额外的属性字典

        Returns:
            ee.FeatureCollection

        示例：
            df = pd.DataFrame({
                'lng': [116.407, 116.408],
                'lat': [39.904, 39.905],
                'grid_uid': ['abc', 'def']
            })

            fc = GEEHelper.create_feature_collection(
                df,
                properties={'grid_uid': 'grid_uid'}
            )
        """
        features = []

        for _, row in points_df.iterrows():
            # 创建点几何
            point = ee.Geometry.Point([row[lng_col], row[lat_col]])

            # 创建属性字典
            props = {}
            if properties:
                for key, source_col in properties.items():
                    if source_col in points_df.columns:
                        props[key] = row[source_col]

            # 创建Feature
            feature = ee.Feature(point, props)
            features.append(feature)

        return ee.FeatureCollection(features)

    @staticmethod
    def export_to_drive(collection: ee.FeatureCollection,
                       description: str,
                       file_name: str,
                       folder: str = 'GEE_Results') -> ee.batch.Export:
        """
        派发导出任务到Google Drive

        Args:
            collection: 要导出的FeatureCollection
            description: 任务描述
            file_name: 输出文件名
            folder: Google Drive文件夹

        Returns:
            ee.batch.Export.task

        示例：
            task = GEEHelper.export_to_drive(
                fc,
                description='LST_2023_01',
                file_name='lst_2023_01.csv'
            )
            task.start()
        """
        task = ee.batch.Export.table.toDrive(
            collection=collection,
            description=description,
            fileName=file_name,
            folder=folder,
            fileFormat='CSV'
        )

        return task

    @staticmethod
    def monitor_task(task: ee.batch.Export,
                    check_interval: int = 10,
                    timeout: int = 3600,
                    verbose: bool = True) -> bool:
        """
        监控任务状态直到完成

        Args:
            task: GEE任务
            check_interval: 检查间隔（秒）
            timeout: 超时时间（秒）
            verbose: 是否打印进度

        Returns:
            bool: 成功返回True，失败返回False

        示例：
            success = GEEHelper.monitor_task(task)
            if success:
                print("任务完成")
            else:
                print("任务失败")
        """
        start_time = time.time()

        while task.active():
            elapsed = time.time() - start_time

            if elapsed > timeout:
                if verbose:
                    print(f"任务超时（{timeout}秒）")
                return False

            if verbose and int(elapsed) % 60 == 0:
                print(f"  任务运行中... 已用时{int(elapsed)}秒")

            time.sleep(check_interval)

        # 检查任务状态
        status = task.status()
        if verbose:
            print(f"  任务状态：{status['state']}")

        return status['state'] == 'COMPLETED'

    @staticmethod
    def extract_values_for_collection(extractor,
                                     points_df: pd.DataFrame,
                                     year: int,
                                     month: int) -> ee.FeatureCollection:
        """
        为FeatureCollection中的每个点提取值

        Args:
            extractor: 提取器实例
            points_df: 点数据
            year: 年份
            month: 月份

        Returns:
            ee.FeatureCollection: 包含提取值的FeatureCollection

        示例：
            fc = GEEHelper.extract_values_for_collection(
                lst_extractor,
                points_df,
                2023, 1
            )
        """
        band_name = extractor.get_band_name()

        def extract_for_point(feature):
            """为单个点提取值"""
            geom = feature.geometry()
            coords = geom.coordinates().getInfo()
            point = ee.Geometry.Point(coords)

            # 提取值
            result = extractor.extract_value(point, year, month)

            # 创建新的Feature，包含原属性和提取的值
            props = feature.toDictionary()
            props = props.set(band_name, result['value'])

            return ee.Feature(geom, props)

        # 映射到所有点
        fc_with_values = points_df_fc.map(extract_for_point)

        return fc_with_values

    @staticmethod
    def batch_extract(extractor,
                    points_df: pd.DataFrame,
                    year: int,
                    month: int,
                    city: str = None,
                    batch_size: int = 5000) -> pd.DataFrame:
        """
        批量提取（简化版，用于小数据集）

        对于小数据集（<5000点），可以直接在内存中提取
        不需要派发GEE任务

        Args:
            extractor: 提取器实例
            points_df: 点数据
            year: 年份
            month: 月份
            city: 城市名
            batch_size: 批次大小

        Returns:
            pd.DataFrame: 包含提取值的DataFrame
        """
        result_df = points_df.copy()
        band_name = extractor.get_band_name()
        result_df[band_name] = None

        # 分批处理
        for i in range(0, len(points_df), batch_size):
            batch = points_df.iloc[i:i+batch_size]

            print(f"  处理批次 {i//batch_size + 1}/{(len(points_df)-1)//batch_size + 1}")

            # 为当前批次提取值
            for _, row in batch.iterrows():
                point = ee.Geometry.Point([row['lng'], row['lat']])

                try:
                    result = extractor.extract_value(point, year, month)
                    value = result['value'].getInfo()

                    # 找到对应行并设置值
                    idx = result_df[result_df['grid_uid'] == row['grid_uid']].index
                    if len(idx) > 0:
                        result_df.loc[idx[0], band_name] = value

                except Exception as e:
                    print(f"    警告：点{row['grid_uid']}提取失败：{e}")
                    continue

        return result_df

    @staticmethod
    def list_drive_tasks() -> List[Dict[str, Any]]:
        """
        列出当前所有GEE任务

        Returns:
            List[Dict]: 任务信息列表

        示例：
            tasks = GEEHelper.list_drive_tasks()
            for task in tasks:
                print(f"{task['id']}: {task['state']}")
        """
        task_list = ee.batch.Export.list()

        tasks = []
        for task_info in task_list:
            tasks.append({
                'id': task_info['id'],
                'state': task_info['state'],
                'description': task_info['description'],
                'creation_time': task_info['creation_timestamp_ms']
            })

        return tasks


class GEETaskManager:
    """
    GEE任务管理器

    管理多个GEE导出任务的生命周期
    """

    def __init__(self):
        """初始化任务管理器"""
        self.tasks = {}

    def add_task(self,
                 task_id: str,
                 task: ee.batch.Export,
                 metadata: Dict[str, Any] = None):
        """
        添加任务到管理器

        Args:
            task_id: 任务ID
            task: GEE任务
            metadata: 元数据（年份、月份、数据源等）
        """
        self.tasks[task_id] = {
            'task': task,
            'metadata': metadata or {},
            'status': 'PENDING'
        }

    def start_task(self, task_id: str):
        """启动任务"""
        if task_id in self.tasks:
            self.tasks[task_id]['task'].start()
            self.tasks[task_id]['status'] = 'RUNNING'

    def monitor_all(self,
                   check_interval: int = 10,
                   timeout: int = 3600) -> Dict[str, bool]:
        """
        监控所有任务

        Args:
            check_interval: 检查间隔
            timeout: 超时时间

        Returns:
            Dict[str, bool]: {task_id: success}
        """
        results = {}

        for task_id, task_info in self.tasks.items():
            print(f"\n监控任务：{task_id}")
            success = GEEHelper.monitor_task(
                task_info['task'],
                check_interval=check_interval,
                timeout=timeout
            )
            results[task_id] = success

            # 更新状态
            self.tasks[task_id]['status'] = 'COMPLETED' if success else 'FAILED'

        return results

    def get_status(self, task_id: str) -> str:
        """获取任务状态"""
        if task_id in self.tasks:
            return self.tasks[task_id]['status']
        return 'UNKNOWN'

    def get_metadata(self, task_id: str) -> Dict[str, Any]:
        """获取任务元数据"""
        if task_id in self.tasks:
            return self.tasks[task_id]['metadata']
        return {}
