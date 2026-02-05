import streamlit as st
import requests
import json
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
from datetime import date, timedelta
import plotly.express as px
import time

# --- Set Streamlit page configuration ---
st.set_page_config(
    page_title="Security Data Explorer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for professional styling ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; color: #333; font-family: 'Inter', sans-serif; }
    
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2.5rem 2rem; margin: 1rem 0 2rem 0;
        border-radius: 12px; color: white; text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
    }
    .main-header h1 { font-size: 2.8rem; font-weight: 800; margin: 0; }
    
    .metric-container {
        display: flex; flex-direction: column; justify-content: center;
        align-items: center; background-color: white; padding: 1.5rem;
        border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #2a5298; transition: transform 0.2s;
        text-align: center; height: 100%;
    }
    .metric-container:hover { transform: translateY(-5px); }
    .metric-value { font-size: 2.5rem; font-weight: 700; color: #2a5298; line-height: 1.2; }
    .metric-label { font-size: 1rem; color: #555; font-weight: 500; }
    
    .legend-container {
        background: white; padding: 1.5rem; border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1); border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="main-header"><h1>🌍 Security Data Explorer</h1><p>Advanced analytics for Security events</p></div>""", unsafe_allow_html=True)

ACLED_CONFIG = {
    "token_url": "https://acleddata.com/oauth/token",
    "api_read_url": "https://acleddata.com/api/acled/read?_format=json",
}

# --- Initialize session state ---
if 'original_df' not in st.session_state: st.session_state.original_df = pd.DataFrame()
if 'data_fetched_successfully' not in st.session_state: st.session_state.data_fetched_successfully = False
if 'map_selection' not in st.session_state: st.session_state.map_selection = "Categorized Map (by Event Type)"
if 'selected_temporal_date' not in st.session_state: st.session_state.selected_temporal_date = None
if 'is_playing' not in st.session_state: st.session_state.is_playing = False

# --- Core Functions ---
@st.cache_data(ttl=86400)
def get_access_token(username, password, token_url):
    # FIXED: Headers and Data for OAuth 415 Error
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'username': username,
        'password': password,
        'grant_type': "password",
        'client_id': "acled"
    }
    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        st.error(f"Failed to get access token: {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_acled_data(token, countries, start_date, end_date):
    headers = {"Authorization": f"Bearer {token}"}
    all_fetched_dfs = []
    
    for country in countries:
        parameters = {
            "country": country,
            "event_date": f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
            "event_date_where": "BETWEEN",
            "limit": "5000" # Set high limit
        }
        try:
            response = requests.get(ACLED_CONFIG["api_read_url"], params=parameters, headers=headers)
            data = response.json()
            if data.get("status") == 200 and data.get("data"):
                all_fetched_dfs.append(pd.DataFrame(data["data"]))
        except Exception as e:
            st.warning(f"Error fetching {country}: {e}")
            
    return pd.concat(all_fetched_dfs, ignore_index=True) if all_fetched_dfs else pd.DataFrame()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    try:
        email = st.secrets["acled"]["email"]
        password = st.secrets["acled"]["password"]
        st.success("✅ Credentials loaded")
    except:
        st.error("❌ Missing API credentials in Secrets")
        st.stop()

    countries_input = st.text_input("Countries", "Palestine, Israel")
    countries_list = [c.strip() for c in countries_input.split(',')]
    
    col1, col2 = st.columns(2)
    start_date = col1.date_input("From", date.today() - timedelta(days=30))
    end_date = col2.date_input("To", date.today())

    st.markdown("---")
    fetch_button = st.button("🚀 Fetch Data", type="primary", use_container_width=True)

# --- Fetching Logic ---
if fetch_button:
    token = get_access_token(email, password, ACLED_CONFIG["token_url"])
    if token:
        with st.spinner("🔄 Fetching conflict data..."):
            fetched_df = fetch_acled_data(token, countries_list, start_date, end_date)
            if not fetched_df.empty:
                # Processing
                fetched_df['event_date'] = pd.to_datetime(fetched_df['event_date'])
                fetched_df["latitude"] = pd.to_numeric(fetched_df["latitude"], errors="coerce")
                fetched_df["longitude"] = pd.to_numeric(fetched_df["longitude"], errors="coerce")
                fetched_df["fatalities"] = pd.to_numeric(fetched_df["fatalities"], errors="coerce").fillna(0)
                fetched_df = fetched_df.dropna(subset=["latitude", "longitude"])
                
                st.session_state.original_df = fetched_df
                st.session_state.data_fetched_successfully = True
                st.session_state.selected_temporal_date = fetched_df['event_date'].min().date()
                st.rerun()

# --- Main Content ---
if st.session_state.data_fetched_successfully:
    full_df = st.session_state.original_df.copy()
    
    # Restored Key Metrics
    st.markdown("### 📊 Key Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-container"><div class="metric-value">{len(full_df):,}</div><div class="metric-label">Events</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><div class="metric-value">{int(full_df["fatalities"].sum()):,}</div><div class="metric-label">Fatalities</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-container"><div class="metric-value">{full_df["admin1"].nunique()}</div><div class="metric-label">Regions</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-container"><div class="metric-value">{(full_df["event_date"].max() - full_df["event_date"].min()).days}</div><div class="metric-label">Days</div></div>', unsafe_allow_html=True)

    # Restored Map Selector Buttons
    st.markdown("---")
    st.markdown("### 🗺️ Geospatial Distribution")
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
    if btn_col1.button("🎨 Categories", use_container_width=True): st.session_state.map_selection = "Categories"
    if btn_col2.button("🔥 Heatmap", use_container_width=True): st.session_state.map_selection = "Heatmap"
    if btn_col3.button("🎯 Impact", use_container_width=True): st.session_state.map_selection = "Impact"
    if btn_col4.button("⏳ Temporal", use_container_width=True): st.session_state.map_selection = "Temporal"

    # Temporal Logic
    display_df = full_df.copy()
    if st.session_state.map_selection == "Temporal":
        unique_dates = sorted(full_df['event_date'].dt.date.unique())
        selected_date = st.slider("Timeline", min_value=unique_dates[0], max_value=unique_dates[-1], value=st.session_state.selected_temporal_date)
        display_df = full_df[full_df['event_date'].dt.date == selected_date]
        
        c1, c2 = st.columns(2)
        if c1.button("▶️ Play"): st.session_state.is_playing = True
        if c2.button("⏸️ Stop"): st.session_state.is_playing = False
        
        if st.session_state.is_playing:
            time.sleep(0.5)
            next_idx = (unique_dates.index(selected_date) + 1) % len(unique_dates)
            st.session_state.selected_temporal_date = unique_dates[next_idx]
            st.rerun()

    # Map Rendering
    map_col, legend_col = st.columns([5, 1])
    with map_col:
        view = pdk.ViewState(latitude=display_df["latitude"].mean(), longitude=display_df["longitude"].mean(), zoom=7)
        
        if st.session_state.map_selection == "Heatmap":
            layer = pdk.Layer("HeatmapLayer", display_df, get_position='[longitude, latitude]', get_weight="fatalities", opacity=0.8)
        elif st.session_state.map_selection == "Impact":
            display_df['radius'] = (display_df['fatalities'] / (display_df['fatalities'].max() or 1)) * 5000 + 1000
            layer = pdk.Layer("ScatterplotLayer", display_df, get_position='[longitude, latitude]', get_radius='radius', get_color='[255, 100, 100, 180]', pickable=True)
        else:
            layer = pdk.Layer("ScatterplotLayer", display_df, get_position='[longitude, latitude]', get_radius=1500, get_color='[30, 80, 255, 160]', pickable=True)
            
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, tooltip={"text": "{event_type}\n{location}\nFatalities: {fatalities}"}))

    # Restored Analytics Dashboard
    st.markdown("---")
    st.markdown("### 📈 Analytics Dashboard")
    ac1, ac2 = st.columns(2)
    with ac1:
        fig1 = px.pie(full_df, names="event_type", title="Event Distribution", color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig1, use_container_width=True)
    with ac2:
        timeline = full_df.groupby(full_df['event_date'].dt.date).size().reset_index(name='events')
        fig2 = px.line(timeline, x='event_date', y='events', title="Event Timeline")
        st.plotly_chart(fig2, use_container_width=True)

    # Data Explorer Expander
    with st.expander("📊 Detailed Data Explorer"):
        st.dataframe(full_df, use_container_width=True)
        st.download_button("📥 Download CSV", full_df.to_csv(index=False), "acled_data.csv", "text/csv")
