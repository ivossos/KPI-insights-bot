#!/usr/bin/env python3
"""
Standalone Streamlit Dashboard for IA Fiscal Capivari
Optimized for Replit environment
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
import os

# Configure Streamlit page
st.set_page_config(
    page_title="IA Fiscal Capivari",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2a5298;
        margin: 0.5rem 0;
    }
    .alert-critical {
        border-left-color: #dc3545;
        background: #fff5f5;
    }
    .alert-medium {
        border-left-color: #ffc107;
        background: #fffdf5;
    }
    .alert-low {
        border-left-color: #28a745;
        background: #f8fff8;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main dashboard function"""

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ IA Fiscal Capivari</h1>
        <p>Sistema de Monitoramento e Alertas para Gastos Municipais</p>
        <small>Dashboard ativo - {}</small>
    </div>
    """.format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")), unsafe_allow_html=True)

    # Check if this is running in development mode
    is_replit = os.environ.get('REPL_ID') is not None

    # Sidebar navigation
    with st.sidebar:
        st.title("📋 Menu")

        if is_replit:
            st.success("🟢 Executando no Replit")

        page = st.selectbox(
            "Navegação:",
            ["Dashboard Principal", "Alertas Ativos", "Análise de Gastos", "Relatórios", "Configurações"],
            index=0
        )

        st.markdown("---")

        # Quick stats in sidebar
        st.markdown("### 📊 Resumo Rápido")
        st.metric("Alertas Hoje", "12", "+3")
        st.metric("Valor Analisado", "R$ 2.1M", "+15%")
        st.metric("Eficiência", "85%", "+2%")

        st.markdown("---")

        # Status indicators
        st.markdown("### 🟢 Status do Sistema")
        st.success("✅ Dashboard: Online")
        st.success("✅ Dados: Simulados")
        st.info("ℹ️ Modo: Demonstração")

    # Main content based on selected page
    if page == "Dashboard Principal":
        show_main_dashboard()
    elif page == "Alertas Ativos":
        show_alerts_page()
    elif page == "Análise de Gastos":
        show_spending_analysis()
    elif page == "Relatórios":
        show_reports_page()
    elif page == "Configurações":
        show_settings_page()

def show_main_dashboard():
    """Main dashboard page"""

    # Key performance indicators
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📢 Total de Alertas",
            value="156",
            delta="12 novos hoje"
        )

    with col2:
        st.metric(
            label="⚠️ Alertas Críticos", 
            value="23",
            delta="5 pendentes"
        )

    with col3:
        st.metric(
            label="💰 Valor Investigado",
            value="R$ 3.2M",
            delta="↑ 18% vs mês anterior"
        )

    with col4:
        st.metric(
            label="🎯 Taxa de Precisão",
            value="89%",
            delta="↑ 3% otimização IA"
        )

    st.markdown("---")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Tendência de Alertas (Últimos 30 dias)")

        # Generate sample data for alerts trend
        dates = pd.date_range(start=datetime.now() - timedelta(days=29), end=datetime.now(), freq='D')
        values = [8, 12, 6, 15, 9, 18, 11, 7, 14, 10, 16, 13, 5, 19, 8, 12, 15, 9, 11, 17, 6, 13, 10, 14, 7, 16, 12, 8, 15, 11]

        df_trend = pd.DataFrame({
            'Data': dates,
            'Alertas': values
        })

        fig_trend = px.line(
            df_trend, 
            x='Data', 
            y='Alertas',
            title="Alertas por Dia"
        )
        fig_trend.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        st.subheader("🎯 Distribuição por Tipo de Alerta")

        alert_types = pd.DataFrame({
            'Tipo': ['Sobrepreço', 'Fracionamento', 'Concentração', 'Emergência', 'Direcionamento'],
            'Quantidade': [45, 38, 28, 25, 20]
        })

        fig_pie = px.pie(
            alert_types, 
            values='Quantidade', 
            names='Tipo',
            title="Tipos de Alertas"
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Recent alerts table
    st.subheader("🚨 Alertas Recentes")

    recent_alerts = pd.DataFrame({
        'ID': ['#2024-001', '#2024-002', '#2024-003', '#2024-004', '#2024-005'],
        'Tipo': ['Sobrepreço', 'Fracionamento', 'Concentração', 'Emergência', 'Direcionamento'],
        'Descrição': [
            'Material de escritório 45% acima do preço médio de mercado',
            'Possível fracionamento em compras de combustível',
            'Alta concentração de contratos com fornecedor XYZ Ltda',
            'Múltiplas emergências de TI do mesmo fornecedor',
            'Indícios de direcionamento em licitação de obras'
        ],
        'Risco': [9, 7, 8, 6, 9],
        'Valor': ['R$ 125.000', 'R$ 89.500', 'R$ 234.000', 'R$ 45.000', 'R$ 678.000'],
        'Data': ['18/01/2024', '18/01/2024', '17/01/2024', '17/01/2024', '16/01/2024'],
        'Status': ['🔴 Crítico', '🟡 Médio', '🔴 Crítico', '🟡 Médio', '🔴 Crítico']
    })

    st.dataframe(
        recent_alerts,
        use_container_width=True,
        hide_index=True
    )

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Atualizar Dados", type="primary"):
            st.success("Dados atualizados!")
            time.sleep(1)
            st.rerun()

    with col2:
        if st.button("📊 Gerar Relatório"):
            st.info("Relatório sendo gerado...")

    with col3:
        if st.button("🔔 Verificar Notificações"):
            st.info("Verificando notificações...")

def show_alerts_page():
    """Alerts management page"""

    st.subheader("🚨 Gestão de Alertas")

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        alert_type = st.selectbox(
            "Tipo de Alerta:",
            ["Todos", "Sobrepreço", "Fracionamento", "Concentração", "Emergência", "Direcionamento"]
        )

    with col2:
        risk_level = st.selectbox(
            "Nível de Risco:",
            ["Todos", "Alto (8-10)", "Médio (5-7)", "Baixo (1-4)"]
        )

    with col3:
        status = st.selectbox(
            "Status:",
            ["Todos", "Pendente", "Em Análise", "Investigado", "Arquivado"]
        )

    with col4:
        date_range = st.selectbox(
            "Período:",
            ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Este ano"]
        )

    if st.button("🔍 Aplicar Filtros", type="primary"):
        st.success("Filtros aplicados com sucesso!")

    st.markdown("---")

    # Sample detailed alerts
    detailed_alerts = pd.DataFrame({
        'ID': [f'#2024-{str(i).zfill(3)}' for i in range(1, 11)],
        'Tipo': ['Sobrepreço', 'Fracionamento', 'Concentração'] * 4 + ['Emergência'],
        'Risco': [9, 7, 8, 6, 9, 5, 8, 7, 9, 6],
        'Valor': [f'R$ {(i*15000 + 10000):,.0f}' for i in range(1, 11)],
        'Fornecedor': [f'Empresa {chr(65+i%10)} Ltda' for i in range(10)],
        'Data': [(datetime.now() - timedelta(days=i)).strftime('%d/%m/%Y') for i in range(10)]
    })

    st.dataframe(detailed_alerts, use_container_width=True, hide_index=True)

def show_spending_analysis():
    """Spending analysis page"""

    st.subheader("💰 Análise de Gastos Municipais")

    # Summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Gasto Total Analisado", "R$ 12.5M", "↑ 8% vs período anterior")

    with col2:
        st.metric("Economia Identificada", "R$ 485K", "↑ 23% otimização")

    with col3:
        st.metric("Contratos Analisados", "1,247", "+156 este mês")

    st.markdown("---")

    # Spending by category
    categories = pd.DataFrame({
        'Categoria': ['Material de Escritório', 'Combustível', 'Obras', 'Serviços TI', 'Medicina', 'Educação'],
        'Valor': [1250000, 2300000, 3200000, 890000, 2100000, 2760000],
        'Alertas': [25, 18, 12, 15, 8, 22]
    })

    col1, col2 = st.columns(2)

    with col1:
        fig_cat_spending = px.bar(
            categories,
            x='Categoria',
            y='Valor',
            title="Gastos por Categoria"
        )
        fig_cat_spending.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig_cat_spending, use_container_width=True)

    with col2:
        fig_cat_alerts = px.scatter(
            categories,
            x='Valor',
            y='Alertas',
            size='Valor',
            hover_name='Categoria',
            title="Relação Gastos vs Alertas"
        )
        fig_cat_alerts.update_layout(height=400)
        st.plotly_chart(fig_cat_alerts, use_container_width=True)

def show_reports_page():
    """Reports page"""

    st.subheader("📋 Relatórios e Exportações")

    # Report generation
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Gerar Relatório")

        report_type = st.selectbox(
            "Tipo de Relatório:",
            ["Resumo Executivo", "Alertas Detalhados", "Análise de Fornecedores", "Gastos por Categoria", "Relatório Completo"]
        )

        date_start = st.date_input("Data Inicial:", value=datetime.now() - timedelta(days=30))
        date_end = st.date_input("Data Final:", value=datetime.now())

        format_type = st.selectbox("Formato:", ["PDF", "Excel", "CSV"])

        if st.button("📄 Gerar Relatório", type="primary"):
            with st.spinner("Gerando relatório..."):
                time.sleep(2)  # Simulate processing
            st.success(f"Relatório {report_type} gerado com sucesso!")

    with col2:
        st.markdown("### 📈 Relatórios Rápidos")

        if st.button("📊 Dashboard Executivo"):
            st.info("Gerando dashboard executivo...")

        if st.button("🚨 Alertas Críticos"):
            st.info("Compilando alertas críticos...")

        if st.button("💰 Resumo Financeiro"):
            st.info("Processando resumo financeiro...")

def show_settings_page():
    """Settings page"""

    st.subheader("⚙️ Configurações do Sistema")

    tabs = st.tabs(["🔧 Alertas", "👥 Usuários", "📧 Notificações", "🔐 Segurança"])

    with tabs[0]:
        st.markdown("### 🎯 Configuração de Alertas")

        col1, col2 = st.columns(2)

        with col1:
            st.number_input("Limite Sobrepreço (%)", min_value=1, max_value=100, value=25)
            st.number_input("Valor Mínimo Fracionamento (R$)", min_value=1000, value=8000)

        with col2:
            st.number_input("Concentração Fornecedor (%)", min_value=10, max_value=100, value=70)
            st.selectbox("Sensibilidade IA:", ["Baixa", "Média", "Alta"], index=1)

        if st.button("💾 Salvar Configurações de Alertas"):
            st.success("Configurações de alertas salvas!")

    with tabs[1]:
        st.markdown("### 👥 Gestão de Usuários")
        st.info("Funcionalidade de gestão de usuários disponível")

    with tabs[2]:
        st.markdown("### 📧 Configurações de Notificação")
        st.info("Configurações de notificação disponíveis")

    with tabs[3]:
        st.markdown("### 🔐 Configurações de Segurança")
        st.info("Configurações de segurança disponíveis")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Erro na aplicação: {str(e)}")
        st.info("Recarregue a página para tentar novamente")