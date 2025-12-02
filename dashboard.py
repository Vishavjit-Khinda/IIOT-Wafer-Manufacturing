"""
Layer 5: Streamlit Dashboard - Application Layer
Interactive dashboard for monitoring production lines and managing alerts
"""
import streamlit as st
import psycopg2
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'Your database name',
    'user': 'postgres',
    'password': 'Your database password'  
}

# Page configuration
st.set_page_config(
    page_title="IIoT Wafer Manufacturing",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        font-size: 1.5rem;  
        font-weight: 500;
        color: #333;
        margin-top: -0.2em;
    }       
    .status-idle {
        background-color: #d3d3d3;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .status-running {
        background-color: #90EE90;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .status-stopped {
        background-color: #FFB6C1;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .alert-box {
        background-color: #ffcccc;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff0000;
    }
    .no-alert-box {
        background-color: #ccffcc;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #00ff00;
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def get_production_line_status():
    """Get current status of all production lines"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    query = "SELECT * FROM production_lines ORDER BY line_name"
    df = pd.read_sql(query, conn)
    return df

def get_latest_sensor_data(line_name, limit=20):
    """Get latest sensor data for a production line"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    query = """
        SELECT * FROM sensor_data 
        WHERE production_line = %s 
        ORDER BY created_at DESC 
        LIMIT %s
    """
    df = pd.read_sql(query, conn, params=(line_name, limit))
    return df

def get_active_alerts():
    """Get unacknowledged alerts"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    query = """
        SELECT * FROM alerts 
        WHERE acknowledged = FALSE 
        ORDER BY created_at DESC
    """
    df = pd.read_sql(query, conn)
    return df

def get_acknowledged_alerts(limit=10):
    """Get recently acknowledged alerts"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    query = """
        SELECT * FROM alerts 
        WHERE acknowledged = TRUE 
        ORDER BY acknowledged_at DESC 
        LIMIT %s
    """
    df = pd.read_sql(query, conn, params=(limit,))
    return df

def acknowledge_alert(alert_id):
    """Acknowledge an alert (no longer affects production line)"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Only update alert as acknowledged - DO NOT restart production line
        cursor.execute("""
            UPDATE alerts 
            SET acknowledged = TRUE, acknowledged_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (alert_id,))
        
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        st.error(f"Error acknowledging alert: {e}")
        conn.rollback()
        return False

def create_trend_chart(df, parameter, title):
    """Create line chart for parameter trends"""
    if df.empty:
        return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df[parameter],
        mode='lines+markers',
        name=parameter,
        line=dict(width=2)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Sample",
        yaxis_title=parameter,
        height=250,
        margin=dict(l=50, r=50, t=40, b=40)
    )
    
    return fig

# Main Dashboard
def main():
    # Header
    st.markdown('<div class="main-header">🔬 Smart Semiconductor Manufacturing Using IIoT Architecture</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Predictive Quality and Fault Detection System</div>', unsafe_allow_html=True)

    
    # Sidebar controls
    st.sidebar.markdown("### Dashboard Controls")
    refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 1, 10, 2)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### System Status")
    st.sidebar.info("✅ Database: Connected")
    
    # Auto-refresh using st.empty() + while loop
    placeholder = st.empty()
    
    # Create separate placeholders for statistics to prevent duplication
    stats_placeholder = st.empty()
    
    refresh_count = 0

    while True:
        refresh_count += 1
        with placeholder.container():
    
            # Get production line status
            line_status_df = get_production_line_status()
    
            # Production Lines Section
            st.markdown("## 🏭 Production Lines")
    
            if not line_status_df.empty:
                cols = st.columns(3)
                
                for idx, (_, line) in enumerate(line_status_df.iterrows()):
                    with cols[idx]:
                        st.markdown(f"### {line['line_name']}")
                        
                        # Status badge - now only shows Running or Idle
                        status = line['status']
                        if status == 'Idle':
                            st.markdown(f'<div class="status-idle">⚪ IDLE</div>', unsafe_allow_html=True)
                        else:
                            # Always show Running (ignore Stopped status)
                            st.markdown(f'<div class="status-running">🟢 RUNNING</div>', unsafe_allow_html=True)
                        
                        # Current wafer
                        if line['current_wafer_id']:
                            st.markdown(f"**Current Wafer:** `{line['current_wafer_id']}`")
                        else:
                            st.markdown("**Current Wafer:** None")
                        
                        st.markdown(f"**Last Updated:** {line['last_updated']}")
                        
                        # Get latest sensor data for this line
                        sensor_df = get_latest_sensor_data(line['line_name'], limit=20)
                        
                        if not sensor_df.empty and status != 'Idle':
                            st.markdown("#### 📊 Process Parameters")
                            
                            # Reverse for chronological order
                            sensor_df = sensor_df.iloc[::-1].reset_index(drop=True)
                            
                            # Key metrics
                            latest = sensor_df.iloc[-1]
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Temperature (°C)", f"{latest['chamber_temperature']:.1f}")
                                st.metric("RF Power (W)", f"{latest['rf_power']:.1f}")
                            with col2:
                                st.metric("Gas Flow (sccm)", f"{latest['gas_flow_rate']:.1f}")
                                st.metric("Vacuum (Torr)", f"{latest['vacuum_pressure']:.3f}")
                            
                            # Trend charts
                            st.markdown("#### 📈 Parameter Trends (Last 20 Samples)")
                            
                            # Temperature trend
                            fig1 = create_trend_chart(sensor_df, 'chamber_temperature', 'Chamber Temperature')
                            st.plotly_chart(fig1, use_container_width=True, key=f"temp_{line['line_name']}_{refresh_count}")
                            
                            # Pressure trend
                            fig2 = create_trend_chart(sensor_df, 'vacuum_pressure', 'Vacuum Pressure')
                            st.plotly_chart(fig2, use_container_width=True, key=f"pressure_{line['line_name']}_{refresh_count}")
                            
                            # Defect probability
                            if 'defect_probability' in sensor_df.columns:
                                fig3 = create_trend_chart(sensor_df, 'defect_probability', 'Defect Probability')
                                st.plotly_chart(fig3, use_container_width=True, key=f"defect_{line['line_name']}_{refresh_count}")
            
            st.markdown("---")
    
            # Alerts Section
            st.markdown("## 🚨 Alert Management")
               
            active_alerts = get_active_alerts()
                
            if active_alerts.empty:
                st.markdown('<div class="no-alert-box">✅ <b>No Active Alerts</b></div>', unsafe_allow_html=True)
            else:
                st.markdown(f"### ⚠️ Active Alerts ({len(active_alerts)})")
                    
                for _, alert in active_alerts.iterrows():
                    with st.container():
                        st.markdown(f'<div class="alert-box">', unsafe_allow_html=True)
                        col1, col2, col3 = st.columns([3, 2, 1])
                            
                        with col1:
                            st.markdown(f"**Production Line:** {alert['production_line']}")
                            st.markdown(f"**Wafer ID:** `{alert['wafer_id']}`")
                            st.markdown(f"**Message:** {alert['alert_message']}")
                            
                        with col2:
                            st.markdown(f"**Defect Probability:** {alert['defect_probability']:.2%}")
                            st.markdown(f"**Time:** {alert['created_at']}")
                    
                        with col3:
                            if st.button(f"✓ Acknowledge", key=f"ack_{alert['id']}_{refresh_count}"):
                                if acknowledge_alert(alert['id']):
                                    st.toast("Alert acknowledged!", icon="✅")
                                    
                                    st.rerun()
                                else:
                                    st.error("Failed to acknowledge alert")
                    
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown("")
            
            # Past Alerts
            st.markdown("### 📋 Past Alerts")
            past_alerts = get_acknowledged_alerts(limit=10)
            
            if not past_alerts.empty:
                past_alerts['Status'] = 'Acknowledged ✓'
                display_df = past_alerts[['production_line', 'wafer_id', 'defect_probability', 
                                           'created_at', 'acknowledged_at', 'Status']].copy()
                display_df.columns = ['Production Line', 'Wafer ID', 'Defect Prob.', 
                                       'Alert Time', 'Acknowledged At', 'Status']
                display_df['Defect Prob.'] = display_df['Defect Prob.'].apply(lambda x: f"{x:.2%}")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No past alerts")
            
            st.markdown("---")
        
        # Statistics Section - OUTSIDE main container to prevent duplication
        with stats_placeholder.container():
            st.markdown("## 📊 System Statistics")
            
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Fetch all data first
                cursor.execute("SELECT COUNT(*) FROM sensor_data")
                total_wafers = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM sensor_data WHERE predicted_defect = 1")
                total_defects = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM alerts")
                total_alerts = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = TRUE")
                ack_alerts = cursor.fetchone()[0]
                
                cursor.close()
                
                # Display all metrics at once (no key parameter needed)
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Wafers Processed", total_wafers)
                col2.metric("Defects Detected", total_defects)
                col3.metric("Total Alerts", total_alerts)
                col4.metric("Acknowledged Alerts", ack_alerts)
        
        # Sleep before refresh - OUTSIDE the container
        time.sleep(refresh_rate)    

if __name__ == "__main__":
    main()