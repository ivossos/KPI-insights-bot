import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import json

from ..models import KPIResult, KPIDefinition
from ...monitoring.logger import logger


class ChartGenerator:
    def __init__(self):
        self.color_palette = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff9500',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }
        
        self.chart_theme = {
            'background_color': '#1a1a1a',
            'paper_color': '#2d2d2d',
            'text_color': '#ffffff',
            'grid_color': '#404040',
            'accent_color': '#ffd700'
        }

    def generate_chart_data(self, kpi_results: List[KPIResult]) -> Dict[str, Any]:
        try:
            if not kpi_results:
                return {}
            
            if len(kpi_results) == 1:
                return self._generate_single_kpi_chart(kpi_results[0])
            else:
                return self._generate_multi_kpi_chart(kpi_results)
                
        except Exception as e:
            logger.error(f"Failed to generate chart data: {e}")
            return {}

    def _generate_single_kpi_chart(self, kpi_result: KPIResult) -> Dict[str, Any]:
        chart_data = {
            'type': 'gauge',
            'data': self._create_gauge_chart(kpi_result),
            'layout': self._get_chart_layout(f"{kpi_result.name} Performance")
        }
        
        if kpi_result.variance_py is not None or kpi_result.variance_plan is not None:
            chart_data['variance_chart'] = self._create_variance_chart(kpi_result)
        
        return chart_data

    def _generate_multi_kpi_chart(self, kpi_results: List[KPIResult]) -> Dict[str, Any]:
        return {
            'type': 'bar',
            'data': self._create_bar_chart(kpi_results),
            'layout': self._get_chart_layout("KPI Comparison"),
            'variance_chart': self._create_multi_variance_chart(kpi_results)
        }

    def _create_gauge_chart(self, kpi_result: KPIResult) -> Dict[str, Any]:
        value = kpi_result.value
        
        if kpi_result.unit == 'percentage':
            max_value = 100
            threshold_good = 80
            threshold_warning = 60
        else:
            max_value = value * 1.5 if value > 0 else 100
            threshold_good = value * 1.2 if value > 0 else 80
            threshold_warning = value * 0.8 if value > 0 else 60
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': kpi_result.name},
            delta={'reference': threshold_good},
            gauge={
                'axis': {'range': [None, max_value]},
                'bar': {'color': self.color_palette['primary']},
                'steps': [
                    {'range': [0, threshold_warning], 'color': self.color_palette['danger']},
                    {'range': [threshold_warning, threshold_good], 'color': self.color_palette['warning']},
                    {'range': [threshold_good, max_value], 'color': self.color_palette['success']}
                ],
                'threshold': {
                    'line': {'color': self.color_palette['dark'], 'width': 4},
                    'thickness': 0.75,
                    'value': threshold_good
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor=self.chart_theme['paper_color'],
            font={'color': self.chart_theme['text_color']},
            height=400
        )
        
        return fig.to_dict()

    def _create_variance_chart(self, kpi_result: KPIResult) -> Dict[str, Any]:
        variances = []
        labels = []
        colors = []
        
        if kpi_result.variance_py is not None:
            variances.append(kpi_result.variance_py)
            labels.append('vs Prior Year')
            colors.append(self.color_palette['primary'])
        
        if kpi_result.variance_plan is not None:
            variances.append(kpi_result.variance_plan)
            labels.append('vs Plan')
            colors.append(self.color_palette['secondary'])
        
        if kpi_result.variance_fx_neutral is not None:
            variances.append(kpi_result.variance_fx_neutral)
            labels.append('FX Neutral')
            colors.append(self.color_palette['info'])
        
        fig = go.Figure(data=[
            go.Bar(
                x=labels,
                y=variances,
                marker_color=colors,
                text=[f"{v:,.0f}" for v in variances],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title=f"{kpi_result.name} - Variance Analysis",
            xaxis_title="Comparison Type",
            yaxis_title=f"Variance ({kpi_result.currency or kpi_result.unit})",
            paper_bgcolor=self.chart_theme['paper_color'],
            plot_bgcolor=self.chart_theme['background_color'],
            font={'color': self.chart_theme['text_color']},
            height=300
        )
        
        return fig.to_dict()

    def _create_bar_chart(self, kpi_results: List[KPIResult]) -> Dict[str, Any]:
        names = [result.name for result in kpi_results]
        values = [result.value for result in kpi_results]
        
        fig = go.Figure(data=[
            go.Bar(
                x=names,
                y=values,
                marker_color=self.color_palette['primary'],
                text=[f"{v:,.0f}" for v in values],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="KPI Overview",
            xaxis_title="KPIs",
            yaxis_title="Value",
            paper_bgcolor=self.chart_theme['paper_color'],
            plot_bgcolor=self.chart_theme['background_color'],
            font={'color': self.chart_theme['text_color']},
            height=400
        )
        
        return fig.to_dict()

    def _create_multi_variance_chart(self, kpi_results: List[KPIResult]) -> Dict[str, Any]:
        data = []
        
        for result in kpi_results:
            if result.variance_py is not None:
                data.append({
                    'KPI': result.name,
                    'Variance_Type': 'vs Prior Year',
                    'Value': result.variance_py
                })
            
            if result.variance_plan is not None:
                data.append({
                    'KPI': result.name,
                    'Variance_Type': 'vs Plan',
                    'Value': result.variance_plan
                })
        
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        fig = px.bar(
            df,
            x='KPI',
            y='Value',
            color='Variance_Type',
            barmode='group',
            title='Variance Analysis Comparison'
        )
        
        fig.update_layout(
            paper_bgcolor=self.chart_theme['paper_color'],
            plot_bgcolor=self.chart_theme['background_color'],
            font={'color': self.chart_theme['text_color']},
            height=400
        )
        
        return fig.to_dict()

    def _get_chart_layout(self, title: str) -> Dict[str, Any]:
        return {
            'title': {
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': self.chart_theme['text_color']}
            },
            'paper_bgcolor': self.chart_theme['paper_color'],
            'plot_bgcolor': self.chart_theme['background_color'],
            'font': {'color': self.chart_theme['text_color']},
            'xaxis': {
                'gridcolor': self.chart_theme['grid_color'],
                'color': self.chart_theme['text_color']
            },
            'yaxis': {
                'gridcolor': self.chart_theme['grid_color'],
                'color': self.chart_theme['text_color']
            }
        }

    def generate_trend_chart(self, historical_data: List[Dict[str, Any]], kpi_name: str) -> Dict[str, Any]:
        try:
            if not historical_data:
                return {}
            
            df = pd.DataFrame(historical_data)
            df['period'] = pd.to_datetime(df['period'])
            df = df.sort_values('period')
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['period'],
                y=df['value'],
                mode='lines+markers',
                name=kpi_name,
                line=dict(color=self.color_palette['primary'], width=3),
                marker=dict(size=8)
            ))
            
            if 'benchmark' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['period'],
                    y=df['benchmark'],
                    mode='lines',
                    name='Benchmark',
                    line=dict(color=self.color_palette['secondary'], dash='dash')
                ))
            
            fig.update_layout(
                title=f"{kpi_name} - Historical Trend",
                xaxis_title="Period",
                yaxis_title="Value",
                paper_bgcolor=self.chart_theme['paper_color'],
                plot_bgcolor=self.chart_theme['background_color'],
                font={'color': self.chart_theme['text_color']},
                height=400,
                hovermode='x unified'
            )
            
            return fig.to_dict()
            
        except Exception as e:
            logger.error(f"Failed to generate trend chart: {e}")
            return {}

    def generate_waterfall_chart(self, breakdown_data: List[Dict[str, Any]], kpi_name: str) -> Dict[str, Any]:
        try:
            if not breakdown_data:
                return {}
            
            categories = [item['category'] for item in breakdown_data]
            values = [item['value'] for item in breakdown_data]
            
            fig = go.Figure(go.Waterfall(
                name=kpi_name,
                orientation="v",
                measure=["relative"] * (len(values) - 1) + ["total"],
                x=categories,
                textposition="outside",
                text=[f"{v:,.0f}" for v in values],
                y=values,
                connector={"line": {"color": self.chart_theme['grid_color']}},
                increasing={"marker": {"color": self.color_palette['success']}},
                decreasing={"marker": {"color": self.color_palette['danger']}},
                totals={"marker": {"color": self.color_palette['primary']}}
            ))
            
            fig.update_layout(
                title=f"{kpi_name} - Breakdown Analysis",
                xaxis_title="Components",
                yaxis_title="Value",
                paper_bgcolor=self.chart_theme['paper_color'],
                plot_bgcolor=self.chart_theme['background_color'],
                font={'color': self.chart_theme['text_color']},
                height=400
            )
            
            return fig.to_dict()
            
        except Exception as e:
            logger.error(f"Failed to generate waterfall chart: {e}")
            return {}

    def generate_dashboard_summary(self, kpi_results: List[KPIResult]) -> Dict[str, Any]:
        try:
            summary_data = []
            
            for result in kpi_results:
                status = self._determine_status(result)
                
                summary_data.append({
                    'name': result.name,
                    'value': result.value,
                    'unit': result.unit,
                    'currency': result.currency,
                    'status': status,
                    'variance_py': result.variance_py,
                    'variance_plan': result.variance_plan,
                    'trend': self._determine_trend(result)
                })
            
            return {
                'summary_cards': summary_data,
                'overview_chart': self._create_overview_chart(kpi_results),
                'status_distribution': self._create_status_chart(summary_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard summary: {e}")
            return {}

    def _determine_status(self, result: KPIResult) -> str:
        if result.variance_plan is not None:
            variance_pct = abs(result.variance_plan) / result.value if result.value != 0 else 0
            if variance_pct > 0.1:
                return "critical"
            elif variance_pct > 0.05:
                return "warning"
            else:
                return "good"
        
        return "neutral"

    def _determine_trend(self, result: KPIResult) -> str:
        if result.variance_py is not None:
            if result.variance_py > 0:
                return "up"
            elif result.variance_py < 0:
                return "down"
        
        return "flat"

    def _create_overview_chart(self, kpi_results: List[KPIResult]) -> Dict[str, Any]:
        return self._create_bar_chart(kpi_results)

    def _create_status_chart(self, summary_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        status_counts = {}
        for item in summary_data:
            status = item['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        fig = go.Figure(data=[go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=0.4,
            marker=dict(colors=[
                self.color_palette['success'] if status == 'good' else
                self.color_palette['warning'] if status == 'warning' else
                self.color_palette['danger'] if status == 'critical' else
                self.color_palette['info']
                for status in status_counts.keys()
            ])
        )])
        
        fig.update_layout(
            title="KPI Status Distribution",
            paper_bgcolor=self.chart_theme['paper_color'],
            font={'color': self.chart_theme['text_color']},
            height=300
        )
        
        return fig.to_dict()