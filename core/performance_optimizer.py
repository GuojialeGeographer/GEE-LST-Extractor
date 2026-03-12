"""
性能优化模块

提供批量处理优化、缓存机制等性能增强功能
"""

import time
import hashlib
import pickle
from pathlib import Path
from typing import Any, Callable, Dict, List
from functools import wraps
import concurrent.futures
from threading import Lock

import pandas as pd
import numpy as np


class PerformanceOptimizer:
    """
    性能优化器

    功能：
    1. 并行处理
    2. 结果缓存
    3. 内存优化
    4. 进度跟踪
    """

    def __init__(self, cache_dir: str = None, max_workers: int = 4):
        """
        初始化性能优化器

        Args:
            cache_dir: 缓存目录路径
            max_workers: 最大并行工作线程数
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path('./cache')
        self.cache_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.lock = Lock()

        # 缓存统计
        self.cache_hits = 0
        self.cache_misses = 0

    def cache_result(self, func: Callable) -> Callable:
        """
        结果缓存装饰器

        缓存函数调用结果，避免重复计算

        Args:
            func: 要缓存的函数

        Returns:
            装饰后的函数

        示例:
            @optimizer.cache_result
            def extract_data(params):
                # 耗时的提取操作
                return result
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = self._generate_cache_key(func.__name__, args, kwargs)
            cache_file = self.cache_dir / f"{cache_key}.pkl"

            # 尝试从缓存加载
            if cache_file.exists():
                with self.lock:
                    if cache_file.exists():
                        try:
                            with open(cache_file, 'rb') as f:
                                result = pickle.load(f)
                            self.cache_hits += 1
                            print(f"✅ 缓存命中: {func.__name__}")
                            return result
                        except Exception as e:
                            print(f"⚠️  缓存加载失败: {e}")

            # 缓存未命中，执行函数
            self.cache_misses += 1
            print(f"⚠️  缓存未命中: {func.__name__}")

            result = func(*args, **kwargs)

            # 保存到缓存
            try:
                with self.lock:
                    with open(cache_file, 'wb') as f:
                        pickle.dump(result, f)
                print(f"💾 结果已缓存: {func.__name__}")
            except Exception as e:
                print(f"⚠️  缓存保存失败: {e}")

            return result

        return wrapper

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        生成缓存键

        Args:
            func_name: 函数名
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            str: 缓存键
        """
        # 创建哈希键
        key_dict = {
            'func': func_name,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }

        key_str = str(key_dict)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()

        return key_hash

    def parallel_execute(self, tasks: List[Callable], args_list: List[tuple] = None) -> List[Any]:
        """
        并行执行多个任务

        Args:
            tasks: 任务函数列表
            args_list: 每个任务的参数列表

        Returns:
            List[Any]: 所有任务的结果

        示例:
            tasks = [extract_data1, extract_data2, extract_data3]
            results = optimizer.parallel_execute(tasks)
        """
        if args_list is None:
            args_list = [() for _ in tasks]

        if len(tasks) != len(args_list):
            raise ValueError("任务数和参数列表长度不匹配")

        results = [None] * len(tasks)

        print(f"🚀 开始并行执行 {len(tasks)} 个任务...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(task, *args): (i, task)
                for i, (task, args) in enumerate(zip(tasks, args_list))
            }

            # 收集结果
            completed = 0
            for future in concurrent.futures.as_completed(future_to_task):
                task_idx, task_func = future_to_task[future]
                try:
                    result = future.result()
                    results[task_idx] = result
                    completed += 1
                    print(f"✅ 任务 {completed}/{len(tasks)} 完成: {task_func.__name__}")
                except Exception as e:
                    print(f"❌ 任务失败: {task_func.__name__} - {e}")
                    results[task_idx] = None

        return results

    def batch_process_with_chunks(self,
                                 data: pd.DataFrame,
                                 process_func: Callable,
                                 chunk_size: int = 100) -> pd.DataFrame:
        """
        分块处理大数据集

        Args:
            data: 要处理的数据
            process_func: 处理函数
            chunk_size: 每块的大小

        Returns:
            pd.DataFrame: 处理后的数据

        示例:
            def process_chunk(chunk):
                # 处理数据块
                return processed_chunk

            result = optimizer.batch_process_with_chunks(large_df, process_chunk, chunk_size=1000)
        """
        total_chunks = (len(data) + chunk_size - 1) // chunk_size
        print(f"📊 分块处理: {len(data)} 条数据，{total_chunks} 个块")

        results = []

        for i in range(0, len(data), chunk_size):
            chunk = data.iloc[i:i+chunk_size]
            chunk_num = i // chunk_size + 1

            print(f"⚙️  处理块 {chunk_num}/{total_chunks} ({len(chunk)} 条)...")

            try:
                processed = process_func(chunk)
                results.append(processed)
            except Exception as e:
                print(f"❌ 块 {chunk_num} 处理失败: {e}")
                # 保留原始数据
                results.append(chunk)

        # 合并结果
        if results:
            return pd.concat(results, ignore_index=True)
        else:
            return pd.DataFrame()

    def optimize_memory_usage(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        优化DataFrame内存使用

        Args:
            df: 要优化的DataFrame

        Returns:
            pd.DataFrame: 优化后的DataFrame
        """
        original_memory = df.memory_usage(deep=True).sum() / 1024 / 1024

        # 优化数值类型
        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')

        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')

        # 优化字符串类型
        for col in df.select_dtypes(include=['object']).columns:
            num_unique = df[col].nunique()
            num_total = len(df[col])

            if num_unique / num_total < 0.5:  # 唯一值少于50%
                df[col] = df[col].astype('category')

        optimized_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        reduction = (1 - optimized_memory / original_memory) * 100

        print(f"💾 内存优化:")
        print(f"   原始: {original_memory:.2f} MB")
        print(f"   优化后: {optimized_memory:.2f} MB")
        print(f"   减少: {reduction:.1f}%")

        return df

    def monitor_performance(self, func: Callable) -> Callable:
        """
        性能监控装饰器

        监控函数执行时间和资源使用

        Args:
            func: 要监控的函数

        Returns:
            装饰后的函数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"⏱️  开始执行: {func.__name__}")

            start_time = time.time()
            start_memory = self._get_memory_usage()

            try:
                result = func(*args, **kwargs)

                end_time = time.time()
                end_memory = self._get_memory_usage()

                execution_time = end_time - start_time
                memory_used = end_memory - start_memory

                print(f"✅ 执行完成: {func.__name__}")
                print(f"   执行时间: {execution_time:.2f} 秒")
                print(f"   内存使用: {memory_used:.2f} MB")

                return result

            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time

                print(f"❌ 执行失败: {func.__name__}")
                print(f"   执行时间: {execution_time:.2f} 秒")
                print(f"   错误: {e}")

                raise

        return wrapper

    def _get_memory_usage(self) -> float:
        """
        获取当前进程的内存使用量（MB）

        Returns:
            float: 内存使用量（MB）
        """
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def clear_cache(self, pattern: str = None):
        """
        清除缓存文件

        Args:
            pattern: 文件名模式（可选），如果为None则清除所有缓存
        """
        if pattern:
            cache_files = list(self.cache_dir.glob(f"*{pattern}*.pkl"))
        else:
            cache_files = list(self.cache_dir.glob("*.pkl"))

        cleared = 0
        for cache_file in cache_files:
            try:
                cache_file.unlink()
                cleared += 1
            except Exception as e:
                print(f"⚠️  无法删除缓存文件 {cache_file}: {e}")

        print(f"🗑️  清除了 {cleared} 个缓存文件")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            dict: 缓存统计
        """
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files) / 1024 / 1024

        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_files': len(cache_files),
            'total_size_mb': total_size,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate_percent': hit_rate
        }

    def print_cache_stats(self):
        """打印缓存统计信息"""
        stats = self.get_cache_stats()

        print("📊 缓存统计:")
        print(f"   缓存文件数: {stats['cache_files']}")
        print(f"   总大小: {stats['total_size_mb']:.2f} MB")
        print(f"   缓存命中: {stats['cache_hits']}")
        print(f"   缓存未命中: {stats['cache_misses']}")
        print(f"   命中率: {stats['hit_rate_percent']:.1f}%")


class ProgressTracker:
    """
    进度跟踪器

    用于跟踪长时间运行任务的进度
    """

    def __init__(self, total_tasks: int):
        """
        初始化进度跟踪器

        Args:
            total_tasks: 总任务数
        """
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = time.time()

    def update(self, success: bool = True):
        """
        更新进度

        Args:
            success: 任务是否成功
        """
        if success:
            self.completed_tasks += 1
        else:
            self.failed_tasks += 1

        self._print_progress()

    def _print_progress(self):
        """打印进度信息"""
        progress_percent = (self.completed_tasks / self.total_tasks) * 100
        elapsed_time = time.time() - self.start_time

        if self.completed_tasks > 0:
            avg_time = elapsed_time / self.completed_tasks
            remaining_tasks = self.total_tasks - self.completed_tasks
            eta = avg_time * remaining_tasks

            print(f"\\r⏳ 进度: {self.completed_tasks}/{self.total_tasks} "
                  f"({progress_percent:.1f}%) | "
                  f"失败: {self.failed_tasks} | "
                  f"ETA: {eta:.0f}秒", end='')

            if self.completed_tasks == self.total_tasks:
                print()  # 换行

    def is_complete(self) -> bool:
        """检查是否所有任务完成"""
        return (self.completed_tasks + self.failed_tasks) >= self.total_tasks


# 使用示例
if __name__ == "__main__":
    # 创建性能优化器
    optimizer = PerformanceOptimizer(cache_dir='./cache', max_workers=4)

    # 示例1: 使用缓存
    @optimizer.cache_result
    def expensive_computation(n):
        print(f"执行复杂计算: {n}")
        time.sleep(1)
        return n * 2

    # 第一次调用会执行
    result1 = expensive_computation(5)

    # 第二次调用会从缓存读取
    result2 = expensive_computation(5)

    # 示例2: 并行执行
    def task1():
        time.sleep(0.5)
        return "Task 1 完成"

    def task2():
        time.sleep(0.5)
        return "Task 2 完成"

    results = optimizer.parallel_execute([task1, task2])

    # 示例3: 内存优化
    df = pd.DataFrame({
        'a': range(10000),
        'b': ['value'] * 10000,
        'c': 1.5
    })

    optimized_df = optimizer.optimize_memory_usage(df)

    # 打印缓存统计
    optimizer.print_cache_stats()
