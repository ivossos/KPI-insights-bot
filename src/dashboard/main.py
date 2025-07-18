import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import asyncio
import logging

# Configure page
st.set_page_config(
    page_title="IA Fiscal Capivari",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import project modules
from auth.google_auth import GoogleAuthenticator
from database.queries import DatabaseQueries
from ai.claude_explainer import ClaudeExplainer
from export.generators import ReportGenerator
from config import settings, config

# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize application components"""
    auth = GoogleAuthenticator()
    db = DatabaseQueries()
    ai = ClaudeExplainer()
    exporter = ReportGenerator()
    return auth, db, ai, exporter

auth, db, ai, exporter = initialize_components()

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
    
    .alert-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .risk-high { border-left: 4px solid #ff4444; }
    .risk-medium { border-left: 4px solid #ffaa00; }
    .risk-low { border-left: 4px solid #00aa44; }
    
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
        font-size: 1.5rem;
        font-weight: bold;
        color: #2a5298;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Sidebar logo
    st.sidebar.markdown('<div class="sidebar-logo">🏛️ IA Fiscal Capivari</div>', unsafe_allow_html=True)
    
    # Authentication
    if not handle_authentication():
        return
        
    # Navigation
    page = st.sidebar.selectbox(
        "Navegação",
        ["Dashboard", "Alertas", "Dados", "Relatórios", "Configurações", "Ajuda"]
    )
    
    # Route to pages
    if page == "Dashboard":
        show_dashboard()
    elif page == "Alertas":
        show_alerts()
    elif page == "Dados":
        show_data()
    elif page == "Relatórios":
        show_reports()
    elif page == "Configurações":
        show_settings()
    elif page == "Ajuda":
        show_help()

def handle_authentication():
    """Handle Google OAuth authentication"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        
    if not st.session_state.authenticated:
        st.markdown("""
        <div class="main-header">
            <h1>🏛️ IA Fiscal Capivari</h1>
            <p>Sistema de Monitoramento e Alertas para Gastos Municipais</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### Acesso Restrito")
            st.info("Este sistema é destinado apenas para auditores e administradores autorizados.")
            
            if st.button("🔐 Entrar com Google", use_container_width=True):
                try:
                    auth_url = auth.get_auth_url()
                    st.markdown(f'<a href="{auth_url}" target="_blank">Clique aqui para autenticar</a>', 
                               unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erro na autenticação: {str(e)}")
                    
            # Handle OAuth callback
            auth_code = st.text_input("Código de autorização:", placeholder="Cole o código aqui")
            
            if auth_code:
                try:
                    user_info = auth.handle_callback(auth_code)
                    if user_info:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.success("Autenticado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Falha na autenticação")
                except Exception as e:
                    st.error(f"Erro na autenticação: {str(e)}")
                    
        return False
    
    return True

def show_dashboard():
    """Show main dashboard"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard Principal</h1>
        <p>Visão geral dos alertas e métricas fiscais</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Time period selector
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Período de Análise")
    with col2:
        period = st.selectbox("Período", ["Último mês", "Últimos 3 meses", "Último ano"])
    
    # Get data based on period
    days_back = {"Último mês": 30, "Últimos 3 meses": 90, "Último ano": 365}[period]
    
    # Load dashboard data
    try:
        metrics = db.get_dashboard_metrics(days_back)
        alerts = db.get_recent_alerts(days_back)
        
        # Key metrics
        show_key_metrics(metrics)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            show_alerts_trend_chart(alerts)
            
        with col2:
            show_risk_distribution_chart(alerts)
            
        # Recent alerts table
        show_recent_alerts_table(alerts)
        
    except Exception as e:
        st.error(f"Erro ao carregar dados do dashboard: {str(e)}")

def show_key_metrics(metrics: Dict[str, Any]):
    """Show key metrics cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total de Alertas", metrics.get("total_alerts", 0))
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Alertas Críticos", metrics.get("critical_alerts", 0))
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Valor Investigado", f"R$ {metrics.get('investigated_amount', 0):,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Taxa de Investigação", f"{metrics.get('investigation_rate', 0):.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)

def show_alerts_trend_chart(alerts: List[Dict[str, Any]]):
    """Show alerts trend chart"""
    if not alerts:
        st.info("Nenhum alerta encontrado para o período selecionado")
        return
        
    # Convert to DataFrame
    df = pd.DataFrame(alerts)
    df['date'] = pd.to_datetime(df['created_at']).dt.date
    
    # Group by date
    daily_alerts = df.groupby('date').size().reset_index(name='count')
    
    # Create chart
    fig = px.line(
        daily_alerts, 
        x='date', 
        y='count',
        title='Tendência de Alertas por Dia',
        labels={'count': 'Número de Alertas', 'date': 'Data'}
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="Data",
        yaxis_title="Número de Alertas"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_risk_distribution_chart(alerts: List[Dict[str, Any]]):
    """Show risk distribution chart"""
    if not alerts:
        st.info("Nenhum alerta encontrado para o período selecionado")
        return
        
    # Convert to DataFrame
    df = pd.DataFrame(alerts)
    
    # Create risk categories
    def categorize_risk(score):
        if score >= 8:
            return "Alto"
        elif score >= 5:
            return "Médio"
        else:
            return "Baixo"
    
    df['risk_category'] = df['risk_score'].apply(categorize_risk)
    
    # Count by category
    risk_counts = df['risk_category'].value_counts()
    
    # Create pie chart
    fig = px.pie(
        values=risk_counts.values,
        names=risk_counts.index,
        title='Distribuição de Risco dos Alertas',
        color=risk_counts.index,
        color_discrete_map={'Alto': '#ff4444', 'Médio': '#ffaa00', 'Baixo': '#00aa44'}
    )
    
    fig.update_layout(height=400)
    
    st.plotly_chart(fig, use_container_width=True)

def show_recent_alerts_table(alerts: List[Dict[str, Any]]):
    """Show recent alerts table"""
    st.subheader("Alertas Recentes")
    
    if not alerts:
        st.info("Nenhum alerta encontrado")
        return
        
    # Convert to DataFrame
    df = pd.DataFrame(alerts)
    
    # Format data for display
    display_df = df[[
        'rule_type', 'risk_score', 'description', 'created_at', 'is_investigated'
    ]].copy()
    
    display_df.columns = ['Tipo', 'Risco', 'Descrição', 'Data', 'Investigado']
    display_df['Data'] = pd.to_datetime(display_df['Data']).dt.strftime('%d/%m/%Y %H:%M')
    display_df['Investigado'] = display_df['Investigado'].map({True: '✅', False: '❌'})
    
    # Display with selection
    selected_indices = st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        on_select="rerun",
        selection_mode="multi-row"
    )
    
    # Action buttons
    if selected_indices:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Marcar como Investigado"):
                # Update database
                for idx in selected_indices:
                    db.mark_alert_investigated(alerts[idx]['id'])
                st.success("Alertas marcados como investigados")
                st.rerun()
                
        with col2:
            if st.button("Exportar Selecionados"):
                # Export selected alerts
                selected_alerts = [alerts[idx] for idx in selected_indices]
                export_data(selected_alerts)
                
        with col3:
            if st.button("Ver Detalhes"):
                # Show detailed view
                for idx in selected_indices:
                    show_alert_details(alerts[idx])

def show_alerts():
    """Show alerts page"""
    st.markdown("""
    <div class="main-header">
        <h1>🚨 Alertas de Anomalias</h1>
        <p>Gerenciamento e análise de alertas fiscais</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filters
    with st.expander("Filtros", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            rule_types = st.multiselect("Tipo de Regra", 
                                      ["overpricing", "split_orders", "supplier_concentration", 
                                       "recurring_emergency", "payroll_anomaly"])
        
        with col2:
            risk_range = st.slider("Nível de Risco", 1, 10, (1, 10))
            
        with col3:
            date_range = st.date_input("Período", value=[datetime.now() - timedelta(days=30), datetime.now()])
            
        with col4:
            status = st.selectbox("Status", ["Todos", "Não Investigado", "Investigado"])
    
    # Get filtered alerts
    filters = {
        'rule_types': rule_types,
        'risk_range': risk_range,
        'date_range': date_range,
        'status': status
    }
    
    alerts = db.get_filtered_alerts(filters)
    
    if not alerts:
        st.info("Nenhum alerta encontrado com os filtros aplicados")
        return
    
    # Display alerts
    for alert in alerts:
        show_alert_card(alert)

def show_alert_card(alert: Dict[str, Any]):
    """Show individual alert card"""
    risk_class = "risk-high" if alert['risk_score'] >= 8 else "risk-medium" if alert['risk_score'] >= 5 else "risk-low"
    
    st.markdown(f'<div class="alert-card {risk_class}">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"**{alert['rule_type'].replace('_', ' ').title()}**")
        st.markdown(alert['description'])
        
    with col2:
        st.metric("Risco", f"{alert['risk_score']}/10")
        
    with col3:
        status = "✅ Investigado" if alert['is_investigated'] else "❌ Pendente"
        st.markdown(f"**Status:** {status}")
        
    if st.button(f"Ver Detalhes", key=f"details_{alert['id']}"):
        show_alert_details(alert)
        
    st.markdown('</div>', unsafe_allow_html=True)

def show_alert_details(alert: Dict[str, Any]):
    """Show detailed alert information"""
    with st.expander(f"Detalhes - {alert['rule_type']}", expanded=True):
        
        # Basic info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Informações Básicas**")
            st.write(f"ID: {alert['id']}")
            st.write(f"Tipo: {alert['rule_type']}")
            st.write(f"Risco: {alert['risk_score']}/10")
            st.write(f"Criado: {alert['created_at']}")
            
        with col2:
            st.markdown("**Status**")
            st.write(f"Investigado: {'Sim' if alert['is_investigated'] else 'Não'}")
            if alert['is_investigated']:
                st.write(f"Investigador: {alert.get('investigator', 'N/A')}")
                st.write(f"Data: {alert.get('investigated_at', 'N/A')}")
        
        # AI explanation
        st.markdown("**Explicação da IA**")
        try:
            explanation = db.get_alert_explanation(alert['id'])
            if explanation:
                st.markdown(f"**Resumo:** {explanation['summary']}")
                st.markdown(f"**Explicação para Cidadãos:** {explanation['citizen_explanation']}")
                st.markdown(f"**Avaliação de Risco:** {explanation['risk_assessment']}")
                
                st.markdown("**Ações Recomendadas:**")
                for action in explanation['recommended_actions']:
                    st.write(f"• {action}")
            else:
                st.info("Explicação da IA não disponível")
        except Exception as e:
            st.error(f"Erro ao carregar explicação: {str(e)}")
        
        # Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if not alert['is_investigated']:
                if st.button("Marcar como Investigado", key=f"investigate_{alert['id']}"):
                    db.mark_alert_investigated(alert['id'])
                    st.success("Alerta marcado como investigado")
                    st.rerun()
        
        with col2:
            if st.button("Exportar Relatório", key=f"export_{alert['id']}"):
                export_alert_report(alert)
        
        with col3:
            if st.button("Adicionar Notas", key=f"notes_{alert['id']}"):
                notes = st.text_area("Notas de Investigação:", key=f"notes_text_{alert['id']}")
                if st.button("Salvar Notas", key=f"save_notes_{alert['id']}"):
                    db.add_alert_notes(alert['id'], notes)
                    st.success("Notas salvas")

def show_data():
    """Show data management page"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Gestão de Dados</h1>
        <p>Monitoramento e qualidade dos dados fiscais</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Data quality metrics
    try:
        quality_metrics = db.get_data_quality_metrics()
        
        st.subheader("Qualidade dos Dados")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Completude", f"{quality_metrics.get('completeness', 0):.1f}%")
            
        with col2:
            st.metric("Consistência", f"{quality_metrics.get('consistency', 0):.1f}%")
            
        with col3:
            st.metric("Atualização", quality_metrics.get('last_update', 'N/A'))
        
        # Data sources status
        st.subheader("Status das Fontes de Dados")
        
        sources = db.get_data_sources_status()
        
        for source in sources:
            with st.expander(f"{source['name']} - {source['status']}"):
                st.write(f"Última atualização: {source['last_update']}")
                st.write(f"Registros: {source['records_count']}")
                st.write(f"Tamanho: {source['size_mb']} MB")
                
                if source['status'] == 'error':
                    st.error(f"Erro: {source['error_message']}")
                    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")

def show_reports():
    """Show reports page"""
    st.markdown("""
    <div class="main-header">
        <h1>📋 Relatórios</h1>
        <p>Geração e exportação de relatórios fiscais</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Report type selector
    report_type = st.selectbox(
        "Tipo de Relatório",
        ["Resumo de Alertas", "Análise de Fornecedores", "Evolução Temporal", "Relatório Completo"]
    )
    
    # Parameters
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Data Inicial", value=datetime.now() - timedelta(days=30))
        
    with col2:
        end_date = st.date_input("Data Final", value=datetime.now())
    
    # Format selector
    format_type = st.selectbox("Formato", ["PDF", "Excel", "CSV"])
    
    # Generate report
    if st.button("Gerar Relatório"):
        try:
            with st.spinner("Gerando relatório..."):
                report_data = db.get_report_data(report_type, start_date, end_date)
                
                if format_type == "PDF":
                    pdf_file = exporter.generate_pdf_report(report_data, report_type)
                    st.download_button(
                        "Download PDF",
                        data=pdf_file,
                        file_name=f"relatorio_{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                    
                elif format_type == "Excel":
                    excel_file = exporter.generate_excel_report(report_data, report_type)
                    st.download_button(
                        "Download Excel",
                        data=excel_file,
                        file_name=f"relatorio_{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                elif format_type == "CSV":
                    csv_file = exporter.generate_csv_report(report_data, report_type)
                    st.download_button(
                        "Download CSV",
                        data=csv_file,
                        file_name=f"relatorio_{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                    
        except Exception as e:
            st.error(f"Erro ao gerar relatório: {str(e)}")

def show_settings():
    """Show settings page"""
    if not is_admin():
        st.error("Acesso negado. Apenas administradores podem acessar as configurações.")
        return
        
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ Configurações</h1>
        <p>Configurações do sistema e regras de negócio</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load current configuration
    try:
        # Thresholds configuration
        st.subheader("Limites de Alertas")
        
        with st.expander("Configurar Limites", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                overpricing_threshold = st.number_input(
                    "Limite de Sobrepreço (%)",
                    min_value=1,
                    max_value=100,
                    value=config["thresholds"]["overpricing_percentage"]
                )
                
                split_order_threshold = st.number_input(
                    "Limite para Fracionamento (R$)",
                    min_value=1000,
                    max_value=100000,
                    value=config["thresholds"]["split_order_threshold"]
                )
                
            with col2:
                supplier_concentration_threshold = st.number_input(
                    "Limite de Concentração de Fornecedores (%)",
                    min_value=10,
                    max_value=100,
                    value=int(config["thresholds"]["supplier_concentration_threshold"] * 100)
                )
                
                emergency_recurrence_days = st.number_input(
                    "Dias para Emergência Recorrente",
                    min_value=1,
                    max_value=365,
                    value=config["thresholds"]["emergency_recurrence_days"]
                )
        
        # Schedule configuration
        st.subheader("Agendamento")
        
        with st.expander("Configurar Horários", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                scraping_time = st.time_input(
                    "Horário de Coleta",
                    value=datetime.strptime(config["schedule"]["scraping_time"], "%H:%M").time()
                )
                
                etl_time = st.time_input(
                    "Horário de Processamento",
                    value=datetime.strptime(config["schedule"]["etl_time"], "%H:%M").time()
                )
                
            with col2:
                alert_processing_time = st.time_input(
                    "Horário de Análise",
                    value=datetime.strptime(config["schedule"]["alert_processing_time"], "%H:%M").time()
                )
                
                notification_time = st.time_input(
                    "Horário de Notificação",
                    value=datetime.strptime(config["schedule"]["notification_time"], "%H:%M").time()
                )
        
        # Save configuration
        if st.button("Salvar Configurações"):
            try:
                new_config = config.copy()
                new_config["thresholds"]["overpricing_percentage"] = overpricing_threshold
                new_config["thresholds"]["split_order_threshold"] = split_order_threshold
                new_config["thresholds"]["supplier_concentration_threshold"] = supplier_concentration_threshold / 100
                new_config["thresholds"]["emergency_recurrence_days"] = emergency_recurrence_days
                
                # Save to file
                with open("config/config.json", "w") as f:
                    json.dump(new_config, f, indent=2)
                    
                st.success("Configurações salvas com sucesso!")
                
            except Exception as e:
                st.error(f"Erro ao salvar configurações: {str(e)}")
                
    except Exception as e:
        st.error(f"Erro ao carregar configurações: {str(e)}")

def show_help():
    """Show help page"""
    st.markdown("""
    <div class="main-header">
        <h1>❓ Ajuda</h1>
        <p>Guia de uso do sistema IA Fiscal Capivari</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Help sections
    with st.expander("Como usar o Dashboard", expanded=True):
        st.markdown("""
        O Dashboard Principal oferece uma visão geral das anomalias fiscais detectadas:
        
        - **Métricas Principais**: Resumo dos alertas e valores investigados
        - **Gráficos**: Tendências temporais e distribuição de risco
        - **Tabela de Alertas**: Lista dos alertas mais recentes
        
        Use os filtros para personalizar a visualização conforme suas necessidades.
        """)
    
    with st.expander("Tipos de Alertas"):
        st.markdown("""
        O sistema detecta os seguintes tipos de anomalias:
        
        - **Sobrepreço**: Itens com preços acima da média de mercado
        - **Fracionamento**: Divisão de despesas para evitar licitação
        - **Concentração de Fornecedores**: Poucos fornecedores dominam os contratos
        - **Emergências Recorrentes**: Mesmo fornecedor tem muitas emergências
        - **Anomalias na Folha**: Pagamentos atípicos na folha de pagamento
        """)
    
    with st.expander("Investigação de Alertas"):
        st.markdown("""
        Para investigar um alerta:
        
        1. Clique em "Ver Detalhes" no alerta desejado
        2. Revise a explicação da IA e as evidências
        3. Siga as ações recomendadas
        4. Marque como "Investigado" quando concluir
        5. Adicione notas sobre os achados
        """)
    
    with st.expander("Relatórios"):
        st.markdown("""
        O sistema oferece diferentes tipos de relatórios:
        
        - **Resumo de Alertas**: Visão geral dos alertas do período
        - **Análise de Fornecedores**: Concentração e padrões de fornecedores
        - **Evolução Temporal**: Tendências ao longo do tempo
        - **Relatório Completo**: Análise detalhada de todos os dados
        
        Relatórios podem ser exportados em PDF, Excel ou CSV.
        """)
    
    # Contact information
    st.markdown("---")
    st.markdown("**Suporte Técnico**: suporte@capivari.sp.gov.br")
    st.markdown("**Desenvolvido por**: Equipe de Tecnologia da Prefeitura de Capivari")

def is_admin():
    """Check if current user is admin"""
    if "user_info" not in st.session_state:
        return False
    
    user_email = st.session_state.user_info.get("email", "")
    admin_emails = ["admin@capivari.sp.gov.br", "auditoria@capivari.sp.gov.br"]
    
    return user_email in admin_emails

def export_data(data):
    """Export data to file"""
    # This would implement the export functionality
    st.info("Funcionalidade de exportação em desenvolvimento")

def export_alert_report(alert):
    """Export individual alert report"""
    # This would implement the alert report export
    st.info("Funcionalidade de exportação em desenvolvimento")

if __name__ == "__main__":
    main()