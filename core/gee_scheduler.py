"""
GEE任务调度器 - 智能批处理和配额管理

遵守GEE速率限制，优化大规模数据提取
"""

import ee
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path


class GEETaskScheduler:
    """
    GEE任务调度器

    功能：
    1. 任务队列管理
    2. 并发控制（遵守GEE配额）
    3. 速率限制管理
    4. 进度监控
    5. 失败重试

    GEE配额（免费账户）：
    - 并发导出任务：3个
    - 每日导出限制：2500个
    - 任务提交速率：~10个/分钟

    使用示例：
        scheduler = GEETaskScheduler()

        # 添加任务
        for i in range(100):
            scheduler.add_task(task_id=i, data=batch[i])

        # 执行所有任务
        scheduler.run_all()
    """

    # GEE配额限制
    QUOTAS = {
        'max_concurrent': 3,          # 最大并发任务数
        'max_per_minute': 10,          # 每分钟最大任务数
        'max_per_day': 2500,           # 每日最大任务数
        'task_delay': 3,               # 任务提交延迟（秒）
        'check_interval': 10,          # 任务状态检查间隔（秒）
        'task_timeout': 3600           # 任务超时时间（秒）
    }

    def __init__(self, session_dir: str = 'sessions'):
        """
        初始化调度器

        Args:
            session_dir: 会话目录（用于保存状态）
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True, parents=True)

        # 任务队列
        self.pending_tasks = []
        self.active_tasks = []
        self.completed_tasks = []
        self.failed_tasks = []

        # 统计信息
        self.stats = {
            'submitted': 0,
            'completed': 0,
            'failed': 0,
            'total_runtime': 0
        }

        # 检查今日配额
        self._check_daily_quota()

    def _check_daily_quota(self):
        """检查今日已使用的配额"""
        today = datetime.now().strftime("%Y%m%d")
        quota_file = self.session_dir / f"quota_{today}.json"

        if quota_file.exists():
            with open(quota_file, 'r') as f:
                self.daily_quota = json.load(f)
        else:
            self.daily_quota = {
                'date': today,
                'submitted': 0,
                'completed': 0
            }
            self._save_daily_quota()

    def _save_daily_quota(self):
        """保存今日配额使用情况"""
        quota_file = self.session_dir / f"quota_{self.daily_quota['date']}.json"
        with open(quota_file, 'w') as f:
            json.dump(self.daily_quota, f, indent=2)

    def _update_daily_quota(self, action: str, count: int = 1):
        """
        更新配额使用情况

        Args:
            action: 'submitted' 或 'completed'
            count: 数量
        """
        # 检查日期是否变更
        today = datetime.now().strftime("%Y%m%d")
        if today != self.daily_quota['date']:
            self.daily_quota = {
                'date': today,
                'submitted': 0,
                'completed': 0
            }

        self.daily_quota[action] += count
        self._save_daily_quota()

    def add_task(self, task_id: str, data: Dict[str, Any], priority: int = 0):
        """
        添加任务到队列

        Args:
            task_id: 任务ID
            data: 任务数据
            priority: 优先级（数字越大越优先）
        """
        task = {
            'task_id': task_id,
            'data': data,
            'priority': priority,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }

        self.pending_tasks.append(task)
        self.pending_tasks.sort(key=lambda x: x['priority'], reverse=True)

    def run_all(self, verbose: bool = True):
        """
        运行所有任务

        Args:
            verbose: 是否打印详细信息
        """
        total_tasks = len(self.pending_tasks)

        if verbose:
            print(f"\n{'='*60}")
            print(f"开始执行 {total_tasks} 个任务")
            print(f"{'='*60}")
            print(f"并发限制：{self.QUOTAS['max_concurrent']}")
            print(f"速率限制：{self.QUOTAS['max_per_minute']} 任务/分钟")
            print(f"{'='*60}\n")

        start_time = time.time()

        while self.pending_tasks or self.active_tasks:
            # 提交新任务（遵守并发限制）
            self._submit_new_tasks(verbose)

            # 检查活动任务
            self._check_active_tasks(verbose)

            # 等待一段时间
            time.sleep(self.QUOTAS['check_interval'])

        runtime = time.time() - start_time
        self.stats['total_runtime'] = runtime

        if verbose:
            print(f"\n{'='*60}")
            print(f"所有任务完成！")
            print(f"{'='*60}")
            print(f"总任务数：{total_tasks}")
            print(f"成功：{self.stats['completed']}")
            print(f"失败：{self.stats['failed']}")
            print(f"总耗时：{runtime/60:.1f} 分钟")
            print(f"平均速度：{total_tasks/(runtime/60):.1f} 任务/分钟")

    def _submit_new_tasks(self, verbose: bool):
        """提交新任务（遵守并发和速率限制）"""
        while self.pending_tasks:
            # 检查并发限制
            if len(self.active_tasks) >= self.QUOTAS['max_concurrent']:
                if verbose:
                    print(f"  达到并发限制 ({len(self.active_tasks)}/{self.QUOTAS['max_concurrent']})")
                break

            # 检查速率限制
            recent_submissions = self._get_recent_submissions(minutes=1)
            if len(recent_submissions) >= self.QUOTAS['max_per_minute']:
                if verbose:
                    print(f"  达到速率限制，等待60秒...")
                break

            # 提交任务
            task = self.pending_tasks.pop(0)
            self._submit_single_task(task, verbose)

    def _submit_single_task(self, task: Dict, verbose: bool):
        """
        提交单个任务

        Args:
            task: 任务字典
            verbose: 是否打印信息
        """
        try:
            # 创建GEE导出任务
            gee_task = self._create_gee_task(task)

            # 启动任务
            gee_task.start()

            # 更新状态
            task['status'] = 'active'
            task['gee_task'] = gee_task
            task['submitted_at'] = datetime.now().isoformat()

            self.active_tasks.append(task)
            self.stats['submitted'] += 1
            self._update_daily_quota('submitted')

            if verbose:
                print(f"  ✓ 任务 {task['task_id']} 已提交")

        except Exception as e:
            if verbose:
                print(f"  ✗ 任务 {task['task_id']} 提交失败：{e}")

            # 标记为失败
            task['status'] = 'failed'
            task['error'] = str(e)
            self.failed_tasks.append(task)
            self.stats['failed'] += 1

    def _create_gee_task(self, task: Dict) -> ee.batch.Export:
        """
        创建GEE导出任务

        Args:
            task: 任务字典

        Returns:
            ee.batch.Export.task
        """
        data = task['data']

        # 创建FeatureCollection
        fc = self._create_feature_collection(data['points'])

        # 生成文件名
        file_name = f"{data['source']}_{data['year']}_{data['month']:02d}_batch{task['task_id']}"
        description = f"{file_name}"

        # 创建导出任务
        gee_task = ee.batch.Export.table.toDrive(
            collection=fc,
            description=description,
            fileName=f"{file_name}.csv",
            folder='GEE_Results',
            fileFormat='CSV'
        )

        return gee_task

    def _create_feature_collection(self, points: pd.DataFrame) -> ee.FeatureCollection:
        """从DataFrame创建FeatureCollection"""
        features = []

        for _, row in points.iterrows():
            point = ee.Geometry.Point([row['lng'], row['lat']])
            props = {'grid_uid': row['grid_uid']}
            features.append(ee.Feature(point, props))

        return ee.FeatureCollection(features)

    def _check_active_tasks(self, verbose: bool):
        """检查活动任务状态"""
        still_active = []

        for task in self.active_tasks:
            gee_task = task['gee_task']

            if gee_task.active():
                # 检查是否超时
                submitted_at = datetime.fromisoformat(task['submitted_at'])
                elapsed = (datetime.now() - submitted_at).total_seconds()

                if elapsed > self.QUOTAS['task_timeout']:
                    # 超时，取消并重试
                    if verbose:
                        print(f"  ⚠ 任务 {task['task_id']} 超时，取消...")
                    # 实际应用中可以重试
                    self.failed_tasks.append(task)
                    self.stats['failed'] += 1
                else:
                    still_active.append(task)
            else:
                # 任务完成
                status = gee_task.status()

                if status['state'] == 'COMPLETED':
                    if verbose:
                        print(f"  ✓ 任务 {task['task_id']} 完成")
                    self.completed_tasks.append(task)
                    self.stats['completed'] += 1
                    self._update_daily_quota('completed')
                else:
                    # 失败
                    if verbose:
                        print(f"  ✗ 任务 {task['task_id']} 失败：{status['state']}")
                    self.failed_tasks.append(task)
                    self.stats['failed'] += 1

        self.active_tasks = still_active

    def _get_recent_submissions(self, minutes: int = 1) -> List[Dict]:
        """获取最近提交的任务"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent = [
            task for task in self.active_tasks
            if datetime.fromisoformat(task['submitted_at']) > cutoff_time
        ]
        return recent

    def get_status(self) -> Dict[str, Any]:
        """
        获取当前状态

        Returns:
            dict: 状态信息
        """
        return {
            'pending': len(self.pending_tasks),
            'active': len(self.active_tasks),
            'completed': self.stats['completed'],
            'failed': self.stats['failed'],
            'total': self.stats['completed'] + self.stats['failed'] + len(self.active_tasks) + len(self.pending_tasks),
            'progress': f"{self.stats['completed']}/{self.stats['completed'] + self.stats['failed'] + len(self.active_tasks) + len(self.pending_tasks)}"
        }

    def save_checkpoint(self):
        """保存检查点"""
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'pending': [t['task_id'] for t in self.pending_tasks],
            'active': [t['task_id'] for t in self.active_tasks],
            'completed': [t['task_id'] for t in self.completed_tasks],
            'failed': [t['task_id'] for t in self.failed_tasks]
        }

        checkpoint_file = self.session_dir / 'checkpoint.json'
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        print(f"✓ 检查点已保存")

    def load_checkpoint(self):
        """加载检查点"""
        checkpoint_file = self.session_dir / 'checkpoint.json'

        if not checkpoint_file.exists():
            print("没有找到检查点")
            return

        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)

        print(f"✓ 检查点已加载：{checkpoint['timestamp']}")
        print(f"   进度：{checkpoint['stats']['completed']} 个任务完成")

        # TODO: 重建任务队列
        # 这需要更复杂的逻辑来恢复GEE任务

    def __repr__(self) -> str):
        """字符串表示"""
        status = self.get_status()
        return (f"<GEETaskScheduler: "
                f"待处理={status['pending']}, "
                f"进行中={status['active']}, "
                f"已完成={status['completed']}, "
                f"失败={status['failed']}>")


class GEETaskSchedulerLite:
    """
    GEE任务调度器（简化版）

    用于小规模数据提取（<100个任务）
    不需要复杂的并发管理
    """

    def __init__(self):
        self.tasks = []
        self.completed = []
        self.failed = []

    def add_task(self, task_id, data):
        """添加任务"""
        self.tasks.append({
            'task_id': task_id,
            'data': data,
            'status': 'pending'
        })

    def run_all(self, verbose=True):
        """运行所有任务"""
        total = len(self.tasks)

        if verbose:
            print(f"\n执行 {total} 个任务...\n")

        for i, task in enumerate(self.tasks):
            if verbose:
                print(f"[{i+1}/{total}] 任务 {task['task_id']}...")

            try:
                # 执行任务（这里需要调用实际的提取函数）
                result = self._execute_task(task['data'])

                task['status'] = 'completed'
                task['result'] = result
                self.completed.append(task)

                if verbose:
                    print(f"  ✓ 完成")

            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                self.failed.append(task)

                if verbose:
                    print(f"  ✗ 失败：{e}")

        if verbose:
            print(f"\n完成：{len(self.completed)}/{total}")
            print(f"失败：{len(self.failed)}/{total}")

    def _execute_task(self, data):
        """执行单个任务（需要实现）"""
        # 这里调用实际的GEE提取逻辑
        # 目前返回占位符
        return {'status': 'success', 'data': data}
