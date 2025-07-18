#!/usr/bin/env python3
"""
Simple dashboard for IA Fiscal Capivari
Works with minimal dependencies
"""

import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd

# Configure Streamlit page
st.set_page_config(
    page_title="IA Fiscal Capivari",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .alert-high { border-left: 5px solid #ff4444; }
    .alert-medium { border-left: 5px solid #ffaa44; }
    .alert-low { border-left: 5px solid #44ff44; }
</style>
""", unsafe_allow_html=True)

def main():
    """Main dashboard function"""
    
    # Header
    st.title("🏛️ IA Fiscal Capivari")
    st.markdown("**Sistema de Monitoramento de Gastos Municipais com IA**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Painel de Controle")
        
        # API connection status
        api_status = check_api_connection()
        if api_status:
            st.success("✅ API Conectada")
        else:
            st.error("❌ API Desconectada")
            
        st.markdown("---")
        
        # Navigation
        page = st.selectbox("Navegar para:", [
            "Dashboard Principal",
            "Alertas Recentes", 
            "Análise de Dados",
            "Configurações"
        ])
    
    # Main content area
    if page == "Dashboard Principal":
        show_main_dashboard()
    elif page == "Alertas Recentes":
        show_alerts_page()
    elif page == "Análise de Dados":
        show_analysis_page()
    elif page == "Configurações":
        show_settings_page()

def check_api_connection():
    """Check if API is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def show_main_dashboard():
    """Show main dashboard"""
    st.header("📊 Dashboard Principal")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Alertas Ativos", "42", "↑ 5")
    with col2:
        st.metric("Gastos Analisados", "R$ 2.5M", "↑ 12%")
    with col3:
        st.metric("Fornecedores", "156", "→ 0")
    with col4:
        st.metric("Taxa de Risco", "23%", "↓ 3%")
    
    st.markdown("---")
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Alertas por Tipo")
        
        # Sample alert data
        alert_data = {
            'Tipo': ['Sobrepreço', 'Fracionamento', 'Concentração', 'Outros'],
            'Quantidade': [15, 12, 8, 7]
        }
        df_alerts = pd.DataFrame(alert_data)
        st.bar_chart(df_alerts.set_index('Tipo'))
        
    with col2:
        st.subheader("💰 Gastos por Categoria")
        
        # Sample spending data
        spending_data = {
            'Categoria': ['Obras', 'Serviços', 'Material', 'Equipamentos'],
            'Valor': [850000, 450000, 320000, 180000]
        }
        df_spending = pd.DataFrame(spending_data)
        st.bar_chart(df_spending.set_index('Categoria'))
    
    # Recent alerts
    st.markdown("---")
    st.subheader("🚨 Alertas Recentes")
    
    # Get alerts from API
    try:
        response = requests.get("http://localhost:8000/alerts", timeout=5)
        if response.status_code == 200:
            alerts_data = response.json()
            
            for alert in alerts_data.get('alerts', []):
                risk_color = "high" if alert['risk_score'] >= 7 else "medium" if alert['risk_score'] >= 4 else "low"
                
                st.markdown(f"""
                <div class="metric-card alert-{risk_color}">
                    <strong>{alert['type'].title()}</strong> - Risco: {alert['risk_score']}/10<br>
                    {alert['description']}<br>
                    <small>📅 {alert['created_at']} | Status: {alert['status']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Não foi possível carregar alertas da API")
            
    except Exception as e:
        st.error(f"Erro ao conectar com API: {str(e)}")
        
        # Show sample alerts
        st.info("Mostrando dados de exemplo:")
        sample_alerts = [
            {"type": "Sobrepreço", "description": "Item com preço 35% acima da média", "risk_score": 8},
            {"type": "Fracionamento", "description": "Possível divisão de pedido detectada", "risk_score": 6},
            {"type": "Concentração", "description": "Alta concentração de fornecedor (78%)", "risk_score": 7}
        ]
        
        for alert in sample_alerts:
            risk_color = "high" if alert['risk_score'] >= 7 else "medium" if alert['risk_score'] >= 4 else "low"
            st.markdown(f"""
            <div class="metric-card alert-{risk_color}">
                <strong>{alert['type']}</strong> - Risco: {alert['risk_score']}/10<br>
                {alert['description']}<br>
                <small>📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} | Status: Pendente</small>
            </div>
            """, unsafe_allow_html=True)

def show_alerts_page():
    """Show alerts page"""
    st.header("🚨 Alertas Recentes")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        alert_type = st.selectbox("Tipo de Alerta", ["Todos", "Sobrepreço", "Fracionamento", "Concentração"])
    with col2:
        risk_level = st.selectbox("Nível de Risco", ["Todos", "Alto (7-10)", "Médio (4-6)", "Baixo (1-3)"])
    with col3:
        status = st.selectbox("Status", ["Todos", "Pendente", "Investigando", "Resolvido"])
    
    st.markdown("---")
    
    # Sample detailed alerts table
    alerts_data = {
        'ID': ['ALT-001', 'ALT-002', 'ALT-003', 'ALT-004'],
        'Tipo': ['Sobrepreço', 'Fracionamento', 'Concentração', 'Sobrepreço'],
        'Descrição': [
            'Papel A4 - 35% acima do preço médio',
            'Divisão de compra de material de limpeza',
            'Fornecedor ABC com 78% dos contratos',
            'Tinta - 42% acima do preço de referência'
        ],
        'Risco': [8, 6, 7, 9],
        'Valor': ['R$ 15.000', 'R$ 8.500', 'R$ 125.000', 'R$ 22.000'],
        'Data': ['2024-01-15', '2024-01-15', '2024-01-14', '2024-01-14'],
        'Status': ['Pendente', 'Investigando', 'Pendente', 'Resolvido']
    }
    
    df_alerts = pd.DataFrame(alerts_data)
    st.dataframe(df_alerts, use_container_width=True)

def show_analysis_page():
    """Show analysis page"""
    st.header("📊 Análise de Dados")
    
    st.info("Esta seção mostrará análises detalhadas dos dados municipais.")
    
    # Sample analysis charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Tendência de Gastos")
        # Generate sample time series data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        spending = [100000 + i*1000 + (i%7)*5000 for i in range(len(dates))]
        df_trend = pd.DataFrame({'Data': dates, 'Gastos': spending})
        st.line_chart(df_trend.set_index('Data'))
        
    with col2:
        st.subheader("Distribuição de Fornecedores")
        suppliers_data = {
            'Fornecedor': ['ABC Ltda', 'XYZ SA', 'DEF Corp', 'GHI Ltda', 'Outros'],
            'Participação': [25, 20, 15, 12, 28]
        }
        df_suppliers = pd.DataFrame(suppliers_data)
        st.bar_chart(df_suppliers.set_index('Fornecedor'))

def show_settings_page():
    """Show settings page"""
    st.header("⚙️ Configurações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Configurações de Alertas")
        st.slider("Limite de Risco Alto", 1, 10, 7)
        st.slider("Limite de Risco Médio", 1, 10, 4)
        st.checkbox("Notificações por Email", True)
        st.checkbox("Notificações por Telegram", False)
        
    with col2:
        st.subheader("Configurações da API")
        st.text_input("URL da API", "http://localhost:8000")
        st.text_input("Token de Acesso", type="password")
        
        if st.button("Testar Conexão"):
            if check_api_connection():
                st.success("✅ Conexão bem-sucedida!")
            else:
                st.error("❌ Falha na conexão")
    
    st.markdown("---")
    
    # System info
    st.subheader("ℹ️ Informações do Sistema")
    try:
        response = requests.get("http://localhost:8000/info", timeout=5)
        if response.status_code == 200:
            info = response.json()
            st.json(info)
        else:
            st.warning("Não foi possível obter informações do sistema")
    except:
        st.error("API não disponível")

if __name__ == "__main__":
    main()