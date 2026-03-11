"""
配置管理器 - 加载和管理配置文件

负责：
1. 加载YAML配置文件
2. 验证配置有效性
3. 合并默认配置
4. 提供配置访问接口
"""

import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """
    配置管理器

    设计目的：
    1. 统一管理所有配置
    2. 提供默认值和验证
    3. 支持配置文件的分层和继承
    4. 简化配置访问

    配置文件层次：
    1. 默认配置（硬编码）
    2. 全局配置文件
    3. 数据源配置文件
    4. 用户自定义配置

    使用示例：
        # 加载配置
        config_manager = ConfigManager('config/data_sources.yaml')

        # 访问配置
        lst_config = config_manager.get_data_source_config('LST')
        global_config = config_manager.get_global_config()

        # 验证配置
        is_valid = config_manager.validate()
    """

    DEFAULT_GLOBAL_CONFIG = {
        'parallel': {
            'enabled': True,
            'max_workers': 3
        },
        'batch': {
            'points_per_task': 5000,
            'delay_between_tasks': 3.0
        },
        'output': {
            'format': 'csv',
            'include_metadata': True,
            'include_quality_flags': True,
            'compression': False
        },
        'quality': {
            'apply_filling_strategies': True,
            'filling_priority': [
                'extended_temporal',
                'spatial_neighbors',
                'temporal_interp',
                'regional_mean'
            ]
        }
    }

    def __init__(self,
                 config_path: Optional[str] = None,
                 config_dict: Optional[Dict[str, Any]] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径（YAML）
            config_dict: 配置字典（与config_path二选一）

        Raises:
            ValueError: 如果既没提供config_path也没提供config_dict
        """
        if config_path:
            self.config = self._load_from_file(config_path)
            self.config_path = config_path
        elif config_dict:
            self.config = config_dict
            self.config_path = None
        else:
            raise ValueError("必须提供config_path或config_dict")

        # 合并默认配置
        self._merge_defaults()

    def _load_from_file(self, path: str) -> Dict[str, Any]:
        """
        从YAML文件加载配置

        Args:
            path: 文件路径

        Returns:
            dict: 配置字典
        """
        config_file = Path(path)

        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config

    def _merge_defaults(self):
        """合并默认配置"""
        if 'global_settings' not in self.config:
            self.config['global_settings'] = {}

        # 递归合并
        self.config['global_settings'] = self._deep_merge(
            self.DEFAULT_GLOBAL_CONFIG,
            self.config['global_settings']
        )

    def _deep_merge(self,
                    base: Dict[str, Any],
                    override: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并两个字典

        Args:
            base: 基础字典
            override: 覆盖字典

        Returns:
            dict: 合并后的字典
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get_global_config(self) -> Dict[str, Any]:
        """
        获取全局配置

        Returns:
            dict: 全局配置

        示例：
            global_config = config_manager.get_global_config()

            # 访问批处理配置
            batch_size = global_config['batch']['points_per_task']
        """
        return self.config.get('global_settings', {})

    def get_data_source_config(self,
                              source_name: str) -> Dict[str, Any]:
        """
        获取特定数据源的配置

        Args:
            source_name: 数据源名称（如'LST', 'NDVI'）

        Returns:
            dict: 数据源配置

        Raises:
            KeyError: 如果数据源不存在

        示例：
            lst_config = config_manager.get_data_source_config('LST')

            # 检查是否启用
            is_enabled = lst_config.get('enabled', False)

            # 获取参数
            parameters = lst_config.get('parameters', {})
        """
        data_sources = self.config.get('data_sources', {})

        if source_name not in data_sources:
            raise KeyError(f"数据源'{source_name}'不存在")

        return data_sources[source_name]

    def get_enabled_data_sources(self) -> list:
        """
        获取所有启用的数据源名称

        Returns:
            list: 启用的数据源名称列表

        示例：
            enabled = config_manager.get_enabled_data_sources()
            # ['LST', 'NDVI', 'PM25']
        """
        data_sources = self.config.get('data_sources', {})
        enabled = []

        for name, config in data_sources.items():
            if config.get('enabled', False):
                enabled.append(name)

        return enabled

    def get_extractor_class(self, source_name: str) -> str:
        """
        获取数据源的提取器类路径

        Args:
            source_name: 数据源名称

        Returns:
            str: 提取器类路径（如'lst_extractor.LSTExtractor'）

        示例：
            extractor_path = config_manager.get_extractor_class('LST')
            # 'lst_extractor.LSTExtractor'
        """
        config = self.get_data_source_config(source_name)
        return config.get('extractor')

    def get_output_config(self) -> Dict[str, Any]:
        """
        获取输出配置

        Returns:
            dict: 输出配置

        示例：
            output_config = config_manager.get_output_config()

            # 输出格式
            format = output_config.get('format', 'csv')

            # 是否包含质量标记
            include_flags = output_config.get('include_quality_flags', True)
        """
        global_config = self.get_global_config()
        return global_config.get('output', {})

    def get_quality_config(self) -> Dict[str, Any]:
        """
        获取质量控制配置

        Returns:
            dict: 质量控制配置

        示例：
            quality_config = config_manager.get_quality_config()

            # 是否应用填充策略
            apply_filling = quality_config.get('apply_filling_strategies', True)

            # 填充优先级
            priority = quality_config.get('filling_priority', [])
        """
        global_config = self.get_global_config()
        return global_config.get('quality', {})

    def set_data_source_enabled(self,
                               source_name: str,
                               enabled: bool):
        """
        启用或禁用数据源

        Args:
            source_name: 数据源名称
            enabled: True启用，False禁用

        示例：
            # 启用NDVI
            config_manager.set_data_source_enabled('NDVI', True)

            # 禁用PM25
            config_manager.set_data_source_enabled('PM25', False)
        """
        if 'data_sources' not in self.config:
            self.config['data_sources'] = {}

        if source_name not in self.config['data_sources']:
            raise KeyError(f"数据源'{source_name}'不存在")

        self.config['data_sources'][source_name]['enabled'] = enabled

    def validate(self) -> bool:
        """
        验证配置有效性

        检查：
        1. 必需的配置键是否存在
        2. 数据源配置是否完整
        3. 提取器类路径是否有效

        Returns:
            bool: 验证通过返回True

        Raises:
            ValueError: 验证失败

        示例：
            try:
                is_valid = config_manager.validate()
                print("配置有效")
            except ValueError as e:
                print(f"配置无效: {e}")
        """
        errors = []

        # 检查全局配置
        if 'global_settings' not in self.config:
            errors.append("缺少'global_settings'配置")

        # 检查数据源配置
        if 'data_sources' not in self.config:
            errors.append("缺少'data_sources'配置")
        else:
            for name, config in self.config['data_sources'].items():
                # 检查必需的键
                required_keys = ['extractor']
                for key in required_keys:
                    if key not in config:
                        errors.append(f"数据源'{name}'缺少'{key}'配置")

                # 检查extractor格式
                if 'extractor' in config:
                    extractor = config['extractor']
                    if not isinstance(extractor, str) or '.' not in extractor:
                        errors.append(f"数据源'{name}'的'extractor'格式无效")

        if errors:
            raise ValueError("配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors))

        return True

    def save(self, path: str):
        """
        保存配置到文件

        Args:
            path: 保存路径

        示例：
            config_manager.save('config/my_config.yaml')
        """
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

    def to_dict(self) -> Dict[str, Any]:
        """
        获取完整配置字典

        Returns:
            dict: 完整配置
        """
        return self.config.copy()

    def __repr__(self) -> str:
        """字符串表示"""
        enabled = self.get_enabled_data_sources()
        return (f"<ConfigManager: {len(enabled)}个启用数据源 "
                f"({', '.join(enabled)})>")
