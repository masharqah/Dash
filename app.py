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
        padding: 2.5rem 2rem; margin: 1rem 0 2rem 0; border-radius: 12px;
        color: white; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.25);
    }
    .metric-container {
        background-color: white; padding: 1.5rem; border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-left: 5px solid #2a5298;
        text-align: center; height: 100%;
    }
    .metric-value { font-size: 2.5rem; font-weight: 700; color: #2a5298; }
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

# --- Functions ---
@st.cache_data(ttl=86400)
def get_access_token(username, password, token_url):
    # FIX: Correct Headers for OAuth
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'username': username,
        'password': password,
        'grant_type': "password",
        'client_id': "acled"
    }
    try:
        response = requests.post(token_url, headers=headers, data=data) # FIX: Use data= instead of json=
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        st.error(f"Authentication Failed: {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_acled_data(token, countries, start_date, end_date):
    headers = {"Authorization": f"Bearer {token}"}
    all_dfs = []
    
    for country in countries:
        parameters = {
            "country": country,
            "event_date": f"{start_date}|{end_date}",
            "event_date_where": "BETWEEN",
            "limit": "5000", # FIX: Set a high limit instead of 0
        }
        try:
            response = requests.get(ACLED_CONFIG["api_read_url"], params=parameters, headers=headers)
            data = response.json()
            if data.get("status") == 200 and data.get("data"):
                all_dfs.append(pd.DataFrame(data["data"]))
        except Exception as e:
            st.warning(f"Failed for {country}: {e}")

    return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    try:
        # Standardized secrets path
        email = st.secrets["acled"]["email"]
        password = st.secrets["acled"]["password"]
        st.success("✅ Credentials loaded")
    except:
        st.error("❌ Credentials missing in Secrets")
        st.stop()

    countries_input = st.text_input("Countries", "Palestine, Israel")
    countries_list = [c.strip() for c in countries_input.split(',')]
    
    col1, col2 = st.columns(2)
    start_date = col1.date_input("From", date.today() - timedelta(days=30))
    end_date = col2.date_input("To", date.today())

    fetch_button = st.button("🚀 Fetch Data", type="primary", use_container_width=True)

if fetch_button:
    token = get_access_token(email, password, ACLED_CONFIG["token_url"])
    if token:
        with st.spinner("Fetching data..."):
            df = fetch_acled_data(token, countries_list, start_date, end_date)
            if not df.empty:
                df['event_date'] = pd.to_datetime(df['event_date'])
                df[["latitude", "longitude"]] = df[["latitude", "longitude"]].apply(pd.to_numeric)
                df["fatalities"] = pd.to_numeric(df["fatalities"]).fillna(0)
                st.session_state.original_df = df
                st.session_state.data_fetched_successfully = True
                st.rerun()

# --- Main Dashboard ---
if st.session_state.data_fetched_successfully:
    df = st.session_state.original_df.copy()
    
    # Simple Metrics Row
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Events", len(df))
    m2.metric("Total Fatalities", int(df["fatalities"].sum()))
    m3.metric("Regions", df["admin1"].nunique())

    # Map Controls
    map_type = st.radio("Map Mode", ["Categories", "Heatmap"], horizontal=True)
    
    # Layer Setup
    if map_type == "Categories":
        # Create discrete colors
        unique_types = df["event_type"].unique()
        color_map = {t: [255, 100, 50, 150] for t in unique_types} # Example static color
        df['color'] = df['event_type'].map(color_map)
        layer = pdk.Layer("ScatterplotLayer", df, get_position='[longitude, latitude]', 
                          get_color='[200, 30, 0, 160]', get_radius=1500, pickable=True)
    else:
        layer = pdk.Layer("HeatmapLayer", df, get_position='[longitude, latitude]', get_weight="fatalities")

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=pdk.ViewState(
        latitude=df["latitude"].mean(), longitude=df["longitude"].mean(), zoom=6
    )))

    st.dataframe(df, use_container_width=True)
