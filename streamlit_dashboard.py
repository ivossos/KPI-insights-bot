
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
        <small>Dashboard em funcionamento - {}s</small>
    </div>
    """.format(int(time.time())), unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.title("📋 Menu")
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
        st.success("API: Conectada")
        st.success("Banco: Online")
        st.success("IA: Ativa")
    
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
        np_values = [8, 12, 6, 15, 9, 18, 11, 7, 14, 10, 16, 13, 5, 19, 8, 12, 15, 9, 11, 17, 6, 13, 10, 14, 7, 16, 12, 8, 15, 11]
        
        df_trend = pd.DataFrame({
            'Data': dates,
            'Alertas': np_values
        })
        
        fig_trend = px.line(
            df_trend, 
            x='Data', 
            y='Alertas',
            title="Alertas por Dia",
            line_shape='spline'
        )
        fig_trend.update_layout(showlegend=False)
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Distribuição por Tipo de Alerta")
        
        alert_types = pd.DataFrame({
            'Tipo': ['Sobrepreço', 'Fracionamento', 'Concentração', 'Emergência', 'Direcionamento'],
            'Quantidade': [45, 38, 28, 25, 20],
            'Cores': ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57']
        })
        
        fig_pie = px.pie(
            alert_types, 
            values='Quantidade', 
            names='Tipo',
            title="Tipos de Alertas",
            color_discrete_sequence=alert_types['Cores']
        )
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
    
    # Alert details
    tabs = st.tabs(["📊 Visão Geral", "📋 Lista Detalhada", "📈 Análise Temporal"])
    
    with tabs[0]:
        col1, col2 = st.columns(2)
        
        with col1:
            # Risk distribution
            risk_data = pd.DataFrame({
                'Nível': ['Alto', 'Médio', 'Baixo'],
                'Quantidade': [23, 45, 32],
                'Cor': ['#dc3545', '#ffc107', '#28a745']
            })
            
            fig_risk = px.bar(
                risk_data,
                x='Nível',
                y='Quantidade',
                title="Distribuição por Nível de Risco",
                color='Nível',
                color_discrete_map={'Alto': '#dc3545', 'Médio': '#ffc107', 'Baixo': '#28a745'}
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        
        with col2:
            # Status distribution
            status_data = pd.DataFrame({
                'Status': ['Pendente', 'Em Análise', 'Investigado', 'Arquivado'],
                'Quantidade': [34, 28, 25, 13]
            })
            
            fig_status = px.pie(
                status_data,
                values='Quantidade',
                names='Status',
                title="Status dos Alertas"
            )
            st.plotly_chart(fig_status, use_container_width=True)
    
    with tabs[1]:
        # Detailed alerts list
        detailed_alerts = pd.DataFrame({
            'ID': [f'#2024-{str(i).zfill(3)}' for i in range(1, 21)],
            'Tipo': ['Sobrepreço', 'Fracionamento', 'Concentração'] * 7,
            'Risco': [9, 7, 8, 6, 9, 5, 8, 7, 9, 6, 8, 5, 7, 9, 6, 8, 7, 9, 5, 8],
            'Valor': [f'R$ {(i*15000 + 10000):,.0f}' for i in range(1, 21)],
            'Fornecedor': [f'Empresa {chr(65+i%10)} Ltda' for i in range(20)],
            'Data': [(datetime.now() - timedelta(days=i)).strftime('%d/%m/%Y') for i in range(20)]
        })
        
        st.dataframe(detailed_alerts, use_container_width=True, hide_index=True)
    
    with tabs[2]:
        # Temporal analysis
        st.info("Análise temporal dos alertas por categoria e período")
        
        # Time series chart
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        types = ['Sobrepreço', 'Fracionamento', 'Concentração']
        
        data_rows = []
        for date in dates:
            for alert_type in types:
                data_rows.append({
                    'Data': date,
                    'Tipo': alert_type,
                    'Alertas': abs(int((date.day + hash(alert_type)) % 8)) + 1
                })
        
        df_temporal = pd.DataFrame(data_rows)
        
        fig_temporal = px.line(
            df_temporal,
            x='Data',
            y='Alertas',
            color='Tipo',
            title="Evolução Temporal por Tipo de Alerta"
        )
        st.plotly_chart(fig_temporal, use_container_width=True)

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
    
    # Analysis charts
    tabs = st.tabs(["📊 Por Categoria", "🏢 Por Secretaria", "📅 Temporal", "🔍 Fornecedores"])
    
    with tabs[0]:
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
                title="Gastos por Categoria",
                text='Valor'
            )
            fig_cat_spending.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
            fig_cat_spending.update_layout(xaxis_tickangle=-45)
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
            st.plotly_chart(fig_cat_alerts, use_container_width=True)
    
    with tabs[1]:
        st.info("Análise de gastos por secretaria municipal")
        
        # Department spending
        departments = pd.DataFrame({
            'Secretaria': ['Educação', 'Saúde', 'Obras', 'Administração', 'Transporte'],
            'Orçamento': [5000000, 4500000, 3200000, 1800000, 1200000],
            'Executado': [4200000, 4100000, 2800000, 1650000, 1050000],
            'Percentual': [84, 91, 88, 92, 88]
        })
        
        fig_dept = px.bar(
            departments,
            x='Secretaria',
            y=['Orçamento', 'Executado'],
            title="Orçamento vs Executado por Secretaria",
            barmode='group'
        )
        st.plotly_chart(fig_dept, use_container_width=True)
    
    with tabs[2]:
        st.info("Análise temporal dos gastos")
        
        # Monthly spending trend
        months = pd.date_range(start='2024-01-01', end='2024-12-01', freq='M')
        monthly_data = pd.DataFrame({
            'Mês': months,
            'Gastos': [1200000 + i*50000 + (i%3)*100000 for i in range(len(months))],
            'Meta': [1500000] * len(months)
        })
        
        fig_monthly = px.line(
            monthly_data,
            x='Mês',
            y=['Gastos', 'Meta'],
            title="Evolução Mensal dos Gastos"
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    with tabs[3]:
        st.info("Análise de fornecedores")
        
        # Top suppliers
        suppliers = pd.DataFrame({
            'Fornecedor': [f'Empresa {chr(65+i)} Ltda' for i in range(10)],
            'Valor_Contratado': [500000 - i*40000 for i in range(10)],
            'Num_Contratos': [15 - i for i in range(10)],
            'Alertas': [8, 5, 12, 3, 7, 9, 4, 6, 10, 2]
        })
        
        fig_suppliers = px.scatter(
            suppliers,
            x='Valor_Contratado',
            y='Num_Contratos',
            size='Alertas',
            hover_name='Fornecedor',
            title="Fornecedores: Valor vs Contratos (tamanho = alertas)"
        )
        st.plotly_chart(fig_suppliers, use_container_width=True)

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
            st.download_button(
                label=f"⬇️ Download {report_type}.{format_type.lower()}",
                data=f"Relatório simulado - {report_type}",
                file_name=f"relatorio_{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.{format_type.lower()}",
                mime="application/octet-stream"
            )
    
    with col2:
        st.markdown("### 📈 Relatórios Rápidos")
        
        if st.button("📊 Dashboard Executivo"):
            st.info("Gerando dashboard executivo...")
        
        if st.button("🚨 Alertas Críticos"):
            st.info("Compilando alertas críticos...")
        
        if st.button("💰 Resumo Financeiro"):
            st.info("Processando resumo financeiro...")
        
        if st.button("📋 Compliance"):
            st.info("Verificando compliance...")
    
    st.markdown("---")
    
    # Recent reports
    st.subheader("📋 Relatórios Recentes")
    
    recent_reports = pd.DataFrame({
        'Relatório': ['Resumo Executivo - Janeiro', 'Alertas Críticos - S01', 'Fornecedores - Trimestre', 'Gastos Educação - Janeiro'],
        'Tipo': ['Executivo', 'Alertas', 'Fornecedores', 'Categoria'],
        'Data_Geração': ['15/01/2024', '12/01/2024', '08/01/2024', '05/01/2024'],
        'Status': ['✅ Concluído', '✅ Concluído', '✅ Concluído', '✅ Concluído'],
        'Tamanho': ['2.1 MB', '856 KB', '1.4 MB', '678 KB']
    })
    
    st.dataframe(recent_reports, use_container_width=True, hide_index=True)

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
            st.number_input("Concentração Fornecedor (%)", min_value=10, max_value=100, value=70)
        
        with col2:
            st.number_input("Dias Emergência Recorrente", min_value=1, value=30)
            st.number_input("Limite Direcionamento (%)", min_value=1, max_value=100, value=15)
            st.selectbox("Sensibilidade IA:", ["Baixa", "Média", "Alta"], index=1)
        
        if st.button("💾 Salvar Configurações de Alertas"):
            st.success("Configurações de alertas salvas!")
    
    with tabs[1]:
        st.markdown("### 👥 Gestão de Usuários")
        
        users_data = pd.DataFrame({
            'Nome': ['Admin Sistema', 'Ana Silva', 'João Santos', 'Maria Costa'],
            'Email': ['admin@capivari.sp.gov.br', 'ana.silva@capivari.sp.gov.br', 'joao.santos@capivari.sp.gov.br', 'maria.costa@capivari.sp.gov.br'],
            'Perfil': ['Administrador', 'Analista', 'Supervisor', 'Consultor'],
            'Status': ['🟢 Ativo', '🟢 Ativo', '🟢 Ativo', '🟡 Pendente']
        })
        
        st.dataframe(users_data, use_container_width=True, hide_index=True)
        
        if st.button("➕ Adicionar Usuário"):
            st.info("Funcionalidade de adição de usuário")
    
    with tabs[2]:
        st.markdown("### 📧 Configurações de Notificação")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Email para alertas críticos", value=True)
            st.checkbox("Email resumo diário", value=True)
            st.checkbox("Telegram para emergências", value=False)
        
        with col2:
            st.time_input("Horário do resumo diário:", value=datetime.strptime("08:00", "%H:%M").time())
            st.text_input("Email principal:", value="admin@capivari.sp.gov.br")
            st.text_input("Telegram Bot Token:", value="", type="password")
        
        if st.button("📧 Salvar Notificações"):
            st.success("Configurações de notificação salvas!")
    
    with tabs[3]:
        st.markdown("### 🔐 Configurações de Segurança")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.number_input("Timeout sessão (minutos):", min_value=15, max_value=480, value=120)
            st.checkbox("Autenticação dois fatores", value=False)
            st.checkbox("Log de auditoria", value=True)
        
        with col2:
            st.selectbox("Nível de log:", ["INFO", "WARNING", "ERROR", "DEBUG"], index=0)
            st.number_input("Retenção logs (dias):", min_value=7, max_value=365, value=90)
            st.checkbox("Backup automático", value=True)
        
        if st.button("🔐 Salvar Segurança"):
            st.success("Configurações de segurança salvas!")

if __name__ == "__main__":
    main()
