"""
会话管理器 - 实现断点续传和状态保存

支持长时间运行的任务在中断后恢复
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd


class SessionManager:
    """
    会话管理器

    功能：
    1. 保存会话状态
    2. 恢复会话状态
    3. 进度追踪
    4. 断点续传
    5. 自动保存

    使用示例：
        session = SessionManager()

        # 保存阶段
        session.save_stage('data_loading', df)

        # 恢复会话
        if session.has_saved_session():
            state = session.load_session()

        # 获取进度
        progress = session.get_progress()
    """

    def __init__(self, session_dir: str = 'sessions'):
        """
        初始化会话管理器

        Args:
            session_dir: 会话文件保存目录
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True, parents=True)

        self.session_id = self._generate_session_id()
        self.session_file = self.session_dir / f"{self.session_id}.json"

        # 当前状态
        self.state = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat(),
            'current_stage': None,
            'stages': {}
        }

    def _generate_session_id(self) -> str:
        """
        生成会话ID

        Returns:
            str: 会话ID（格式：YYYYMMDD_HHMMSS）
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def save_stage(self, stage_name: str, data: Any = None, metadata: Dict = None):
        """
        保存一个阶段的完成状态

        Args:
            stage_name: 阶段名称
            data: 阶段数据（会被保存）
            metadata: 额外的元数据

        示例：
            session.save_stage('data_loading', df, {'n_rows': len(df)})
        """
        # 保存数据（如果是DataFrame或dict）
        if data is not None:
            if isinstance(data, pd.DataFrame):
                data_file = self.session_dir / f"{stage_name}.csv"
                data.to_csv(data_file, index=False)
                data_path = str(data_file)
            elif isinstance(data, dict):
                data_file = self.session_dir / f"{stage_name}.json"
                with open(data_file, 'w') as f:
                    json.dump(data, f, indent=2)
                data_path = str(data_file)
            else:
                data_path = None

        # 更新状态
        self.state['current_stage'] = stage_name
        self.state['stages'][stage_name] = {
            'status': 'completed',
            'completed_time': datetime.now().isoformat(),
            'data_path': data_path,
            'metadata': metadata or {}
        }
        self.state['last_update'] = datetime.now().isoformat()

        # 保存到文件
        self._save_to_file()

        print(f"✓ 阶段 '{stage_name}' 已保存")

    def save_progress(self, current: int, total: int, stage_name: str = 'gee_extraction'):
        """
        保存进度信息

        Args:
            current: 当前进度
            total: 总数
            stage_name: 阶段名称
        """
        progress_pct = current / total * 100

        self.state['current_stage'] = stage_name
        self.state['stages'][stage_name] = {
            'status': 'in_progress',
            'current': current,
            'total': total,
            'progress': f"{current}/{total} ({progress_pct:.1f}%)",
            'last_update': datetime.now().isoformat()
        }
        self.state['last_update'] = datetime.now().isoformat()

        self._save_to_file()

        # 显示进度
        print(f"  进度：{current}/{total} ({progress_pct:.1f}%)")

    def mark_stage_failed(self, stage_name: str, error: str):
        """
        标记阶段失败

        Args:
            stage_name: 阶段名称
            error: 错误信息
        """
        self.state['stages'][stage_name] = {
            'status': 'failed',
            'error': error,
            'failed_time': datetime.now().isoformat()
        }
        self._save_to_file()

        print(f"✗ 阶段 '{stage_name}' 失败：{error}")

    def complete_session(self):
        """标记会话完成"""
        self.state['status'] = 'completed'
        self.state['end_time'] = datetime.now().isoformat()
        self._save_to_file()

        print(f"✓ 会话 {self.session_id} 已完成")

    def _save_to_file(self):
        """保存状态到文件"""
        with open(self.session_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def has_saved_session(self) -> bool:
        """
        检查是否有保存的会话

        Returns:
            bool: 是否有保存的会话
        """
        # 查找最新的会话文件
        session_files = list(self.session_dir.glob("*.json"))

        if not session_files:
            return False

        # 使用最新的会话文件
        latest_file = max(session_files, key=os.path.getctime)
        self.session_file = latest_file

        # 加载会话ID
        self.session_id = latest_file.stem

        return True

    def load_session(self) -> Dict[str, Any]:
        """
        加载保存的会话

        Returns:
            dict: 会话状态
        """
        with open(self.session_file, 'r') as f:
            self.state = json.load(f)

        return self.state

    def get_progress(self) -> Dict[str, Any]:
        """
        获取当前进度信息

        Returns:
            dict: 进度信息
        """
        if 'current_stage' not in self.state:
            return {'status': 'not_started'}

        current_stage = self.state['current_stage']

        if current_stage in self.state['stages']:
            stage_info = self.state['stages'][current_stage]
            return {
                'stage': current_stage,
                'status': stage_info.get('status'),
                'progress': stage_info.get('progress', 'N/A')
            }

        return {'status': 'unknown'}

    def get_stage_data(self, stage_name: str) -> Optional[Any]:
        """
        获取阶段的数据

        Args:
            stage_name: 阶段名称

        Returns:
            数据对象（DataFrame或dict），如果不存在返回None
        """
        if stage_name not in self.state['stages']:
            return None

        stage_info = self.state['stages'][stage_name]
        data_path = stage_info.get('data_path')

        if not data_path or not os.path.exists(data_path):
            return None

        # 根据文件类型加载数据
        if data_path.endswith('.csv'):
            return pd.read_csv(data_path)
        elif data_path.endswith('.json'):
            with open(data_path, 'r') as f:
                return json.load(f)

        return None

    def print_summary(self):
        """打印会话摘要"""
        if not self.has_saved_session():
            print("当前没有保存的会话")
            return

        state = self.load_session()

        print("\n" + "="*60)
        print("会话摘要")
        print("="*60)
        print(f"会话ID：{state['session_id']}")
        print(f"开始时间：{state['start_time']}")
        print(f"最后更新：{state['last_update']}")
        print(f"当前阶段：{state.get('current_stage', 'N/A')}")
        print("\n阶段状态：")

        for stage_name, stage_info in state['stages'].items():
            status = stage_info['status']
            print(f"  {stage_name}: {status}")

            if status == 'completed':
                data_path = stage_info.get('data_path', 'N/A')
                print(f"    数据：{data_path}")
            elif status == 'in_progress':
                progress = stage_info.get('progress', 'N/A')
                print(f"    进度：{progress}")
            elif status == 'failed':
                error = stage_info.get('error', 'Unknown error')
                print(f"    错误：{error}")

        print("="*60)

    def get_resume_instructions(self) -> str:
        """
        获取恢复说明

        Returns:
            str: 恢复说明
        """
        if not self.has_saved_session():
            return "没有保存的会话，无法恢复"

        state = self.load_session()
        current_stage = state.get('current_stage')

        instructions = f"""
会话恢复说明：

会话ID：{state['session_id']}
最后更新：{state['last_update']}
当前阶段：{current_stage}

恢复步骤：
1. 运行以下Cell加载会话：
   session = SessionManager()
   session.print_summary()
   state = session.load_session()

2. 根据阶段状态决定操作：
"""
        # 添加每个阶段的具体恢复说明
        for stage_name, stage_info in state['stages'].items():
            if stage_info['status'] == 'completed':
                instructions += f"\n   {stage_name}: 已完成 ✓"
                if 'data_path' in stage_info:
                    data = self.get_stage_data(stage_name)
                    if isinstance(data, pd.DataFrame):
                        instructions += f"\n      数据已加载：{len(data)} 行"
            elif stage_info['status'] == 'in_progress':
                instructions += f"\n   {stage_name}: 进行中..."
                instructions += f"\n      当前进度：{stage_info.get('progress', 'N/A')}"
                instructions += f"\n      建议：重新运行该阶段"

        return instructions

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<SessionManager: {self.session_id}>"


def create_sample_session():
    """创建示例会话（用于测试）"""
    session = SessionManager()

    # 模拟阶段1完成
    import pandas as pd
    df = pd.DataFrame({
        'lng': [116.407, 116.408],
        'lat': [39.904, 39.905]
    })
    session.save_stage('data_preparation', df, {'n_rows': len(df)})

    # 模拟阶段2完成
    session.save_stage('gridding', {'n_unique_grids': 2})

    # 模拟阶段3进行中
    session.save_progress(5, 186, 'gee_extraction')

    return session
