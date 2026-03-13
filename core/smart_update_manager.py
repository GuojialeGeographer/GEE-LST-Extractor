"""
智能更新管理器 - 一键更新所有数据源
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from smart_dataset_discoverer import SmartDatasetDiscoverer, DatasetVersionTracker


class SmartUpdateManager:
    """
    智能更新管理器

    功能：
    1. 一键发现所有数据源的最新版本
    2. 自动更新提取器配置
    3. 验证更新后的配置
    4. 提供回滚功能
    """

    def __init__(self, config_path: str = 'config/datasets_config.json'):
        """
        初始化

        参数:
        -------
        config_path : str
            配置文件路径
        """
        self.config_path = Path(config_path)
        self.backup_path = self.config_path.parent / f"{self.config_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        self.discoverer = SmartDatasetDiscoverer()
        self.version_tracker = DatasetVersionTracker()

        self.current_config = self._load_config()
        self.update_history = []

    def _load_config(self) -> Dict[str, Any]:
        """加载当前配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  配置文件不存在: {self.config_path}")
            return {}

    def _save_config(self, config: Dict[str, Any]):
        """保存配置"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def _backup_config(self):
        """备份当前配置"""
        if self.config_path.exists():
            shutil.copy2(self.config_path, self.backup_path)
            print(f"✅ 配置已备份到: {self.backup_path}")

    def check_updates(self, data_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        检查可用的更新

        参数:
        -------
        data_types : list, optional
            要检查的数据类型，None表示检查所有

        返回:
        -------
        dict
            可用的更新
        """
        print("\n🔍 检查数据集更新...")
        print("="*60)

        if data_types is None:
            data_types = self.discoverer.DATASET_PATTERNS.keys()

        available_updates = {}

        for data_type in data_types:
            print(f"\n检查 {data_type}...")
            recommendation = self.discoverer.recommend_dataset(data_type)

            if 'error' not in recommendation:
                current_collection = self.current_config.get(data_type, {}).get('collection', '')
                recommended_collection = recommendation['recommended_collection']

                if current_collection != recommended_collection:
                    available_updates[data_type] = {
                        'current': current_collection,
                        'recommended': recommended_collection,
                        'current_version': self._extract_version(current_collection),
                        'recommended_version': recommendation['version'],
                        'reason': recommendation['reason']
                    }
                    print(f"  ✅ 发现更新: {current_collection} → {recommended_collection}")
                else:
                    print(f"  ℹ️  已是最新版本: {current_collection}")
            else:
                print(f"  ⚠️  {recommendation['error']}")

        return available_updates

    def _extract_version(self, collection_id: str) -> str:
        """从集合ID提取版本号"""
        try:
            return collection_id.split('/')[1]
        except:
            return 'unknown'

    def apply_updates(self, updates: Dict[str, Dict[str, Any]], create_backup: bool = True) -> bool:
        """
        应用更新

        参数:
        -------
        updates : dict
            要应用的更新
        create_backup : bool
            是否创建备份

        返回:
        -------
        bool
            是否成功
        """
        print("\n🔄 应用更新...")
        print("="*60)

        # 创建备份
        if create_backup:
            self._backup_config()

        try:
            # 更新配置
            updated_config = self.current_config.copy()

            for data_type, update_info in updates.items():
                print(f"\n更新 {data_type}:")
                print(f"  {update_info['current']} → {update_info['recommended']}")

                # 更新配置
                if data_type not in updated_config:
                    updated_config[data_type] = {}

                updated_config[data_type]['collection'] = update_info['recommended']

                # 获取新的元数据
                try:
                    metadata = self.discoverer.get_dataset_metadata(update_info['recommended'])
                    if 'bands' in metadata:
                        updated_config[data_type]['band'] = metadata['bands'][0] if metadata['bands'] else 'value'
                    if 'time_range' in metadata:
                        updated_config[data_type]['time_range'] = metadata['time_range']
                except Exception as e:
                    print(f"  ⚠️  无法获取元数据: {e}")

                # 记录到版本历史
                self.version_tracker.record_version(
                    data_type,
                    update_info['recommended'],
                    update_info
                )

            # 保存新配置
            self._save_config(updated_config)
            self.current_config = updated_config

            # 记录更新历史
            self.update_history.append({
                'timestamp': datetime.now().isoformat(),
                'updates': updates,
                'backup_file': str(self.backup_path) if create_backup else None
            })

            print(f"\n✅ 更新完成！共更新 {len(updates)} 个数据源")
            return True

        except Exception as e:
            print(f"\n❌ 更新失败: {e}")
            print("💡 配置未更改")
            return False

    def rollback_update(self, backup_file: Optional[str] = None) -> bool:
        """
        回滚到之前的配置

        参数:
        -------
        backup_file : str, optional
            备份文件路径，None表示使用最新备份

        返回:
        -------
        bool
            是否成功
        """
        print("\n⏪ 回滚配置...")

        if backup_file is None:
            # 查找最新的备份文件
            backup_files = list(self.config_path.parent.glob(f"{self.config_path.stem}_backup_*.json"))
            if not backup_files:
                print("❌ 未找到备份文件")
                return False
            backup_file = str(max(backup_files))

        backup_path = Path(backup_file)
        if not backup_path.exists():
            print(f"❌ 备份文件不存在: {backup_file}")
            return False

        try:
            # 恢复备份
            shutil.copy2(backup_path, self.config_path)
            self.current_config = self._load_config()
            print(f"✅ 已从备份恢复: {backup_file}")
            return True
        except Exception as e:
            print(f"❌ 回滚失败: {e}")
            return False

    def validate_updates(self) -> Dict[str, Any]:
        """
        验证更新后的配置

        返回:
        -------
        dict
            验证结果
        """
        print("\n✅ 验证更新...")
        print("="*60)

        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        for data_type, config in self.current_config.items():
            print(f"\n验证 {data_type}...")

            try:
                # 检查集合是否可访问
                collection_id = config.get('collection', '')
                if not collection_id:
                    validation_results['errors'].append(f"{data_type}: 缺少collection配置")
                    validation_results['valid'] = False
                    continue

                # 尝试访问集合
                metadata = self.discoverer.get_dataset_metadata(collection_id)

                if 'error' in metadata:
                    validation_results['errors'].append(f"{data_type}: {metadata['error']}")
                    validation_results['valid'] = False
                else:
                    print(f"  ✅ {collection_id} 可访问")

                    # 检查波段配置
                    if 'band' not in config:
                        validation_results['warnings'].append(f"{data_type}: 未指定band，将使用默认值")
                    else:
                        band = config['band']
                        if band not in metadata.get('bands', []):
                            validation_results['warnings'].append(
                                f"{data_type}: 波段'{band}'不在集合中，可用波段: {metadata.get('bands', [])}"
                            )

            except Exception as e:
                validation_results['errors'].append(f"{data_type}: {str(e)}")
                validation_results['valid'] = False

        return validation_results

    def update_all(self, auto_apply: bool = False, create_backup: bool = True) -> Dict[str, Any]:
        """
        一键更新所有数据源

        参数:
        -------
        auto_apply : bool
            是否自动应用更新
        create_backup : bool
            是否创建备份

        返回:
        -------
        dict
            更新结果
        """
        print("\n" + "="*60)
        print("🚀 智能数据更新系统")
        print("="*60)

        # 步骤1：检查更新
        available_updates = self.check_updates()

        if not available_updates:
            print("\n✅ 所有数据源已是最新版本，无需更新")
            return {
                'success': True,
                'message': '已是最新版本',
                'updated_count': 0
            }

        print(f"\n📊 发现 {len(available_updates)} 个可用更新")

        # 显示更新摘要
        self._print_update_summary(available_updates)

        if not auto_apply:
            # 询问用户是否应用
            response = input("\n是否应用这些更新？(y/n): ").strip().lower()
            if response != 'y':
                print("❌ 取消更新")
                return {
                    'success': False,
                    'message': '用户取消更新',
                    'available_updates': available_updates
                }

        # 步骤2：应用更新
        success = self.apply_updates(available_updates, create_backup)

        if not success:
            return {
                'success': False,
                'message': '更新失败',
                'available_updates': available_updates
            }

        # 步骤3：验证更新
        validation = self.validate_updates()

        if not validation['valid']:
            print("\n⚠️  验证失败，建议回滚")
            print("错误:")
            for error in validation['errors']:
                print(f"  - {error}")
        else:
            print("\n✅ 验证通过")

        if validation['warnings']:
            print("\n⚠️  警告:")
            for warning in validation['warnings']:
                print(f"  - {warning}")

        return {
            'success': validation['valid'],
            'message': '更新完成',
            'updated_count': len(available_updates),
            'validation': validation,
            'backup_file': str(self.backup_path) if create_backup else None
        }

    def _print_update_summary(self, updates: Dict[str, Dict[str, Any]]):
        """打印更新摘要"""
        print("\n" + "="*60)
        print("更新摘要")
        print("="*60)

        for data_type, update_info in updates.items():
            print(f"\n{data_type}:")
            print(f"  当前: {update_info['current_version']} - {update_info['current']}")
            print(f"  推荐: {update_info['recommended_version']} - {update_info['recommended']}")
            print(f"  原因: {update_info['reason']}")

    def get_update_history(self) -> List[Dict[str, Any]]:
        """获取更新历史"""
        return self.update_history

    def export_update_report(self, output_path: str = 'output/update_report.json'):
        """
        导出更新报告

        参数:
        -------
        output_path : str
            输出路径
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'current_config': self.current_config,
            'update_history': self.update_history,
            'version_history': self.version_tracker.history
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ 更新报告已导出: {output_path}")


# 便捷函数
def smart_update_all(config_path: str = 'config/datasets_config.json',
                    auto_apply: bool = False) -> Dict[str, Any]:
    """
    一键更新所有数据源

    参数:
    -------
    config_path : str
        配置文件路径
    auto_apply : bool
        是否自动应用更新

    返回:
    -------
    dict
        更新结果
    """
    manager = SmartUpdateManager(config_path)
    return manager.update_all(auto_apply=auto_apply)


# 使用示例
if __name__ == '__main__':
    # 示例1：检查更新
    manager = SmartUpdateManager()
    updates = manager.check_updates()

    # 示例2：更新所有
    result = manager.update_all(auto_apply=False)

    # 示例3：导出报告
    manager.export_update_report()
