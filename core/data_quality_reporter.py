"""
数据质量报告生成器

自动生成详细的数据质量分析报告
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class DataQualityReporter:
    """
    数据质量报告生成器

    功能：
    1. 数据完整性检查
    2. 缺失值分析
    3. 异常值检测
    4. 统计摘要
    5. 可视化报告
    """

    def __init__(self, output_dir: str = './output'):
        """
        初始化报告生成器

        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_full_report(self,
                            data: pd.DataFrame,
                            report_name: str = 'data_quality_report',
                            include_plots: bool = True) -> Dict[str, Any]:
        """
        生成完整的数据质量报告

        Args:
            data: 要分析的数据
            report_name: 报告名称
            include_plots: 是否包含可视化图表

        Returns:
            dict: 包含所有质量指标的字典
        """
        print(f"\\n{'='*60}")
        print(f"📊 生成数据质量报告: {report_name}")
        print(f"{'='*60}")

        # 1. 基本信息统计
        basic_stats = self._analyze_basic_info(data)

        # 2. 缺失值分析
        missing_stats = self._analyze_missing_values(data)

        # 3. 异常值检测
        outlier_stats = self._detect_outliers(data)

        # 4. 数据类型分析
        type_stats = self._analyze_data_types(data)

        # 5. 统计摘要
        summary_stats = self._generate_summary(data)

        # 6. 相关性分析（仅数值列）
        correlation_stats = self._analyze_correlations(data)

        # 汇总所有结果
        report = {
            'report_name': report_name,
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'basic_info': basic_stats,
            'missing_values': missing_stats,
            'outliers': outlier_stats,
            'data_types': type_stats,
            'summary': summary_stats,
            'correlations': correlation_stats
        }

        # 保存报告
        self._save_report(report, report_name)

        # 生成可视化
        if include_plots:
            self._generate_plots(data, report_name)

        # 打印摘要
        self._print_summary(report)

        return report

    def _analyze_basic_info(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析基本信息"""
        return {
            'total_rows': len(data),
            'total_columns': len(data.columns),
            'memory_usage_mb': data.memory_usage(deep=True).sum() / 1024 / 1024,
            'column_names': list(data.columns)
        }

    def _analyze_missing_values(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析缺失值"""
        missing_counts = data.isnull().sum()
        missing_ratios = missing_counts / len(data)

        # 按列分类
        columns_no_missing = missing_counts[missing_counts == 0].index.tolist()
        columns_some_missing = missing_counts[(missing_counts > 0) & (missing_counts < len(data))].index.tolist()
        columns_all_missing = missing_counts[missing_counts == len(data)].index.tolist()

        return {
            'total_missing': missing_counts.sum(),
            'missing_ratio': missing_ratios.mean(),
            'columns_no_missing': columns_no_missing,
            'columns_some_missing': columns_some_missing,
            'columns_all_missing': columns_all_missing,
            'missing_by_column': missing_counts[missing_counts > 0].to_dict()
        }

    def _detect_outliers(self, data: pd.DataFrame) -> Dict[str, Any]:
        """检测异常值（仅数值列）"""
        outlier_info = {}

        numeric_cols = data.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            # 使用IQR方法检测异常值
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = data[(data[col] < lower_bound) | (data[col] > upper_bound)][col]

            outlier_info[col] = {
                'count': len(outliers),
                'ratio': len(outliers) / len(data),
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'outlier_values': outliers.tolist()[:10]  # 只保存前10个
            }

        return outlier_info

    def _analyze_data_types(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析数据类型"""
        type_counts = data.dtypes.value_counts().to_dict()

        type_info = {}
        for col in data.columns:
            dtype = str(data[col].dtype)
            unique_count = data[col].nunique()

            type_info[col] = {
                'dtype': dtype,
                'unique_values': unique_count,
                'is_numeric': pd.api.types.is_numeric_dtype(data[col])
            }

        return {
            'type_counts': type_counts,
            'column_details': type_info
        }

    def _generate_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """生成统计摘要"""
        numeric_data = data.select_dtypes(include=[np.number])

        if len(numeric_data.columns) > 0:
            return numeric_data.describe().to_dict()
        else:
            return {}

    def _analyze_correlations(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析相关性（仅数值列）"""
        numeric_data = data.select_dtypes(include=[np.number])

        if len(numeric_data.columns) < 2:
            return {'message': '需要至少2个数值列来计算相关性'}

        # 计算相关矩阵
        corr_matrix = numeric_data.corr()

        # 找出强相关的变量对
        strong_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:  # 强相关阈值
                    strong_correlations.append({
                        'var1': corr_matrix.columns[i],
                        'var2': corr_matrix.columns[j],
                        'correlation': corr_val
                    })

        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'strong_correlations': strong_correlations
        }

    def _save_report(self, report: Dict[str, Any], report_name: str):
        """保存报告到文件"""
        # 保存为JSON
        import json
        json_file = self.output_dir / f"{report_name}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        # 保存为Markdown
        md_file = self.output_dir / f"{report_name}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown_report(report))

        print(f"\\n💾 报告已保存:")
        print(f"   JSON: {json_file}")
        print(f"   Markdown: {md_file}")

    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """生成Markdown格式的报告"""
        md = f"""# {report['report_name']}

**生成时间**: {report['generation_time']}

---

## 📊 基本信息

- **总行数**: {report['basic_info']['total_rows']:,}
- **总列数**: {report['basic_info']['total_columns']}
- **内存使用**: {report['basic_info']['memory_usage_mb']:.2f} MB

---

## 🔍 缺失值分析

### 总体情况

- **总缺失值数**: {report['missing_values']['total_missing']:,}
- **缺失比例**: {report['missing_values']['missing_ratio']:.2%}

### 按列统计

#### 无缺失值 ({len(report['missing_values']['columns_no_missing'])} 列)
{', '.join(report['missing_values']['columns_no_missing'][:5])}
{'...' if len(report['missing_values']['columns_no_missing']) > 5 else ''}

#### 有缺失值 ({len(report['missing_values']['columns_some_missing'])} 列)
"""

        # 添加有缺失值的列详情
        for col, count in report['missing_values']['get('missing_by_column', {}).items():
            ratio = count / report['basic_info']['total_rows']
            md += f"- **{col}**: {count} ({ratio:.1%})\\n"

        md += f"""
#### 全部缺失 ({len(report['missing_values']['columns_all_missing'])} 列)
{', '.join(report['missing_values']['columns_all_missing']) if report['missing_values']['columns_all_missing'] else '无'}

---

## ⚠️ 异常值检测

"""

        # 添加异常值信息
        outlier_stats = report['outliers']
        if outlier_stats:
            for col, info in outlier_stats.items():
                md += f"### {col}\\n\\n"
                md += f"- **异常值数量**: {info['count']}\\n"
                md += f"- **异常值比例**: {info['ratio']:.2%}\\n"
                md += f"- **正常范围**: [{info['lower_bound']:.2f}, {info['upper_bound']:.2f}]\\n\\n"
        else:
            md += "数值列不足以进行异常值检测\\n\\n"

        md += """
---

## 📈 数据类型统计

"""

        # 添加数据类型信息
        for dtype, count in report['data_types']['type_counts'].items():
            md += f"- **{dtype}**: {count} 列\\n"

        md += """
---

## 📊 统计摘要

"""

        # 添加统计摘要
        summary = report.get('summary', {})
        if summary:
            for col, stats in summary.items():
                md += f"### {col}\\n\\n"
                for stat_name, stat_val in stats.items():
                    md += f"- **{stat_name}**: {stat_val:.4f}\\n"
                md += "\\n"
        else:
            md += "无数值列可生成统计摘要\\n\\n"

        md += """
---

## 🔗 相关性分析

"""

        # 添加强相关对
        strong_corr = report.get('correlations', {}).get('strong_correlations', [])
        if strong_corr:
            md += "### 强相关变量对 (|r| > 0.7)\\n\\n"
            for corr in strong_corr:
                md += f"- **{corr['var1']}** ↔ **{corr['var2']}**: r = {corr['correlation']:.3f}\\n"
        else:
            md += "无强相关变量对\\n"

        md += """
---

## 💡 建议

"""

        # 生成建议
        suggestions = self._generate_suggestions(report)
        for suggestion in suggestions:
            md += f"- {suggestion}\\n"

        md += """
---

*报告由 DataQualityReporter 自动生成*
"""

        return md

    def _generate_suggestions(self, report: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 缺失值建议
        missing_ratio = report['missing_values']['missing_ratio']
        if missing_ratio > 0.1:
            suggestions.append(f"⚠️ 数据缺失率较高({missing_ratio:.1%})，建议检查数据源或考虑填充策略")
        elif missing_ratio > 0:
            suggestions.append(f"✓ 数据有少量缺失({missing_ratio:.1%})，可以考虑插值填充")

        # 异常值建议
        total_outliers = sum(info['count'] for info in report['outliers'].values())
        if total_outliers > 0:
            suggestions.append(f"⚠️ 检测到{total_outliers}个异常值，建议验证这些数据点")

        # 数据类型建议
        if len(report['data_types']['type_counts']) > 3:
            suggestions.append("💡 数据类型较多，建议考虑统一数据类型以提升性能")

        # 内存建议
        memory_mb = report['basic_info']['memory_usage_mb']
        if memory_mb > 100:
            suggestions.append(f"💾 数据集较大({memory_mb:.1f}MB)，建议使用分块处理或优化数据类型")

        # 相关性建议
        strong_corr = report.get('correlations', {}).get('strong_correlations', [])
        if len(strong_corr) > 5:
            suggestions.append("🔗 发现多个强相关变量，考虑降维或特征选择")

        if not suggestions:
            suggestions.append("✓ 数据质量良好，无特殊问题")

        return suggestions

    def _generate_plots(self, data: pd.DataFrame, report_name: str):
        """生成可视化图表"""
        print("\\n📊 生成可视化图表...")

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 1. 缺失值图
        ax1 = axes[0, 0]
        missing_counts = data.isnull().sum()
        missing_counts = missing_counts[missing_counts > 0].sort_values(ascending=False)
        if len(missing_counts) > 0:
            missing_counts.plot(kind='bar', ax=ax1, color='coral')
            ax1.set_title('缺失值统计', fontweight='bold')
            ax1.set_xlabel('列名')
            ax1.set_ylabel('缺失值数量')
            ax1.tick_params(axis='x', rotation=45)
        else:
            ax1.text(0.5, 0.5, '无缺失值', ha='center', va='center', transform=ax1.transAxes)

        # 2. 数据类型分布
        ax2 = axes[0, 1]
        type_counts = data.dtypes.value_counts()
        type_counts.plot(kind='pie', ax=ax2, autopct='%1.1f%%', startangle=90)
        ax2.set_title('数据类型分布', fontweight='bold')
        ax2.set_ylabel('')

        # 3. 数值列分布（如果有）
        ax3 = axes[1, 0]
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # 选择前4个数值列
            plot_cols = numeric_cols[:min(4, len(numeric_cols))]
            for i, col in enumerate(plot_cols):
                data[col].plot(kind='kde', ax=ax3, label=col)
            ax3.set_title('数值列分布', fontweight='bold')
            ax3.set_xlabel('值')
            ax3.set_ylabel('密度')
            ax3.legend()
        else:
            ax3.text(0.5, 0.5, '无数值列', ha='center', va='center', transform=ax3.transAxes)

        # 4. 数据质量评分
        ax4 = axes[1, 1]
        scores = self._calculate_quality_scores(data)
        score_names = ['完整性', '无异常值', '数据类型一致性', '内存效率']
        colors = ['green' if s > 0.7 else 'orange' if s > 0.4 else 'red' for s in scores]
        ax4.bar(score_names, scores, color=colors, alpha=0.7)
        ax4.set_title('数据质量评分', fontweight='bold')
        ax4.set_ylabel('评分')
        ax4.set_ylim(0, 1)
        ax4.axhline(y=0.7, color='green', linestyle='--', alpha=0.5, label='良好')
        ax4.legend()

        plt.tight_layout()

        # 保存图表
        plot_file = self.output_dir / f"{report_name}_plots.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"   ✅ 图表已保存: {plot_file}")

    def _calculate_quality_scores(self, data: pd.DataFrame) -> List[float]:
        """计算数据质量评分"""
        scores = []

        # 1. 完整性评分
        completeness = 1 - (data.isnull().sum().sum() / (len(data) * len(data.columns)))
        scores.append(completeness)

        # 2. 无异常值评分
        numeric_data = data.select_dtypes(include=[np.number])
        if len(numeric_data.columns) > 0:
            total_outliers = 0
            total_values = len(numeric_data) * len(numeric_data.columns)
            for col in numeric_data.columns:
                Q1 = numeric_data[col].quantile(0.25)
                Q3 = numeric_data[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = numeric_data[(numeric_data[col] < Q1 - 1.5*IQR) | (numeric_data[col] > Q3 + 1.5*IQR)][col]
                total_outliers += len(outliers)
            outlier_score = 1 - (total_outliers / total_values if total_values > 0 else 0)
            scores.append(outlier_score)
        else:
            scores.append(1.0)  # 无数值列，满分

        # 3. 数据类型一致性评分
        type_variety = len(data.dtypes.unique())
        type_score = 1 - min((type_variety - 1) / 5, 1)  # 超过6种类型扣分
        scores.append(type_score)

        # 4. 内存效率评分
        memory_mb = data.memory_usage(deep=True).sum() / 1024 / 1024
        memory_score = 1 - min(memory_mb / 1000, 1)  # 超过1GB扣分
        scores.append(memory_score)

        return scores

    def _print_summary(self, report: Dict[str, Any]):
        """打印报告摘要"""
        print(f"\\n{'='*60}")
        print("📋 数据质量摘要")
        print(f"{'='*60}")

        basic_info = report['basic_info']
        print(f"\\n📊 基本信息:")
        print(f"   数据量: {basic_info['total_rows']:,} 行 × {basic_info['total_columns']} 列")
        print(f"   内存使用: {basic_info['memory_usage_mb']:.2f} MB")

        missing_info = report['missing_values']
        print(f"\\n🔍 缺失值:")
        print(f"   总缺失: {missing_info['total_missing']:,} ({missing_info['missing_ratio']:.2%})")
        print(f"   完整列: {len(missing_info['columns_no_missing'])}/{basic_info['total_columns']}")

        outlier_info = report['outliers']
        total_outliers = sum(info['count'] for info in outlier_info.values())
        print(f"\\n⚠️  异常值:")
        print(f"   总计: {total_outliers}")

        suggestions = self._generate_suggestions(report)
        print(f"\\n💡 建议:")
        for suggestion in suggestions:
            print(f"   {suggestion}")

        print(f"\\n{'='*60}")


# 使用示例
if __name__ == "__main__":
    # 创建测试数据
    import numpy as np
    test_data = pd.DataFrame({
        'A': np.random.randn(1000),
        'B': np.random.randn(1000) * 2,
        'C': np.random.rand(1000),
        'D': np.random.choice(['X', 'Y', 'Z'], 1000)
    })

    # 添加一些缺失值
    test_data.loc[0:10, 'A'] = np.nan

    # 生成报告
    reporter = DataQualityReporter(output_dir='./output')
    report = reporter.generate_full_report(test_data, report_name='test_quality')
