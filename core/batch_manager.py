"""
批次管理器 - 批次划分和任务派发

负责：
1. 数据分批
2. 任务派发控制
3. 并发管理
4. 进度跟踪
"""

import pandas as pd
import numpy as np
from typing import List, Callable, Optional
import time


class BatchManager:
    """
    批次管理器

    设计目的：
    1. 避免GEE任务过大导致超时或内存溢出
    2. 控制提交速率，避免触发GEE限流
    3. 提供进度跟踪和错误重试

    批次大小建议：
    - 1000点/批：保守，适合测试
    - 5000点/批：推荐，平衡效率与稳定性 ✅
    - 10000点/批：激进，可能超时

    使用场景：
    - 大规模数据提取（>10000点）
    - 需要稳定性和可恢复性
    - 避免GEE配额限制

    示例：
        batch_manager = BatchManager(
            points_per_task=5000,
            delay_between_tasks=3
        )

        # 创建批次
        batches = batch_manager.create_batches(unique_grids_df)

        # 提交任务
        for i, batch in enumerate(batches):
            print(f"提交批次 {i+1}/{len(batches)}")
            # 提交GEE任务...
            batch_manager.delay()  # 控制速率
    """

    def __init__(self,
                 points_per_task: int = 5000,
                 delay_between_tasks: float = 3.0,
                 max_retries: int = 3):
        """
        初始化批次管理器

        Args:
            points_per_task: 每个GEE任务处理的最大点数
                           建议值：5000（平衡效率和稳定性）
            delay_between_tasks: 任务之间的延迟（秒）
                                 建议值：3秒（避免触发限流）
            max_retries: 失败任务的最大重试次数

        配置建议：
        - 快速测试：points_per_task=1000
        - 生产环境：points_per_task=5000 ✅
        - 超大数据：points_per_task=10000（风险较高）
        """
        self.points_per_task = points_per_task
        self.delay_between_tasks = delay_between_tasks
        self.max_retries = max_retries

        # 统计信息
        self.stats = {
            'total_batches': 0,
            'submitted_batches': 0,
            'failed_batches': 0,
            'retried_batches': 0
        }

    def create_batches(self,
                      df: pd.DataFrame,
                      group_by: Optional[list] = None) -> List[pd.DataFrame]:
        """
        将数据分成批次

        支持分组批处理：
        - 如果指定group_by，先按列分组，再在每组内分批
        - 适用于按年月分组的场景

        Args:
            df: 输入数据（通常是唯一网格）
            group_by: 分组列名（如['year', 'month']）

        Returns:
            List[pd.DataFrame]: 批次列表

        示例：
            # 简单分批
            batches = batch_manager.create_batches(unique_grids)

            # 按年月分组后分批
            batches = batch_manager.create_batches(
                unique_grids,
                group_by=['year', 'month']
            )
        """
        batches = []

        if group_by:
            # 分组后分批
            grouped = df.groupby(group_by)

            for group_keys, group_df in grouped:
                # 在每组内分批
                for i in range(0, len(group_df), self.points_per_task):
                    batch = group_df.iloc[i:i+self.points_per_task]
                    batches.append(batch)

        else:
            # 直接分批
            for i in range(0, len(df), self.points_per_task):
                batch = df.iloc[i:i+self.points_per_task]
                batches.append(batch)

        # 更新统计
        self.stats['total_batches'] = len(batches)

        print(f"批次划分完成：")
        print(f"  总点数：{len(df):,}")
        print(f"  批次大小：{self.points_per_task:,}点/批")
        print(f"  批次数量：{len(batches)}")

        # 显示批次大小分布
        batch_sizes = [len(b) for b in batches]
        print(f"  批次大小：最小{min(batch_sizes)}，最大{max(batch_sizes)}，平均{int(np.mean(batch_sizes))}")

        return batches

    def delay(self, custom_delay: Optional[float] = None):
        """
        任务之间的延迟

        用于控制提交速率，避免触发GEE限流

        Args:
            custom_delay: 自定义延迟（秒），None使用默认值

        示例：
            batch_manager.delay()  # 使用默认延迟
            batch_manager.delay(5)  # 自定义延迟
        """
        delay = custom_delay if custom_delay is not None else self.delay_between_tasks
        time.sleep(delay)

    def submit_with_retry(self,
                         task_func: Callable,
                         batch: pd.DataFrame,
                         batch_id: int = None,
                         verbose: bool = True) -> bool:
        """
        提交任务并支持重试

        Args:
            task_func: 任务函数（接受batch作为参数）
            batch: 批次数据
            batch_id: 批次ID（用于日志）
            verbose: 是否打印详细信息

        Returns:
            bool: 成功返回True，失败返回False

        示例：
            def submit_gee_task(batch):
                # 提交GEE任务的逻辑
                task = ee.batch.Export.table.toDrive(...)
                task.start()
                return task

            success = batch_manager.submit_with_retry(
                task_func=submit_gee_task,
                batch=batch,
                batch_id=0
            )
        """
        batch_id = batch_id if batch_id is not None else 0

        for attempt in range(self.max_retries + 1):
            try:
                if verbose:
                    print(f"  批次 {batch_id}: 尝试 {attempt + 1}/{self.max_retries + 1}")

                # 执行任务
                result = task_func(batch)

                # 更新统计
                if attempt > 0:
                    self.stats['retried_batches'] += 1
                else:
                    self.stats['submitted_batches'] += 1

                return True

            except Exception as e:
                if verbose:
                    print(f"  批次 {batch_id}: 失败 - {str(e)}")

                if attempt < self.max_retries:
                    # 等待后重试
                    if verbose:
                        print(f"  批次 {batch_id}: {self.delay_between_tasks}秒后重试...")
                    self.delay()
                else:
                    # 最后一次也失败了
                    self.stats['failed_batches'] += 1
                    if verbose:
                        print(f"  批次 {batch_id}: 放弃（已达最大重试次数）")
                    return False

        return False

    def submit_all(self,
                   batches: List[pd.DataFrame],
                   task_func: Callable,
                   progress_callback: Optional[Callable] = None) -> dict:
        """
        提交所有批次

        Args:
            batches: 批次列表
            task_func: 任务函数
            progress_callback: 进度回调函数 callback(current, total)

        Returns:
            dict: 提交结果统计

        示例：
            def submit_task(batch):
                # 提交GEE任务
                ...

            results = batch_manager.submit_all(
                batches=batches,
                task_func=submit_task
            )

            print(f"成功：{results['success']}")
            print(f"失败：{results['failed']}")
        """
        results = {
            'success': 0,
            'failed': 0,
            'total': len(batches)
        }

        for i, batch in enumerate(batches):
            # 调用进度回调
            if progress_callback:
                progress_callback(i, len(batches))

            # 提交任务
            success = self.submit_with_retry(
                task_func=task_func,
                batch=batch,
                batch_id=i
            )

            if success:
                results['success'] += 1
            else:
                results['failed'] += 1

            # 控制速率（最后一个任务不延迟）
            if i < len(batches) - 1:
                self.delay()

        return results

    def estimate_time(self, n_batches: int) -> dict:
        """
        估算总耗时

        Args:
            n_batches: 批次数量

        Returns:
            dict: 时间估算

        示例：
            # 100个批次
            time_info = batch_manager.estimate_time(100)
            print(f"预计耗时：{time_info['total_minutes']}分钟")
        """
        # 假设每个批次任务处理时间
        avg_processing_time = 10 * 60  # 10分钟（秒）

        processing_time = n_batches * avg_processing_time
        delay_time = (n_batches - 1) * self.delay_between_tasks
        total_time = processing_time + delay_time

        return {
            'total_batches': n_batches,
            'total_seconds': total_time,
            'total_minutes': total_time / 60,
            'total_hours': total_time / 3600,
            'processing_time_minutes': processing_time / 60,
            'delay_time_minutes': delay_time / 60
        }

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            dict: 统计信息
        """
        return self.stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_batches': 0,
            'submitted_batches': 0,
            'failed_batches': 0,
            'retried_batches': 0
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return (f"<BatchManager: {self.points_per_task}点/批, "
                f"{self.delay_between_tasks}秒延迟, "
                f"{self.max_retries}次重试>")
