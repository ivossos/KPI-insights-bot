import streamlit as st
import requests
import json
import plotly.graph_objects as go
from typing import Dict, List, Any
import pandas as pd
from datetime import datetime, timedelta
import time

from ..models import KPIQuery, KPIResponse, UserRole
from ...monitoring.logger import logger

# Page configuration
st.set_page_config(
    page_title="KPI Insight Bot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme with gold accents
st.markdown("""
<style>
    .main {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    .stButton > button {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #ffd700;
        border-radius: 5px;
    }
    
    .stButton > button:hover {
        background-color: #ffd700;
        color: #000000;
    }
    
    .stTextInput > div > div > input {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #ffd700;
    }
    
    .stSelectbox > div > div > select {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #ffd700;
    }
    
    .metric-card {
        background-color: #2d2d2d;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ffd700;
        margin: 10px 0;
    }
    
    .chat-container {
        background-color: #2d2d2d;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ffd700;
        margin: 10px 0;
        min-height: 400px;
    }
    
    .user-message {
        background-color: #0066cc;
        color: white;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        text-align: right;
    }
    
    .bot-message {
        background-color: #2d2d2d;
        color: white;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        border-left: 3px solid #ffd700;
    }
    
    .kpi-value {
        font-size: 2em;
        font-weight: bold;
        color: #ffd700;
    }
    
    .variance-positive {
        color: #28a745;
    }
    
    .variance-negative {
        color: #dc3545;
    }
    
    .sidebar .sidebar-content {
        background-color: #2d2d2d;
    }
</style>
""", unsafe_allow_html=True)

class KPIDashboard:
    def __init__(self):
        self.api_base_url = "http://localhost:8000/api/v1"
        self.session_state = st.session_state
        self._initialize_session_state()

    def _initialize_session_state(self):
        if 'chat_history' not in self.session_state:
            self.session_state.chat_history = []
        if 'user_token' not in self.session_state:
            self.session_state.user_token = None
        if 'user_role' not in self.session_state:
            self.session_state.user_role = UserRole.VIEWER
        if 'available_kpis' not in self.session_state:
            self.session_state.available_kpis = []
        if 'current_kpi_results' not in self.session_state:
            self.session_state.current_kpi_results = []

    def run(self):
        st.title("📊 KPI Insight Bot")
        st.markdown("---")
        
        if not self.session_state.user_token:
            self._show_login_page()
        else:
            self._show_main_dashboard()

    def _show_login_page(self):
        st.header("🔐 Login")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            
            login_method = st.radio(
                "Choose login method:",
                ["Email/Password", "Google SSO", "Corporate SSO"]
            )
            
            if login_method == "Email/Password":
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                if st.button("Login", key="email_login"):
                    if email and password:
                        if self._authenticate_user(email, password):
                            st.success("Login successful!")
                            st.experimental_rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.error("Please fill in all fields")
            
            elif login_method == "Google SSO":
                st.info("Google SSO integration coming soon")
                
            elif login_method == "Corporate SSO":
                st.info("Corporate SSO integration coming soon")
            
            st.markdown('</div>', unsafe_allow_html=True)

    def _show_main_dashboard(self):
        # Sidebar
        with st.sidebar:
            st.header("🎛️ Controls")
            
            # User info
            st.info(f"Role: {self.session_state.user_role.value}")
            
            # KPI Categories
            st.subheader("📋 KPI Categories")
            categories = ["All", "Revenue", "Expenses", "Margin", "Cash", "Variance"]
            selected_category = st.selectbox("Select Category", categories)
            
            # Time filters
            st.subheader("📅 Time Filters")
            time_period = st.selectbox("Period", ["YTD", "Current Month", "Current Quarter", "Last Month", "Last Quarter"])
            year = st.selectbox("Year", [2024, 2023, 2022, 2021])
            
            # Quick actions
            st.subheader("⚡ Quick Actions")
            if st.button("Show All KPIs"):
                self._show_all_kpis()
            
            if st.button("Generate Report"):
                self._generate_report()
            
            if st.button("Clear Chat"):
                self.session_state.chat_history = []
                st.experimental_rerun()
            
            # Logout
            if st.button("Logout"):
                self._logout()

        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._show_chat_interface()
        
        with col2:
            self._show_kpi_overview()

    def _show_chat_interface(self):
        st.header("💬 Chat with KPI Bot")
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            
            # Display chat history
            for message in self.session_state.chat_history:
                if message['type'] == 'user':
                    st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)
                    
                    # Show KPI results if available
                    if 'kpi_results' in message:
                        self._display_kpi_results(message['kpi_results'])
                    
                    # Show chart if available
                    if 'chart_data' in message:
                        self._display_chart(message['chart_data'])
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat input
        user_input = st.text_input(
            "Ask about KPIs:",
            placeholder="e.g., 'What's our revenue variance this quarter?'",
            key="chat_input"
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            if st.button("Send", key="send_message"):
                if user_input:
                    self._process_chat_message(user_input)
                    st.experimental_rerun()
        
        with col2:
            if st.button("Suggestions", key="get_suggestions"):
                self._show_suggestions()

    def _show_kpi_overview(self):
        st.header("📈 KPI Overview")
        
        # Summary metrics
        if self.session_state.current_kpi_results:
            for result in self.session_state.current_kpi_results[:3]:  # Show top 3
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**{result['name']}**")
                    st.markdown(f'<div class="kpi-value">{result["value"]:,.0f}</div>', unsafe_allow_html=True)
                    st.markdown(f"*{result['unit']} ({result['currency'] or 'N/A'})*")
                
                with col2:
                    if result.get('variance_py'):
                        variance_class = "variance-positive" if result['variance_py'] > 0 else "variance-negative"
                        st.markdown(f'<div class="{variance_class}">vs PY: {result["variance_py"]:,.0f}</div>', unsafe_allow_html=True)
                    
                    if result.get('variance_plan'):
                        variance_class = "variance-positive" if result['variance_plan'] > 0 else "variance-negative"
                        st.markdown(f'<div class="{variance_class}">vs Plan: {result["variance_plan"]:,.0f}</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Recent alerts
        st.subheader("🚨 Recent Alerts")
        self._show_recent_alerts()
        
        # Quick stats
        st.subheader("📊 Quick Stats")
        self._show_quick_stats()

    def _process_chat_message(self, user_input: str):
        # Add user message to chat history
        self.session_state.chat_history.append({
            'type': 'user',
            'content': user_input,
            'timestamp': datetime.now()
        })
        
        # Show typing indicator
        with st.spinner("Processing your query..."):
            try:
                # Make API call
                response = self._query_kpi_api(user_input)
                
                if response:
                    # Add bot response to chat history
                    bot_message = {
                        'type': 'bot',
                        'content': response.get('narrative_summary', 'No summary available'),
                        'timestamp': datetime.now(),
                        'kpi_results': response.get('kpi_results', []),
                        'chart_data': response.get('chart_data', {}),
                        'suggestions': response.get('suggestions', [])
                    }
                    
                    self.session_state.chat_history.append(bot_message)
                    self.session_state.current_kpi_results = response.get('kpi_results', [])
                else:
                    self.session_state.chat_history.append({
                        'type': 'bot',
                        'content': 'Sorry, I encountered an error processing your request.',
                        'timestamp': datetime.now()
                    })
                    
            except Exception as e:
                logger.error(f"Chat message processing failed: {e}")
                self.session_state.chat_history.append({
                    'type': 'bot',
                    'content': f'Error: {str(e)}',
                    'timestamp': datetime.now()
                })

    def _query_kpi_api(self, query_text: str) -> Dict[str, Any]:
        try:
            headers = {
                'Authorization': f'Bearer {self.session_state.user_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'user_id': 'current_user',
                'query_text': query_text,
                'filters': {
                    'year': '2024',
                    'period': 'YTD'
                }
            }
            
            response = requests.post(
                f"{self.api_base_url}/kpi/query",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"API call failed: {e}")
            st.error(f"Connection error: {str(e)}")
            return None

    def _display_kpi_results(self, kpi_results: List[Dict[str, Any]]):
        if not kpi_results:
            return
        
        for result in kpi_results:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label=result['name'],
                    value=f"{result['value']:,.0f}",
                    delta=result.get('variance_py', 0)
                )
            
            with col2:
                if result.get('variance_plan'):
                    st.metric(
                        label="vs Plan",
                        value=f"{result['variance_plan']:,.0f}",
                        delta=None
                    )
            
            with col3:
                if result.get('drill_down_url'):
                    if st.button(f"Drill Down", key=f"drill_{result['kpi_id']}"):
                        self._show_drill_down(result['kpi_id'])

    def _display_chart(self, chart_data: Dict[str, Any]):
        if not chart_data:
            return
        
        try:
            if chart_data.get('type') == 'gauge':
                fig = go.Figure(chart_data['data'])
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_data.get('type') == 'bar':
                fig = go.Figure(chart_data['data'])
                st.plotly_chart(fig, use_container_width=True)
            
            # Show variance chart if available
            if 'variance_chart' in chart_data:
                st.subheader("Variance Analysis")
                fig = go.Figure(chart_data['variance_chart'])
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            logger.error(f"Chart display failed: {e}")
            st.error("Failed to display chart")

    def _show_drill_down(self, kpi_id: str):
        st.subheader(f"Drill Down - {kpi_id}")
        
        # This would fetch detailed data from the API
        st.info("Drill-down functionality coming soon")

    def _show_suggestions(self):
        suggestions = [
            "Show me revenue trends this year",
            "What's our OPEX variance vs plan?",
            "How is our gross margin performing?",
            "Show cash position by quarter",
            "Compare revenue vs last year"
        ]
        
        st.subheader("💡 Suggested Queries")
        for suggestion in suggestions:
            if st.button(suggestion, key=f"suggestion_{suggestion}"):
                self._process_chat_message(suggestion)

    def _show_recent_alerts(self):
        # Mock alert data
        alerts = [
            {"kpi": "Revenue", "message": "5% above plan", "severity": "info"},
            {"kpi": "OPEX", "message": "2% over budget", "severity": "warning"},
            {"kpi": "Cash", "message": "Below threshold", "severity": "critical"}
        ]
        
        for alert in alerts:
            color = {
                "info": "blue",
                "warning": "orange", 
                "critical": "red"
            }.get(alert['severity'], "gray")
            
            st.markdown(f":{color}[{alert['kpi']}]: {alert['message']}")

    def _show_quick_stats(self):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total KPIs", "15")
            st.metric("Active Alerts", "3")
        
        with col2:
            st.metric("This Month Queries", "127")
            st.metric("Avg Response Time", "2.3s")

    def _show_all_kpis(self):
        st.subheader("📋 All Available KPIs")
        
        # This would fetch from the API
        kpis = [
            {"name": "Total Revenue", "category": "Revenue", "status": "Active"},
            {"name": "Gross Margin %", "category": "Margin", "status": "Active"},
            {"name": "OPEX Variance", "category": "Variance", "status": "Active"},
            {"name": "Cash Position", "category": "Cash", "status": "Active"}
        ]
        
        df = pd.DataFrame(kpis)
        st.dataframe(df, use_container_width=True)

    def _generate_report(self):
        st.subheader("📊 Generate Report")
        st.info("Report generation functionality coming soon")

    def _authenticate_user(self, email: str, password: str) -> bool:
        # Mock authentication
        if email == "admin@company.com" and password == "admin123":
            self.session_state.user_token = "mock_token_123"
            self.session_state.user_role = UserRole.ADMIN
            return True
        elif email == "analyst@company.com" and password == "analyst123":
            self.session_state.user_token = "mock_token_456"
            self.session_state.user_role = UserRole.ANALYST
            return True
        return False

    def _logout(self):
        self.session_state.user_token = None
        self.session_state.user_role = UserRole.VIEWER
        self.session_state.chat_history = []
        self.session_state.current_kpi_results = []
        st.experimental_rerun()

# Run the dashboard
if __name__ == "__main__":
    dashboard = KPIDashboard()
    dashboard.run()