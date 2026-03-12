# GEE环境数据提取工具 - Notebook驱动系统设计

## 🎯 核心设计原则

### 1. Notebook-First（Notebook优先）
- **所有操作通过Notebook完成**
- **分步执行，每步可验证**
- **可视化进度**
- **交互式调整**

### 2. 一键运行
- **最少的用户干预**
- **智能进度保存**
- **断点续传**
- **错误自动恢复**

### 3. 大规模友好
- **智能批处理**
- **GEE配额管理**
- **速率限制遵循**
- **并行处理优化**

### 4. 生产就绪
- **完整的错误处理**
- **详细的日志记录**
- **状态可追溯**
- **结果可验证**

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                  GEE_Extractor_Master.ipynb              │
│                  (主Notebook - 一键运行)                  │
└─────────────────────────────────────────────────────────┘
                         ↓
    ┌──────────────────────────────────────────────┐
    │         Session Manager（会话管理器）         │
    │  - 保存/加载进度                              │
    │  - 断点续传                                   │
    │  - 状态追踪                                   │
    └──────────────────────────────────────────────┘
                         ↓
    ┌──────────────────────────────────────────────┐
    │      Notebook Pipeline（Notebook流程）        │
    │                                               │
    │  1. 配置和认证                              │
    │  2. 数据准备                                 │
    │  3. 时空网格化                               │
    │  4. 批次规划                                 │
    │  5. GEE任务派发（智能调度）                  │
    │  6. 进度监控                                 │
    │  7. 结果下载                                 │
    │  8. 数据合并                                 │
    │  9. 质量分析                                 │
    │  10. 结果导出                                │
    └──────────────────────────────────────────────┘
                         ↓
    ┌──────────────────────────────────────────────┐
    │      Core Framework（核心框架）              │
    │  - 所有数据源提取器                         │
    │  - 质量追踪                                 │
    │  - GEE辅助函数                              │
    └──────────────────────────────────────────────┘
```

---

## 📘 Notebook体系设计

### 主Notebook：一键运行
```
GEE_Extractor_Master.ipynb
├── Cell 1: 导入和初始化
├── Cell 2: GEE认证检查
├── Cell 3: 配置文件加载
├── Cell 4: 数据加载
├── Cell 5: 时空网格化
├── Cell 6: 批次规划
├── Cell 7: 智能任务派发 ⭐ 核心
├── Cell 8: 进度监控
├── Cell 9: 结果下载
├── Cell 10: 数据合并
├── Cell 11: 质量分析
└── Cell 12: 结果导出
```

### 辅助Notebooks
```
notebooks/
├── 00_Setup.ipynb              # 初始化和认证
├── 01_Quick_Start.ipynb         # 快速开始（小数据集）
├── 02_Single_Source.ipynb       # 单数据源提取
├── 03_Batch_Processing.ipynb    # 批处理（大数据集）
├── 04_Advanced_Config.ipynb     # 高级配置
└── 05_Troubleshooting.ipynb     # 问题排查
```

---

## 🔄 Session Manager设计

### 核心功能
```python
class SessionManager:
    """
    会话管理器 - 实现断点续传
    """

    def save_session(self, state):
        """保存当前会话状态"""
        session_file = 'sessions/session_state.json'
        with open(session_file, 'w') as f:
            json.dump(state, f, indent=2)

    def load_session(self):
        """恢复会话状态"""
        session_file = 'sessions/session_state.json'
        with open(session_file, 'r') as f:
            return json.load(f)

    def get_progress(self):
        """获取当前进度"""
        pass

    def resume_from_checkpoint(self, checkpoint_name):
        """从检查点恢复"""
        pass
```

### 状态保存结构
```json
{
    "session_id": "20250312_beijing_lst",
    "start_time": "2025-03-12 10:00:00",
    "last_update": "2025-03-12 14:30:00",
    "current_stage": "gee_extraction",
    "stages": {
        "data_preparation": {
            "status": "completed",
            "output": "temp/prepared_data.csv"
        },
        "gridding": {
            "status": "completed",
            "output": "temp/unique_grids.csv"
        },
        "batch_planning": {
            "status": "completed",
            "output": "temp/batch_list.csv"
        },
        "gee_extraction": {
            "status": "in_progress",
            "completed_batches": [1, 2, 3, 4, 5],
            "total_batches": 186,
            "progress": "5/186 (2.7%)"
        },
        "download": {
            "status": "pending"
        },
        "merge": {
            "status": "pending"
        }
    }
}
```

---

## ⚡ 智能任务调度器

### GEE配额管理
```python
class GEETaskScheduler:
    """
    GEE任务调度器 - 遵守速率限制
    """

    # GEE免费配额
    QUOTAS = {
        'concurrent_exports': 3,  # 同时进行的导出任务
        'exports_per_day': 2500,  # 每日导出限制
        'tasks_per_minute': 10,  # 每分钟任务数
    }

    def __init__(self):
        self.active_tasks = []
        self.completed_tasks = []
        self.failed_tasks = []

    def submit_task(self, task_info):
        """提交任务（考虑配额）"""
        # 检查并发限制
        while len(self.active_tasks) >= self.QUOTAS['concurrent_exports']:
            self.wait_for_completion()

        # 提交任务
        task = self._create_gee_task(task_info)
        task.start()
        self.active_tasks.append(task)

        # 控制提交速率
        time.sleep(3)  # 3秒延迟

    def wait_for_completion(self):
        """等待任务完成"""
        # 监控任务状态
        # 自动处理失败
        pass

    def get_status(self):
        """获取整体状态"""
        return {
            'active': len(self.active_tasks),
            'completed': len(self.completed_tasks),
            'failed': len(self.failed_tasks),
            'progress': f"{len(self.completed_tasks)}/总任务数"
        }
```

---

## 📱 主Notebook设计

### GEE_Extractor_Master.ipynb

```markdown
# GEE环境数据提取工具 - 主控台

## 使用说明
1. 运行所有Cell以完成完整流程
2. 每个步骤有进度显示
3. 支持断点续传
4. 自动保存状态

## 一键运行
- 菜单：Cell -> Run All
- 或：Shift + Enter（逐个运行）

---

## Step 1: 初始化

# 导入所需库
import sys
sys.path.append('..')

from core.session_manager import SessionManager
from core.gee_scheduler import GEETaskScheduler
from core.universal_extractor import UniversalExtractor

# 初始化会话管理器
session = SessionManager()
print("✓ 会话管理器初始化完成")

---

## Step 2: 检查和恢复

# 尝试恢复之前的会话
if session.has_saved_session():
    print("发现之前的会话，是否恢复？")
    print("1. 恢复之前的会话")
    print("2. 开始新会话")

    choice = input("请选择 (1/2): ")

    if choice == '1':
        state = session.load_session()
        print(f"✓ 会话已恢复：{state['session_id']}")
        print(f"   当前进度：{state['stages']['gee_extraction']['progress']}")
    else:
        print("开始新会话...")
else:
    print("✓ 这是新会话")

---

## Step 3: 配置加载

# 加载配置
config_path = '../config/data_sources.yaml'
extractor = UniversalExtractor(config_path=config_path)

print(f"✓ 配置已加载")
print(f"   启用的数据源：{', '.join(extractor.list_data_sources())}")

---

## Step 4: 数据加载

# 加载数据
import pandas as pd

data_path = input("请输入数据文件路径 (或直接回车使用示例数据): ")

if data_path == '':
    # 使用示例数据
    print("使用示例数据...")
    df = pd.read_csv('../data/sample_points.csv')
else:
    df = pd.read_csv(data_path)

print(f"✓ 数据已加载：{len(df):,} 行")
print(df.head())

# 保存会话状态
session.save_stage('data_loading', df)

---

## Step 5: 时空网格化

# 创建时空网格
from core.grid_manager import GridManager

grid_manager = GridManager(precision=4)
gridded_df = grid_manager.create_grids(
    df,
    year=2023,
    month=1,
    city='Beijing'
)

print(f"✓ 时空网格化完成")
print(f"   原始点数：{len(df):,}")
print(f"   唯一网格数：{gridded_df['grid_uid'].nunique():,}")
print(f"   冗余率：{(1 - gridded_df['grid_uid'].nunique()/len(df))*100:.1f}%")

# 保存会话状态
session.save_stage('gridding', gridded_df)

---

## Step 6: 批次规划

# 创建批次
batch_size = 5000
batch_manager = BatchManager(points_per_task=batch_size)

unique_grids = grid_manager.get_unique_grids(gridded_df)
batches = batch_manager.create_batches(unique_grids)

print(f"✓ 批次规划完成")
print(f"   总批次数：{len(batches)}")

# 保存批次列表
batches.to_csv('../temp/batch_list.csv', index=False)

# 保存会话状态
session.save_stage('batch_planning', batches)

---

## Step 7: GEE任务派发（核心）

# 初始化任务调度器
scheduler = GEETaskScheduler()

# 选择数据源
print("可用的数据源：")
for i, source in enumerate(extractor.list_data_sources(), 1):
    print(f"{i}. {source}")

source_choice = int(input("请选择数据源编号: "))
source_name = extractor.list_data_sources()[source_choice-1]

print(f"\n开始提取：{source_name}")
print("="*60)

# 智能任务派发
results = []

for i, batch_df in enumerate(batches):
    print(f"\n批次 {i+1}/{len(batches)}")
    print(f"  点数：{len(batch_df)}")

    # 检查配额
    status = scheduler.get_status()
    print(f"  当前状态：{status}")

    # 派发任务
    task_info = {
        'batch_id': i,
        'data': batch_df,
        'source': source_name,
        'year': 2023,
        'month': 1
    }

    scheduler.submit_task(task_info)

    # 更新进度
    progress = (i+1) / len(batches) * 100
    print(f"  总进度：{progress:.1f}%")

    # 保存进度（每10个批次保存一次）
    if (i+1) % 10 == 0:
        session.save_progress(i+1, len(batches))

print("\n✓ 所有任务已派发")

---

## Step 8: 进度监控

# 监控所有任务完成
print("等待所有任务完成...")
print("提示：这个过程可能需要几小时")
print("可以安全地关闭Notebook，稍后恢复")

scheduler.wait_for_all()

print("\n✓ 所有任务已完成")

---

## Step 9: 结果下载

# 下载所有结果
from gee_helper import download_results

results_dir = '../lst_results'
os.makedirs(results_dir, exist_ok=True)

downloaded_files = download_results(
    scheduler.completed_tasks,
    output_dir=results_dir
)

print(f"✓ 结果已下载：{len(downloaded_files)} 个文件")

---

## Step 10: 数据合并

# 合并所有结果
from core.data_merger import DataMerger

merger = DataMerger()
final_df = merger.merge_all(downloaded_files)

print(f"✓ 数据已合并：{len(final_df):,} 行")
print(final_df.head())

---

## Step 11: 质量分析

# 质量报告
from core.quality_tracker import QualityTracker

quality = QualityTracker(config)
report = quality.generate_comprehensive_report(final_df)

print("\n=== 质量报告 ===")
print(report)

---

## Step 12: 结果导出

# 导出最终结果
final_df.to_csv('../output/final_results.csv', index=False)
final_df.to_parquet('../output/final_results.parquet', index=False)

print("\n✓ 提取完成！")
print("结果已保存到：")
print("  - ../output/final_results.csv")
print("  - ../output/final_results.parquet")
```

---

## 🎯 关键特性实现

### 1. 进度可视化
```python
from IPython.display import HTML, display

def show_progress(current, total, stage_name):
    """显示进度条"""
    progress = current / total * 100

    html = f"""
    <div style="width:100%%; background:#f0f0f0; padding:10px;">
        <h3>{stage_name}</h3>
        <div style="width:100%%; background:#ddd; height:30px; border-radius:5px;">
            <div style="width:{progress}%%; background:#4CAF50; height:30px; border-radius:5px; line-height:30px; text-align:center; color:white;">
                {progress:.1f}%
            </div>
        </div>
        <p>{current}/{total} ({progress:.1f}%)</p>
    </div>
    """
    display(HTML(html))
```

### 2. 自动保存和恢复
```python
# 每个关键步骤后自动保存
def auto_save(stage_name, data):
    """自动保存状态"""
    session.save_stage(stage_name, data)
    print(f"✓ {stage_name} 已保存")

# 启动时自动恢复
def auto_resume():
    """自动恢复"""
    if session.has_saved_session():
        print("发现保存的会话，正在恢复...")
        return session.load_session()
    return None
```

### 3. 智能错误处理
```python
def safe_execute(func, max_retries=3):
    """安全执行函数"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  失败（尝试 {attempt+1}/{max_retries}）：{e}")
                print(f"  30秒后重试...")
                time.sleep(30)
            else:
                raise
```

---

## 📊 使用流程

### 新用户（第一次使用）
1. 打开 `00_Setup.ipynb` - 初始化环境
2. 运行 `01_Quick_Start.ipynb` - 快速开始（10个点）
3. 验证结果
4. 运行 `GEE_Extractor_Master.ipynb` - 完整流程

### 经验用户
1. 准备数据文件
2. 修改配置文件（如需要）
3. 运行 `GEE_Extractor_Master.ipynb`
4. 等待完成

### 大数据集（百万级）
1. 使用 `03_Batch_Processing.ipynb`
2. 配置批次大小
3. 分批处理
4. 断点续传

---

## 🔧 配置文件

### 全局配置
```yaml
# config/global_config.yaml

gee:
  # 并发限制
  max_concurrent_tasks: 3
  task_delay_seconds: 3

  # 批次配置
  default_batch_size: 5000
  max_batch_size: 10000

  # 速率限制
  tasks_per_minute: 10
  exports_per_day: 2500

processing:
  # 进度保存
  save_interval_minutes: 5
  auto_save: true

  # 断点续传
  enable_resume: true
  checkpoint_dir: 'sessions'

output:
  # 输出格式
  formats: ['csv', 'parquet']

  # 质量报告
  generate_quality_report: true
  generate_sensitivity_analysis: true
```

---

## ✅ 验收标准

### 功能完整性
- [ ] Notebook可一键运行
- [ ] 支持断点续传
- [ ] 进度可视化
- [ ] 自动错误处理

### 性能要求
- [ ] 支持100万+数据点
- [ ] 遵守GEE配额
- [ ] 速率限制管理
- [ ] 并发优化

### 易用性
- [ ] 最少用户干预
- [ ] 清晰的进度显示
- [ ] 详细的错误信息
- [ ] 自动状态保存

---

## 📅 实施计划

### 第1步：创建Notebook框架（今天）
- [ ] GEE_Extractor_Master.ipynb
- [ ] Session Manager
- [ ] 进度可视化

### 第2步：智能调度器（今天）
- [ ] GEETaskScheduler
- [ ] 配额管理
- [ ] 错误处理

### 第3步：完整流程（本周）
- [ ] 所有步骤实现
- [ ] 测试小数据集
- [ ] 测试大数据集

### 第4步：优化（下周）
- [ ] 性能优化
- [ ] 用户体验优化
- [ ] 文档完善

---

*设计日期：2026-03-12*
*优先级：最高*
