"""
智能GEE数据发现器

自动发现和更新GEE上最新的数据集
"""

import ee
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime
import re


class GEEDataDiscoverer:
    """
    GEE数据智能发现器

    功能：
    1. 搜索可用的数据集
    2. 自动识别数据集版本
    3. 检测最新数据
    4. 推荐最佳数据源
    5. 自动更新配置
    """

    # 已知的数据集模式
    DATASET_PATTERNS = {
        'MODIS': {
            'pattern': r'MODIS/(\\d+)/([\\w_]+)',
            'base_collections': [
                'MODIS/061/MOD11A2',  # LST
                'MODIS/061/MOD13Q1',  # NDVI/EVI
                'MODIS/061/MCD43A3',  # Albedo
            ]
        },
        'Landsat': {
            'pattern': r'LANDSAT/(\\w+)/(\\d+)/([\\w_]+)',
            'base_collections': [
                'LANDSAT/LC08/C02/T1_L2',  # Landsat 8
                'LANDSAT/LC09/C02/T1_L2',  # Landsat 9
            ]
        },
        'Sentinel': {
            'pattern': r'COPERNICUS/(\\w+)/([\\w_]+)',
            'base_collections': [
                'COPERNICUS/S2_SR_HARMONIZED',
            ]
        }
    }

    def __init__(self):
        """初始化发现器"""
        try:
            ee.Initialize()
            self.gee_available = True
            print("✅ GEE已连接")
        except Exception as e:
            self.gee_available = False
            print(f"⚠️  GEE连接失败: {e}")

    def discover_latest_datasets(self,
                                 keywords: List[str] = None) -> pd.DataFrame:
        """
        发现最新的数据集

        Args:
            keywords: 搜索关键词（如['LST', 'NDVI', 'temperature']）

        Returns:
            DataFrame: 包含数据集信息的表格
        """
        if not self.gee_available:
            raise RuntimeError("GEE不可用")

        if keywords is None:
            keywords = ['MODIS', 'Landsat', 'Sentinel', 'temperature', 'vegetation']

        print(f"🔍 搜索关键词: {', '.join(keywords)}")

        # 搜索数据集
        discovered = []

        # 检查已知的数据集模式
        for category, info in self.DATASET_PATTERNS.items():
            for collection_id in info['base_collections']:
                try:
                    collection = ee.ImageCollection(collection_id)

                    # 获取数据集信息
                    info_dict = self._get_collection_info(collection_id)

                    if info_dict:
                        discovered.append(info_dict)
                        print(f"✅ 发现: {collection_id}")

                except Exception as e:
                    # 数据集可能不存在或无法访问
                    print(f"⚠️  无法访问: {collection_id}")
                    continue

        # 转换为DataFrame
        if discovered:
            df = pd.DataFrame(discovered)

            # 按更新时间排序
            if 'last_update' in df.columns:
                df = df.sort_values('last_update', ascending=False)

            return df
        else:
            return pd.DataFrame()

    def _get_collection_info(self,
                           collection_id: str) -> Dict[str, Any]:
        """
        获取数据集信息

        Args:
            collection_id: 数据集ID

        Returns:
            dict: 数据集信息
        """
        try:
            collection = ee.ImageCollection(collection_id)

            # 获取第一幅影像以获取元数据
            first_image = collection.limit(1).first()

            if first_image is None:
                return None

            # 获取属性
            properties = first_image.toDict()

            # 提取关键信息
            info = {
                'collection_id': collection_id,
                'description': properties.get('system:description', ''),
                'bands': list(first_image.bandNames().getInfo()),
                'band_count': len(first_image.bandNames().getInfo()),
                'properties': properties
            }

            # 尝试获取时间范围
            start_date = properties.get('system:time_start')
            end_date = properties.get('system:time_end')

            if start_date:
                info['start_date'] = start_date
                info['end_date'] = end_date
                info['last_update'] = end_date if end_date else start_date

            return info

        except Exception as e:
            print(f"⚠️  获取数据集信息失败 {collection_id}: {e}")
            return None

    def check_for_newer_versions(self,
                                dataset_type: str) -> List[Dict[str, Any]]:
        """
        检查是否有新版本的数据集

        Args:
            dataset_type: 数据集类型（如'MODIS', 'Landsat'）

        Returns:
            list: 新版本信息列表
        """
        newer_versions = []

        if dataset_type == 'MODIS':
            # 检查不同的版本号
            for version in ['061', '062', '063', '064']:  # 尝试未来版本
                test_collections = [
                    f'MODIS/{version}/MOD11A2',  # LST
                    f'MODIS/{version}/MOD13Q1',  # NDVI
                ]

                for collection_id in test_collections:
                    try:
                        collection = ee.ImageCollection(collection_id)
                        info = self._get_collection_info(collection_id)

                        if info:
                            newer_versions.append({
                                'version': version,
                                'collection_id': collection_id,
                                'status': 'available'
                            })
                            print(f"✅ 发现新版本: {collection_id}")

                    except Exception:
                        # 版本不存在
                        pass

        return newer_versions

    def auto_update_extractors(self,
                              force: bool = False) -> Dict[str, Any]:
        """
        自动更新提取器配置

        Args:
            force: 是否强制更新（即使版本号相同）

        Returns:
            dict: 更新报告
        """
        update_report = {
            'timestamp': datetime.now().isoformat(),
            'updates': [],
            'recommendations': []
        }

        print("\\n🤖 开始智能数据发现...")

        # 1. 发现最新数据集
        latest_datasets = self.discover_latest_datasets()

        if len(latest_datasets) > 0:
            print(f"\\n📊 发现 {len(latest_datasets)} 个可用数据集")

            # 2. 检查版本更新
            for dataset_type in ['MODIS', 'Landsat']:
                newer = self.check_for_newer_versions(dataset_type)

                if newer:
                    print(f"\\n✨ 发现 {dataset_type} 新版本:")
                    for v in newer:
                        print(f"   - 版本 {v['version']}: {v['collection_id']}")

                        update_report['updates'].append(v)
                        update_report['recommendations'].append({
                            'type': 'version_update',
                            'dataset': dataset_type,
                            'current': '061',
                            'new': v['version'],
                            'collection': v['collection_id'],
                            'action': '建议更新配置文件'
                        })

        # 3. 生成推荐
        self._generate_recommendations(update_report)

        # 4. 保存报告
        self._save_update_report(update_report)

        return update_report

    def _generate_recommendations(self, report: Dict[str, Any]):
        """生成更新推荐"""
        print("\\n💡 智能推荐:")

        for rec in report['recommendations']:
            if rec['type'] == 'version_update':
                print(f"   🔄 {rec['dataset']}: 版本 {rec['current']} → {rec['new']}")
                print(f"      数据集: {rec['collection']}")
                print(f"      操作: {rec['action']}")

    def _save_update_report(self, report: Dict[str, Any]):
        """保存更新报告"""
        import json
        from pathlib import Path

        report_dir = Path('./cache')
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / f"gee_update_report_{datetime.now().strftime('%Y%m%d')}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"\\n💾 更新报告已保存: {report_file}")

    def search_datasets_by_keywords(self,
                                   keywords: List[str]) -> pd.DataFrame:
        """
        根据关键词搜索数据集

        Args:
            keywords: 关键词列表

        Returns:
            DataFrame: 搜索结果
        """
        print(f"\\n🔍 搜索数据集: {', '.join(keywords)}")

        # 这里可以扩展为实际的GEE搜索
        # 目前使用已知数据集

        all_datasets = []

        # MODIS数据集
        modis_datasets = {
            'MODIS/061/MOD11A2': {
                'name': '地表温度',
                'keywords': ['LST', 'temperature', 'thermal'],
                'resolution': '1000m',
                'temporal': '8-day'
            },
            'MODIS/061/MOD13Q1': {
                'name': '植被指数',
                'keywords': ['NDVI', 'EVI', 'vegetation'],
                'resolution': '250m',
                'temporal': '16-day'
            }
        }

        for collection_id, info in modis_datasets.items():
            # 检查关键词匹配
            match_score = 0
            matched_keywords = []

            for keyword in keywords:
                keyword_lower = keyword.lower()

                # 检查名称
                if keyword_lower in info['name'].lower():
                    match_score += 2
                    matched_keywords.append(keyword)

                # 检查关键词列表
                if any(keyword_lower in kw.lower() for kw in info['keywords']):
                    match_score += 1
                    if keyword not in matched_keywords:
                        matched_keywords.append(keyword)

            if match_score > 0:
                all_datasets.append({
                    'collection_id': collection_id,
                    'name': info['name'],
                    'match_score': match_score,
                    'matched_keywords': ', '.join(matched_keywords),
                    'resolution': info['resolution'],
                    'temporal': info['temporal']
                })

        if all_datasets:
            df = pd.DataFrame(all_datasets)
            df = df.sort_values('match_score', ascending=False)
            return df
        else:
            return pd.DataFrame()

    def get_recommended_dataset(self,
                               data_type: str) -> Dict[str, Any]:
        """
        为特定数据类型推荐最佳数据集

        Args:
            data_type: 数据类型（如'LST', 'NDVI'）

        Returns:
            dict: 推荐的数据集信息
        """
        recommendations = {
            'LST': {
                'primary': 'MODIS/061/MOD11A2',
                'alternatives': ['LANDSAT/LC08/C02/T1_L2'],
                'reason': 'MODIS提供8天重访，适合长期监测',
                'resolution': '1000m',
                'temporal_coverage': '2000-至今'
            },
            'NDVI': {
                'primary': 'MODIS/061/MOD13Q1',
                'alternatives': ['LANDSAT/LC08/C02/T1_L2', 'Sentinel-2'],
                'reason': 'MODIS提供16天重访，全球覆盖',
                'resolution': '250m',
                'temporal_coverage': '2000-至今'
            },
            'population': {
                'primary': 'WorldPop/GP/100m/pop',
                'alternatives': ['GPWv4'],
                'reason': 'WorldPop提供高分辨率人口数据',
                'resolution': '100m',
                'temporal_coverage': '2000-2020'
            }
        }

        return recommendations.get(data_type, {})


class AutoExtractorUpdater:
    """
    自动提取器更新器

    根据GEE数据发现结果，自动更新提取器代码
    """

    def __init__(self):
        """初始化更新器"""
        self.discoverer = GEEDataDiscoverer()

    def check_and_update(self,
                         extractor_name: str) -> Dict[str, Any]:
        """
        检查并更新指定的提取器

        Args:
            extractor_name: 提取器名称（如'LSTExtractor'）

        Returns:
            dict: 更新报告
        """
        print(f"\\n🔧 检查 {extractor_name}...")

        # 运行智能发现
        update_report = self.discoverer.auto_update_extractors()

        # 分析更新建议
        if update_report['updates']:
            print(f"\\n✨ 发现 {len(update_report['updates'])} 个更新")

            # 生成更新代码
            for update in update_report['updates']:
                if update['status'] == 'available':
                    print(f"\\n📝 更新建议:")
                    print(f"   版本: {update['version']}")
                    print(f"   数据集: {update['collection_id']}")

                    # 这里可以添加自动更新代码的逻辑
                    # 比如修改extractors/*.py文件

        return update_report

    def generate_update_script(self,
                               updates: List[Dict[str, Any]]) -> str:
        """
        生成自动更新脚本

        Args:
            updates: 更新列表

        Returns:
            str: Python脚本内容
        """
        script = f'''#!/usr/bin/env python3
"""
自动生成的提取器更新脚本
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import sys
sys.path.insert(0, '.')

# 更新记录
updates = {updates}

print("🤖 开始自动更新提取器...")

for update in updates:
    print(f"更新: {{update['collection_id']}}")
    # 这里添加实际的更新逻辑

print("✅ 更新完成！")
'''

        return script


# 使用示例
if __name__ == "__main__":
    discoverer = GEEDataDiscoverer()

    # 发现最新数据集
    print("=== GEE数据智能发现 ===")

    # 1. 搜索特定关键词
    results = discoverer.search_datasets_by_keywords(['LST', 'temperature'])
    if not results.empty:
        print("\\n搜索结果:")
        print(results[['collection_id', 'name', 'match_score', 'resolution']])

    # 2. 获取推荐
    print("\\n=== 数据集推荐 ===")
    for data_type in ['LST', 'NDVI']:
        rec = discoverer.get_recommended_dataset(data_type)
        if rec:
            print(f"\\n{data_type}:")
            print(f"  推荐: {rec['primary']}")
            print(f"  理由: {rec['reason']}")
            print(f"  分辨率: {rec['resolution']}")

    # 3. 检查更新
    print("\\n=== 自动检查更新 ===")
    updater = AutoExtractorUpdater()
    report = updater.check_and_update('LSTExtractor')
