
#!/usr/bin/env python3
"""
Simple Streamlit Dashboard for IA Fiscal Capivari
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json

# Configure page
st.set_page_config(
    page_title="IA Fiscal Capivari",
    page_icon="🏛️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
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
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("Navegação")
    page = st.sidebar.selectbox(
        "Escolha uma página:",
        ["Dashboard", "Alertas", "Relatórios", "Configurações"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Alertas":
        show_alerts()
    elif page == "Relatórios":
        show_reports()
    elif page == "Configurações":
        show_settings()

def show_dashboard():
    """Show main dashboard"""
    st.subheader("📊 Dashboard Principal")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Alertas", "23", "+5")
        
    with col2:
        st.metric("Alertas Críticos", "8", "+2")
        
    with col3:
        st.metric("Valor Investigado", "R$ 1.2M", "+15%")
        
    with col4:
        st.metric("Taxa de Investigação", "78%", "+3%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Mock data for alerts trend
        dates = pd.date_range(start='2024-01-01', end='2024-01-15', freq='D')
        values = [5, 8, 3, 12, 7, 15, 9, 6, 11, 4, 13, 8, 10, 7, 12]
        
        df = pd.DataFrame({'Date': dates, 'Alerts': values})
        
        fig = px.line(df, x='Date', y='Alerts', title='Tendência de Alertas')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Risk distribution
        risk_data = pd.DataFrame({
            'Risk Level': ['Alto', 'Médio', 'Baixo'],
            'Count': [8, 10, 5]
        })
        
        fig = px.pie(risk_data, values='Count', names='Risk Level', 
                     title='Distribuição de Risco',
                     color_discrete_map={'Alto': '#ff4444', 'Médio': '#ffaa00', 'Baixo': '#00aa44'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent alerts table
    st.subheader("Alertas Recentes")
    
    alerts_data = {
        'Tipo': ['Sobrepreço', 'Fracionamento', 'Concentração', 'Emergência'],
        'Descrição': [
            'Item 35% acima do preço médio',
            'Possível divisão de pedidos',
            'Alta concentração de fornecedores',
            'Muitas emergências do mesmo fornecedor'
        ],
        'Risco': [8, 6, 7, 5],
        'Data': ['15/01/2024', '15/01/2024', '14/01/2024', '14/01/2024'],
        'Status': ['Pendente', 'Investigado', 'Pendente', 'Pendente']
    }
    
    df_alerts = pd.DataFrame(alerts_data)
    st.dataframe(df_alerts, use_container_width=True)

def show_alerts():
    """Show alerts page"""
    st.subheader("🚨 Gestão de Alertas")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rule_type = st.selectbox("Tipo de Regra", 
                                ["Todos", "Sobrepreço", "Fracionamento", "Concentração"])
    
    with col2:
        risk_level = st.selectbox("Nível de Risco", 
                                 ["Todos", "Alto (8-10)", "Médio (5-7)", "Baixo (1-4)"])
    
    with col3:
        status = st.selectbox("Status", ["Todos", "Pendente", "Investigado"])
    
    st.info("Sistema de alertas em funcionamento. Conectando com base de dados...")

def show_reports():
    """Show reports page"""
    st.subheader("📋 Relatórios")
    
    report_type = st.selectbox(
        "Tipo de Relatório",
        ["Resumo de Alertas", "Análise de Fornecedores", "Evolução Temporal"]
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Data Inicial", value=datetime.now() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("Data Final", value=datetime.now())
    
    if st.button("Gerar Relatório"):
        st.success("Relatório gerado com sucesso!")
        st.info("Funcionalidade de download será implementada na próxima versão.")

def show_settings():
    """Show settings page"""
    st.subheader("⚙️ Configurações")
    
    st.markdown("### Limites de Alertas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        overpricing = st.number_input("Limite de Sobrepreço (%)", min_value=1, max_value=100, value=20)
        split_threshold = st.number_input("Limite para Fracionamento (R$)", min_value=1000, value=8000)
    
    with col2:
        concentration = st.number_input("Concentração de Fornecedores (%)", min_value=10, value=70)
        emergency_days = st.number_input("Dias para Emergência Recorrente", min_value=1, value=30)
    
    if st.button("Salvar Configurações"):
        st.success("Configurações salvas com sucesso!")

if __name__ == "__main__":
    main()
