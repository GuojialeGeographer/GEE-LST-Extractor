# 🔧 故障排除指南

本文档提供常见问题的解决方案和调试技巧。

---

## 目录

- [环境问题](#环境问题)
- [认证问题](#认证问题)
- [网络问题](#网络问题)
- [数据问题](#数据问题)
- [GEE任务问题](#gee任务问题)
- [性能问题](#性能问题)
- [其他问题](#其他问题)

---

## 环境问题

### 问题1: ImportError: No module named 'ee'

**错误信息**：
```
ImportError: No module named 'ee'
```

**原因**：earthengine-api未安装

**解决方案**：
```bash
# 方法1：使用conda（推荐）
conda install -c conda-forge earthengine-api

# 方法2：使用pip
pip install earthengine-api

# 验证安装
python -c "import ee; print(ee.__version__)"
```

---

### 问题2: Python版本不兼容

**错误信息**：
```
SyntaxError: f-strings are not supported in Python 3.5
```

**原因**：Python版本过低

**解决方案**：
```bash
# 创建新环境，使用Python 3.8+
conda create -n geelst python=3.10
conda activate geelst

# 重新安装依赖
conda install -c conda-forge earthengine-api pandas numpy jupyter
```

---

### 问题3: Jupyter无法启动

**错误信息**：
```
jupyter: command not found
```

**解决方案**：
```bash
# 安装jupyter
conda install jupyter

# 启动
jupyter notebook

# 如果需要指定kernel
python -m ipykernel install --user --name geelst
```

---

## 认证问题

### 问题4: 未授权访问

**错误信息**：
```
Error: Access denied. Please authenticate first.
```

**解决方案**：
```python
import ee
ee.Authenticate()
```

按提示完成认证：
1. 点击链接
2. 登录Google账号
3. 复制授权码
4. 粘贴到终端

---

### 问题5: Token过期

**错误信息**：
```
Error: Token expired or invalid.
```

**解决方案**：
```python
# 强制重新认证
import ee
ee.Authenticate(force=True)

# 重新初始化
ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
```

---

### 问题6: 项目权限问题

**错误信息**：
```
Permission denied for project 'xxx'
```

**解决方案**：
```python
# 不指定project，使用默认
ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')

# 而不是
ee.Initialize(project='xxx', ...)  # 可能出错
```

---

## 网络问题

### 问题7: 连接超时

**错误信息**：
```
socket.timeout: timed out
Connection error
```

**原因**：未使用高流量API或网络不稳定

**解决方案**：
```python
# 使用高流量API
import ee
ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
```

**其他建议**：
- 检查网络连接
- 使用VPN（如果在海外）
- 稍后重试

---

### 问题8: SSL证书错误

**错误信息**：
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**解决方案**：
```bash
# 方法1：更新证书
conda install certifi

# 方法2：临时禁用SSL验证（不推荐）
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

---

### 问题9: 任务提交但不可见

**现象**：代码显示"任务已提交"，但GEE Tasks页面看不到

**可能原因**：
1. 认证token过期
2. 未使用高流量API
3. 项目权限问题
4. 浏览器缓存

**解决方案**：
```python
# 1. 重新认证
ee.Authenticate(force=True)
ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')

# 2. 提交测试任务
test_task = ee.batch.Export.table.toDrive(...)
test_task.start()

# 3. 立即检查GEE页面
# https://code.earthengine.google.com/
# 点击右上角Tasks按钮

# 4. 清除浏览器缓存后重试
```

---

## 数据问题

### 问题10: 缺少必需列

**错误信息**：
```
ValueError: 缺少必需列: ['lng', 'lat', 'create_time']
```

**解决方案**：
```python
# 检查数据列名
import pandas as pd
df = pd.read_csv('your_data.csv')
print(df.columns)

# 如果列名不同，重命名
df = df.rename(columns={
    'longitude': 'lng',
    'latitude': 'lat',
    'timestamp': 'create_time'
})

# 保存修正后的数据
df.to_csv('mobility_locations.csv', index=False)
```

---

### 问题11: 时间解析失败

**错误信息**：
```
ParserError: Unknown string format
```

**解决方案**：
```python
# 检查时间格式
import pandas as pd
df = pd.read_csv('your_data.csv')
print(df['create_time'].head())

# 手动指定格式
df['create_time'] = pd.to_datetime(
    df['create_time'],
    format='%Y-%m-%d %H:%M:%S'  # 根据实际格式调整
)

# 或者让pandas自动推断
df['create_time'] = pd.to_datetime(df['create_time'], errors='coerce')
```

---

### 问题12: 经纬度异常

**现象**：部分点的经纬度超出合理范围

**检查方法**：
```python
# 检查范围
print(f"经度范围: [{df['lng'].min()}, {df['lng'].max()}]")
print(f"纬度范围: [{df['lat'].min()}, {df['lat'].max()}]")

# 合理范围
lng_valid = (df['lng'] >= -180) & (df['lng'] <= 180)
lat_valid = (df['lat'] >= -90) & (df['lat'] <= 90)

# 删除异常值
df = df[lng_valid & lat_valid].copy()
print(f"删除后: {len(df)} 行")
```

---

## GEE任务问题

### 问题13: 任务失败 - Computation timed out

**错误信息**：
```
Error: Computation timed out
```

**原因**：批次过大或计算量过大

**解决方案**：
```python
# 减小批次大小
MAX_POINTS_PER_TASK = 3000  # 原来是5000

# 或者进一步减小
MAX_POINTS_PER_TASK = 2000

# 重新运行阶段2和阶段4
```

---

### 问题14: 任务失败 - Memory limit exceeded

**错误信息**：
```
Error: Memory limit exceeded
```

**解决方案**：
```python
# 减小批次大小
MAX_POINTS_PER_TASK = 2000

# 缩小region buffer
region = fc.geometry().bounds().buffer(3000)  # 原来是5000
```

---

### 问题15: 部分任务失败

**现象**：180个任务中，5-10个失败

**原因**：偶发性错误（网络波动、GEE负载等）

**解决方案**：
```python
# 阶段4会记录失败任务
print(failed_tasks)

# 手动重试失败的任务
for task in failed_tasks:
    # 提取参数
    year = task['year']
    month = task['month']
    # ... 重新提交该批次
```

---

### 问题16: 所有任务都失败

**可能原因**：
1. GEE服务故障
2. 认证问题
3. 数据格式错误
4. 算法错误

**诊断步骤**：
```python
# 1. 检查GEE状态
# 访问: https://earthengine.status.page/

# 2. 测试简单任务
import ee
ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')

# 创建简单测试
point = ee.Geometry.Point([116.4, 39.9])
feature = ee.Feature(point, {'name': 'test'})
fc = ee.FeatureCollection([feature])

task = ee.batch.Export.table.toDrive(
    collection=fc,
    description='TEST',
    folder='LST_Results',
    fileFormat='CSV'
)
task.start()

# 如果成功，说明GEE正常，检查数据和算法
```

---

## 性能问题

### 问题17: 处理速度慢

**现象**：任务提交后长时间不完成

**可能原因**：
1. GEE负载高
2. 批次过大
3. 区域过大

**优化建议**：
```python
# 1. 减小批次
MAX_POINTS_PER_TASK = 3000

# 2. 减小buffer
region = fc.geometry().bounds().buffer(3000)

# 3. 避开高峰时段
# 美国东部时间凌晨/清晨（北京时间下午/晚上）
```

---

### 问题18: 内存占用高

**现象**：Jupyter notebook占用大量内存

**解决方案**：
```python
# 定期清理变量
import gc
del df_large
gc.collect()

# 使用分块读取
for chunk in pd.read_csv('large_file.csv', chunksize=10000):
    process(chunk)
```

---

## 其他问题

### 问题19: 重复的grid_uid

**现象**：grid_uid不唯一

**检查**：
```python
# 检查唯一性
df_unique = pd.read_csv('temp/unique_grids.csv')
uid_count = df_unique['grid_uid'].nunique()
total_count = len(df_unique)

print(f"总行数: {total_count}")
print(f"唯一UID: {uid_count}")
print(f"重复: {total_count - uid_count}")

# 如果有重复，检查原因
duplicates = df_unique[df_unique.duplicated(subset=['grid_uid'], keep=False)]
print(duplicates)
```

**原因**：UUID版本错误或key包含冲突

**修复**：使用UUID5而非UUID4
```python
# 正确
uid = uuid.uuid5(uuid.NAMESPACE_DNS, key).hex[:12]

# 错误
uid = uuid.uuid4().hex[:12]  # 每次生成不同值
```

---

### 问题20: 最终数据LST全为NaN

**检查步骤**：
```python
# 1. 检查LST结果文件
import pandas as pd
from glob import glob

lst_files = glob('lst_results/*.csv')
for f in lst_files[:5]:
    df = pd.read_csv(f)
    print(f"{os.path.basename(f)}: {df['LST'].notna().sum()} 有效值")

# 2. 检查grid_uid匹配
df_lst = pd.read_csv('lst_results/some_file.csv')
df_raw = pd.read_csv('temp/raw_with_grid_uid.csv')

print(f"LST文件grid_uid数: {df_lst['grid_uid'].nunique()}")
print(f"原始数据grid_uid数: {df_raw['grid_uid'].nunique()}")

# 检查交集
lst_uids = set(df_lst['grid_uid'])
raw_uids = set(df_raw['grid_uid'])
print(f"交集: {len(lst_uids & raw_uids)}")
print(f"仅在LST中: {len(lst_uids - raw_uids)}")
print(f"仅在原始中: {len(raw_uids - lst_uids)}")
```

---

## 获取帮助

### 官方资源

1. **Google Earth Engine**
   - 文档: https://developers.google.com/earth-engine
   - 社区: https://developers.google.com/earth-engine/community
   - 状态页: https://earthengine.status.page/

2. **Landsat**
   - USGS: https://www.usgs.gov/land-resources/nli/landsat
   - 数据获取: https://earthexplorer.usgs.gov/

3. **Python**
   - Pandas: https://pandas.pydata.org/docs/
   - Earth Engine API: https://pypi.org/project/earthengine-api/

### 提交Issue

如果以上方案都无法解决问题，请提交Issue：

```
https://github.com/yourusername/GEE-LST-Extractor/issues
```

**请提供以下信息**：

1. **环境信息**
   ```bash
   python --version
   conda list | grep -E "ee|pandas|numpy"
   ```

2. **错误信息**
   - 完整错误堆栈
   - 错误发生的步骤

3. **数据信息**
   - 数据量（行数）
   - 列名
   - 时间范围

4. **已尝试的解决方案**

---

## 预防性措施

### 定期备份

```bash
# 备份temp文件夹
cp -r temp temp_backup_$(date +%Y%m%d)

# 备份batch_list
cp temp/batch_list.csv batch_list_backup.csv
```

### 检查点保存

```python
# 保存进度
import json

progress = {
    'last_completed_batch': 50,
    'total_batches': 186,
    'success_count': 50,
    'failed_tasks': []
}

with open('progress.json', 'w') as f:
    json.dump(progress, f)

# 恢复进度
with open('progress.json', 'r') as f:
    progress = json.load(f)

# 从失败点继续
start_from = progress['last_completed_batch'] + 1
```

### 日志记录

```python
import logging

logging.basicConfig(
    filename='lst_extraction.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info(f"开始处理批次 {batch_id}")
try:
    # 处理逻辑
    logging.info(f"批次 {batch_id} 完成")
except Exception as e:
    logging.error(f"批次 {batch_id} 失败: {str(e)}")
```

---

*本文档随项目更新。如有新的问题或解决方案，欢迎补充。*
