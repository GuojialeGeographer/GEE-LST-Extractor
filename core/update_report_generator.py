"""
更新报告生成器 - 生成详细的HTML更新报告
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class UpdateReportGenerator:
    """
    更新报告生成器

    生成美观、详细的HTML更新报告
    """

    def __init__(self, template_dir: str = 'templates'):
        """
        初始化

        参数:
        -------
        template_dir : str
            模板目录
        """
        self.template_dir = Path(template_dir)

    def generate_html_report(self, update_data: Dict[str, Any],
                           output_path: str = 'output/update_report.html') -> str:
        """
        生成HTML报告

        参数:
        -------
        update_data : dict
            更新数据
        output_path : str
            输出路径

        返回:
        -------
        str
            生成的HTML
        """
        html_content = self._build_html_report(update_data)

        # 保存报告
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_file)

    def _build_html_report(self, data: Dict[str, Any]) -> str:
        """构建HTML报告"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据集更新报告 - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}

        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-left: 10px;
            border-left: 4px solid #3498db;
        }}

        h3 {{
            color: #555;
            margin-top: 20px;
            margin-bottom: 10px;
        }}

        .summary {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }}

        .summary-item {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}

        .summary-item .value {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }}

        .summary-item .label {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 5px;
        }}

        .update-card {{
            background: #f9f9f9;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
        }}

        .update-card.success {{
            border-left-color: #27ae60;
        }}

        .update-card.warning {{
            border-left-color: #f39c12;
        }}

        .update-card.error {{
            border-left-color: #e74c3c;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            margin-left: 10px;
        }}

        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}

        .badge-warning {{
            background: #fff3cd;
            color: #856404;
        }}

        .badge-error {{
            background: #f8d7da;
            color: #721c24;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        th {{
            background: #34495e;
            color: white;
            font-weight: 600;
        }}

        tr:hover {{
            background: #f5f5f5;
        }}

        .version-change {{
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
        }}

        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}

        .timestamp {{
            color: #95a5a6;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 数据集更新报告</h1>
        <p class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        {self._generate_summary_section(data)}

        {self._generate_updates_section(data)}

        {self._generate_validation_section(data)}

        {self._generate_history_section(data)}

        <div class="footer">
            <p>LST数据提取工具 - 智能更新系统</p>
            <p>报告版本: 1.0 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_summary_section(self, data: Dict[str, Any]) -> str:
        """生成摘要部分"""
        total_updates = len(data.get('updates', []))
        successful = sum(1 for u in data.get('updates', []) if u.get('status') == 'completed')
        failed = total_updates - successful

        return f"""
        <div class="summary">
            <h2>📊 更新摘要</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="value">{total_updates}</div>
                    <div class="label">总更新数</div>
                </div>
                <div class="summary-item">
                    <div class="value" style="color: #27ae60;">{successful}</div>
                    <div class="label">成功</div>
                </div>
                <div class="summary-item">
                    <div class="value" style="color: #e74c3c;">{failed}</div>
                    <div class="label">失败</div>
                </div>
            </div>
        </div>
        """

    def _generate_updates_section(self, data: Dict[str, Any]) -> str:
        """生成更新详情部分"""
        updates = data.get('updates', [])

        if not updates:
            return """
            <div class="summary">
                <h2>ℹ️ 无可用更新</h2>
                <p>所有数据源已是最新版本。</p>
            </div>
            """

        html = """
        <h2>🔄 更新详情</h2>
        """

        for update in updates:
            data_type = update.get('data_type', 'Unknown')
            old_version = update.get('current_version', 'N/A')
            new_version = update.get('recommended_version', 'N/A')
            reason = update.get('reason', '')

            status_class = 'success' if update.get('status') == 'completed' else 'error'
            status_badge = 'success' if update.get('status') == 'completed' else 'error'
            status_text = '✅ 成功' if update.get('status') == 'completed' else '❌ 失败'

            html += f"""
            <div class="update-card {status_class}">
                <h3>{data_type} <span class="badge badge-{status_badge}">{status_text}</span></h3>
                <p><strong>版本变化:</strong> <span class="version-change">{old_version} → {new_version}</span></p>
                <p><strong>原因:</strong> {reason}</p>
                <p><strong>数据集:</strong> {update.get('recommended', 'N/A')}</p>
            </div>
            """

        return html

    def _generate_validation_section(self, data: Dict[str, Any]) -> str:
        """生成验证部分"""
        validation = data.get('validation', {})

        if not validation:
            return ''

        html = '<h2>✅ 验证结果</h2>'

        if validation.get('valid'):
            html += '<div class="update-card success"><p>所有数据源验证通过！</p></div>'
        else:
            html += '<div class="update-card error"><p>⚠️ 验证失败，请检查以下错误：</p></div>'

        if validation.get('errors'):
            html += '<h3>错误</h3><ul>'
            for error in validation['errors']:
                html += f'<li style="color: #e74c3c;">{error}</li>'
            html += '</ul>'

        if validation.get('warnings'):
            html += '<h3>警告</h3><ul>'
            for warning in validation['warnings']:
                html += f'<li style="color: #f39c12;">{warning}</li>'
            html += '</ul>'

        return html

    def _generate_history_section(self, data: Dict[str, Any]) -> str:
        """生成历史记录部分"""
        history = data.get('version_history', {})

        if not history:
            return ''

        html = '<h2>📜 版本历史</h2>'

        for data_type, versions in history.items():
            if not versions:
                continue

            html += f'<h3>{data_type}</h3>'
            html += '<table>'
            html += '<thead><tr><th>时间</th><th>集合</th><th>版本</th></tr></thead>'
            html += '<tbody>'

            for version in versions[-5:]:  # 只显示最近5条
                timestamp = version.get('timestamp', 'N/A')
                collection = version.get('collection_id', 'N/A')
                version_num = collection.split('/')[1] if '/' in collection else 'N/A'

                html += f'''
                <tr>
                    <td>{timestamp}</td>
                    <td>{collection}</td>
                    <td>{version_num}</td>
                </tr>
                '''

            html += '</tbody></table>'

        return html

    def generate_json_report(self, update_data: Dict[str, Any],
                            output_path: str = 'output/update_report.json') -> str:
        """
        生成JSON报告

        参数:
        -------
        update_data : dict
            更新数据
        output_path : str
            输出路径

        返回:
        -------
        str
            生成的JSON文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        report = {
            'generated_at': datetime.now().isoformat(),
            'report_type': 'dataset_update',
            'data': update_data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return str(output_file)

    def generate_markdown_report(self, update_data: Dict[str, Any],
                                output_path: str = 'output/update_report.md') -> str:
        """
        生成Markdown报告

        参数:
        -------
        update_data : dict
            更新数据
        output_path : str
            输出路径

        返回:
        -------
        str
            生成的Markdown文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        md_content = self._build_markdown_report(update_data)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return str(output_file)

    def _build_markdown_report(self, data: Dict[str, Any]) -> str:
        """构建Markdown报告"""
        md = f"""# 🤖 数据集更新报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 更新摘要

"""

        updates = data.get('updates', [])
        total = len(updates)
        successful = sum(1 for u in updates if u.get('status') == 'completed')
        failed = total - successful

        md += f"""- **总更新数**: {total}
- **成功**: {successful}
- **失败**: {failed}

---

## 🔄 更新详情

"""

        for update in updates:
            data_type = update.get('data_type', 'Unknown')
            old_version = update.get('current_version', 'N/A')
            new_version = update.get('recommended_version', 'N/A')
            status = '✅ 成功' if update.get('status') == 'completed' else '❌ 失败'

            md += f"""### {data_type} {status}

- **版本变化**: `{old_version}` → `{new_version}`
- **原因**: {update.get('reason', 'N/A')}
- **数据集**: {update.get('recommended', 'N/A')}

---

"""

        # 添加验证结果
        validation = data.get('validation', {})
        if validation:
            md += """## ✅ 验证结果

"""

            if validation.get('valid'):
                md += "✅ 所有数据源验证通过！\n\n"
            else:
                md += "⚠️ 验证失败\n\n"

                if validation.get('errors'):
                    md += "### 错误\n"
                    for error in validation['errors']:
                        md += f"- {error}\n"
                    md += "\n"

                if validation.get('warnings'):
                    md += "### 警告\n"
                    for warning in validation['warnings']:
                        md += f"- {warning}\n"
                    md += "\n"

        md += f"""
---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*LST数据提取工具 - 智能更新系统 v1.0*
"""

        return md


# 便捷函数
def generate_all_reports(update_data: Dict[str, Any],
                        output_dir: str = 'output') -> Dict[str, str]:
    """
    生成所有格式的报告

    参数:
    -------
    update_data : dict
        更新数据
    output_dir : str
        输出目录

    返回:
    -------
    dict
        生成的报告路径
    """
    generator = UpdateReportGenerator()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_path = Path(output_dir) / f'update_report_{timestamp}'

    reports = {}

    # 生成HTML报告
    reports['html'] = generator.generate_html_report(
        update_data,
        str(base_path.with_suffix('.html'))
    )

    # 生成JSON报告
    reports['json'] = generator.generate_json_report(
        update_data,
        str(base_path.with_suffix('.json'))
    )

    # 生成Markdown报告
    reports['markdown'] = generator.generate_markdown_report(
        update_data,
        str(base_path.with_suffix('.md'))
    )

    return reports


# 使用示例
if __name__ == '__main__':
    # 示例数据
    sample_data = {
        'updates': [
            {
                'data_type': 'LST',
                'current_version': '006',
                'recommended_version': '061',
                'current': 'MODIS/006/MOD11A2',
                'recommended': 'MODIS/061/MOD11A2',
                'reason': '推荐使用版本061，这是最新的稳定版本',
                'status': 'completed'
            },
            {
                'data_type': 'NDVI',
                'current_version': '006',
                'recommended_version': '061',
                'current': 'MODIS/006/MOD13Q1',
                'recommended': 'MODIS/061/MOD13Q1',
                'reason': '推荐使用版本061，这是最新的稳定版本',
                'status': 'completed'
            }
        ],
        'validation': {
            'valid': True,
            'errors': [],
            'warnings': []
        },
        'version_history': {
            'LST': [
                {
                    'collection_id': 'MODIS/006/MOD11A2',
                    'timestamp': '2026-01-01T00:00:00',
                    'metadata': {}
                },
                {
                    'collection_id': 'MODIS/061/MOD11A2',
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {}
                }
            ]
        }
    }

    # 生成所有报告
    reports = generate_all_reports(sample_data)

    print("✅ 报告生成完成:")
    for format_type, path in reports.items():
        print(f"  {format_type.upper()}: {path}")
