"""
智能数据集发现模块 - 自动发现GEE最新数据集
"""

import ee
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class SmartDatasetDiscoverer:
    """
    智能数据集发现器

    功能：
    1. 搜索特定类型的GEE数据集
    2. 获取数据集元数据
    3. 比较不同版本的数据集
    4. 推荐最佳数据集
    """

    # 预定义的数据集搜索模式
    DATASET_PATTERNS = {
        'LST': {
            'keywords': ['MODIS', 'LST', 'Land Surface Temperature'],
            'preferred_collections': [
                'MODIS/061/MOD11A2',  # 最新版本
                'MODIS/006/MOD11A2',
                'MODIS/061/MYD11A2',
            ]
        },
        'NDVI': {
            'keywords': ['MODIS', 'NDVI', 'Vegetation'],
            'preferred_collections': [
                'MODIS/061/MOD13Q1',
                'MODIS/061/MYD13Q1',
                'MODIS/006/MOD13Q1',
            ]
        },
        'EVI': {
            'keywords': ['MODIS', 'EVI', 'Vegetation'],
            'preferred_collections': [
                'MODIS/061/MOD13Q1',
                'MODIS/061/MYD13Q1',
            ]
        },
        'Albedo': {
            'keywords': ['MODIS', 'Albedo', 'MCD43'],
            'preferred_collections': [
                'MODIS/061/MCD43A3',
                'MODIS/006/MCD43A3',
            ]
        },
        'PM25': {
            'keywords': ['PM25', 'Particulate', 'Air Quality'],
            'preferred_collections': [
                'MODIS/006/MCD19A2_GRANULES',
            ]
        }
    }

    def __init__(self):
        """初始化发现器"""
        try:
            ee.Initialize()
            self.ee = ee
            self.available = True
            print("✅ GEE已初始化")
        except Exception as e:
            print(f"⚠️  GEE初始化失败: {e}")
            self.available = False

        self.discovered_datasets = {}

    def discover_datasets(self, data_type: str) -> Dict[str, Any]:
        """
        发现指定类型的数据集

        参数:
        -------
        data_type : str
            数据类型 (LST, NDVI, EVI, Albedo, PM25)

        返回:
        -------
        dict
            发现的数据集信息
        """
        if not self.available:
            return {'error': 'GEE不可用'}

        if data_type not in self.DATASET_PATTERNS:
            return {'error': f'不支持的数据类型: {data_type}'}

        print(f"\n🔍 正在搜索 {data_type} 数据集...")

        pattern = self.DATASET_PATTERNS[data_type]
        results = []

        # 尝试预定义的集合
        for collection_id in pattern['preferred_collections']:
            try:
                info = self._get_collection_info(collection_id)
                if info:
                    results.append(info)
                    print(f"  ✅ 找到: {collection_id}")
            except Exception as e:
                print(f"  ⚠️  无法访问 {collection_id}: {e}")
                continue

        # 选择最佳数据集
        best_dataset = self._select_best_dataset(results)

        self.discovered_datasets[data_type] = {
            'all_candidates': results,
            'recommended': best_dataset,
            'search_time': datetime.now().isoformat()
        }

        return self.discovered_datasets[data_type]

    def _get_collection_info(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """
        获取集合的详细信息

        参数:
        -------
        collection_id : str
            GEE集合ID

        返回:
        -------
        dict or None
            集合信息
        """
        try:
            collection = ee.ImageCollection(collection_id)

            # 获取集合信息
            info = collection.getInfo()

            # 获取时间范围
            first_image = collection.first()
            if first_image:
                try:
                    first_info = first_image.getInfo()
                    properties = first_info.get('properties', {})

                    # 尝试获取时间信息
                    start_time = properties.get('system:time_start')
                    if start_time:
                        start_date = datetime.fromtimestamp(start_time / 1000)
                    else:
                        start_date = None
                except:
                    start_date = None
            else:
                start_date = None

            # 获取波段信息
            bands = []
            try:
                band_info = collection.first().bandNames().getInfo()
                bands = band_info if band_info else []
            except:
                pass

            return {
                'collection_id': collection_id,
                'version': collection_id.split('/')[1],  # 提取版本号
                'start_date': start_date.isoformat() if start_date else '未知',
                'bands': bands,
                'accessible': True
            }

        except Exception as e:
            return None

    def _select_best_dataset(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        从候选数据集中选择最佳的

        选择标准：
        1. 最高版本号
        2. 可访问性
        3. 数据完整性

        参数:
        -------
        candidates : list
            候选数据集列表

        返回:
        -------
        dict
            推荐的数据集
        """
        if not candidates:
            return None

        # 按版本号排序（优先选择061版本，然后006等）
        def version_key(candidate):
            version = candidate.get('version', '000')
            # 061版本优先
            if version == '061':
                return 2
            elif version == '006':
                return 1
            else:
                return 0

        sorted_candidates = sorted(candidates, key=version_key, reverse=True)

        return sorted_candidates[0]

    def get_dataset_metadata(self, collection_id: str) -> Dict[str, Any]:
        """
        获取数据集的完整元数据

        参数:
        -------
        collection_id : str
            集合ID

        返回:
        -------
        dict
            元数据
        """
        try:
            collection = ee.ImageCollection(collection_id)

            # 获取波段信息
            first = collection.first()
            band_names = first.bandNames().getInfo()
            band_types = {}

            for band in band_names:
                try:
                    band_info = first.select(band).getInfo()
                    band_types[band] = band_info.get('bands', [{}])[0].get('data_type', {})
                except:
                    band_types[band] = {'type': 'unknown'}

            # 获取时间范围
            try:
                dates = collection.aggregate_array('system:time_start').getInfo()
                if dates:
                    dates_sorted = sorted([d / 1000 for d in dates])
                    time_range = {
                        'start': datetime.fromtimestamp(dates_sorted[0]).isoformat(),
                        'end': datetime.fromtimestamp(dates_sorted[-1]).isoformat()
                    }
                else:
                    time_range = None
            except:
                time_range = None

            return {
                'collection_id': collection_id,
                'bands': band_names,
                'band_types': band_types,
                'time_range': time_range,
                'properties': collection.first().toDictionary().getInfo()
            }

        except Exception as e:
            return {'error': str(e)}

    def compare_datasets(self, dataset1: str, dataset2: str) -> Dict[str, Any]:
        """
        比较两个数据集

        参数:
        -------
        dataset1, dataset2 : str
            要比较的集合ID

        返回:
        -------
        dict
            比较结果
        """
        info1 = self.get_dataset_metadata(dataset1)
        info2 = self.get_dataset_metadata(dataset2)

        return {
            'dataset1': info1,
            'dataset2': info2,
            'differences': {
                'version_newer': dataset1 if info1.get('version', '') > info2.get('version', '') else dataset2,
                'more_bands': dataset1 if len(info1.get('bands', [])) > len(info2.get('bands', [])) else dataset2,
            }
        }

    def recommend_dataset(self, data_type: str) -> Dict[str, Any]:
        """
        为特定数据类型推荐最佳数据集

        参数:
        -------
        data_type : str
            数据类型

        返回:
        -------
        dict
            推荐结果
        """
        discovery_result = self.discover_datasets(data_type)

        if 'error' in discovery_result:
            return discovery_result

        recommended = discovery_result.get('recommended')

        if not recommended:
            return {'error': '未找到合适的数据集'}

        # 获取完整元数据
        metadata = self.get_dataset_metadata(recommended['collection_id'])

        return {
            'data_type': data_type,
            'recommended_collection': recommended['collection_id'],
            'version': recommended['version'],
            'bands': metadata.get('bands', []),
            'time_range': metadata.get('time_range'),
            'reason': f"推荐使用版本{recommended['version']}，这是最新的稳定版本"
        }

    def discover_all_datasets(self) -> Dict[str, Dict[str, Any]]:
        """
        发现所有支持的数据类型的最佳数据集

        返回:
        -------
        dict
            所有数据类型的推荐
        """
        all_recommendations = {}

        for data_type in self.DATASET_PATTERNS.keys():
            print(f"\n{'='*60}")
            print(f"发现 {data_type} 数据集...")
            print(f"{'='*60}")

            recommendation = self.recommend_dataset(data_type)
            all_recommendations[data_type] = recommendation

        return all_recommendations

    def generate_config_update(self, current_config: Dict) -> Dict[str, Any]:
        """
        生成配置更新建议

        参数:
        -------
        current_config : dict
            当前配置

        返回:
        -------
        dict
            更新建议
        """
        recommendations = self.discover_all_datasets()

        updates = {
            'timestamp': datetime.now().isoformat(),
            'updates': [],
            'unchanged': []
        }

        for data_type, recommendation in recommendations.items():
            if 'error' in recommendation:
                continue

            current_collection = current_config.get(data_type, {}).get('collection', '')
            recommended_collection = recommendation['recommended_collection']

            if current_collection != recommended_collection:
                updates['updates'].append({
                    'data_type': data_type,
                    'old_collection': current_collection,
                    'new_collection': recommended_collection,
                    'reason': recommendation['reason'],
                    'version': recommendation['version']
                })
            else:
                updates['unchanged'].append(data_type)

        return updates


class DatasetVersionTracker:
    """
    数据集版本跟踪器

    跟踪数据集的版本变化历史
    """

    def __init__(self, tracker_file: str = 'dataset_versions.json'):
        """
        初始化

        参数:
        -------
        tracker_file : str
            跟踪文件路径
        """
        self.tracker_file = tracker_file
        self.history = self._load_history()

    def _load_history(self) -> Dict[str, Any]:
        """加载历史记录"""
        try:
            with open(self.tracker_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_history(self):
        """保存历史记录"""
        with open(self.tracker_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def record_version(self, data_type: str, collection_id: str, metadata: Dict = None):
        """
        记录数据集版本

        参数:
        -------
        data_type : str
            数据类型
        collection_id : str
            集合ID
        metadata : dict, optional
            额外的元数据
        """
        if data_type not in self.history:
            self.history[data_type] = []

        self.history[data_type].append({
            'collection_id': collection_id,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })

        self._save_history()

    def get_version_history(self, data_type: str) -> List[Dict[str, Any]]:
        """
        获取数据集的版本历史

        参数:
        -------
        data_type : str
            数据类型

        返回:
        -------
        list
            版本历史
        """
        return self.history.get(data_type, [])


# 使用示例
if __name__ == '__main__':
    discoverer = SmartDatasetDiscoverer()

    # 发现所有数据集
    all_datasets = discoverer.discover_all_datasets()

    print("\n" + "="*60)
    print("数据集发现结果")
    print("="*60)

    for data_type, info in all_datasets.items():
        if 'error' not in info:
            print(f"\n{data_type}:")
            print(f"  推荐集合: {info['recommended_collection']}")
            print(f"  版本: {info['version']}")
            print(f"  原因: {info['reason']}")
