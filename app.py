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
    /* Main container and text styling */
    .stApp {
        background-color: #f0f2f6;
        color: #333;
        font-family: 'Inter', sans-serif;
    }
    
    /* Branded Header */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2.5rem 2rem;
        margin: 1rem 0 2rem 0;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
        opacity: 0.95;
    }
    .main-header h1 {
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 6px rgba(0,0,0,0.4);
    }
    .main-header p {
        font-size: 1.2rem;
        margin-top: 0.5rem;
        opacity: 0.9;
    }
    
    /* Sleek Metric Cards */
    .metric-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #2a5298;
        transition: transform 0.2s, box-shadow 0.2s;
        text-align: center;
        height: 100%;
    }
    .metric-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2a5298;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
        font-weight: 500;
        margin-top: 0.2rem;
    }
    
    /* Legend Styling */
    .legend-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        height: fit-content;
        margin-left: 1rem;
    }
    .legend-title {
        color: #2a5298;
        font-weight: 600;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }

    /* Sidebar sections */
    .sidebar .st-cd {
        border-left: 3px solid #2a5298;
        padding-left: 1rem;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            padding: 2rem 1rem;
        }
        .main-header h1 {
            font-size: 2rem;
        }
        .metric-container {
            margin-bottom: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Branded header ---
st.markdown("""
<div class="main-header">
    <h1>🌍  Security Data Explorer</h1>
    <p>Advanced analytics for Security events</p>
</div>
""", unsafe_allow_html=True)

# --- Configuration for OAuth authentication ---
ACLED_CONFIG = {
    "token_url": "https://acleddata.com/oauth/token",
    "api_read_url": "https://acleddata.com/api/acled/read?_format=json",
}

# --- Initialize session state ---
if 'original_df' not in st.session_state:
    st.session_state.original_df = pd.DataFrame()
if 'data_fetched_successfully' not in st.session_state:
    st.session_state.data_fetched_successfully = False
if 'map_selection' not in st.session_state:
    st.session_state.map_selection = "Categorized Map (by Event Type)"
if 'selected_temporal_date' not in st.session_state:
    st.session_state.selected_temporal_date = None
if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False
if 'date_index' not in st.session_state:
    st.session_state.date_index = 0

# --- Functions for authentication and data fetching ---
@st.cache_data(ttl=86400)
def get_access_token(username, password, token_url):
    """
    Retrieves a temporary access token using OAuth password grant flow.
    """
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
          'username': username,
          'password': password,
          'grant_type': "password",
          'client_id': "acled"
    }
    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        return token_data['access_token']
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to get access token: {e}")
        st.stop()

@st.cache_data(ttl=3600)
def fetch_acled_data(token, countries, start_date, end_date):
    """
    Fetches conflict data from the ACLED API using the provided access token.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    all_fetched_dfs = []
    formatted_start_date = start_date.strftime("%Y-%m-%d")
    formatted_end_date = end_date.strftime("%Y-%m-%d")

    for country in countries:
        parameters = {
            "country": country,
            "event_date": f"{formatted_start_date}|{formatted_end_date}",
            "event_date_where": "BETWEEN",
            "limit": "0",
            "fields": "event_id_cnty|event_date|event_type|sub_event_type|country|admin1|admin2|location|fatalities|latitude|longitude|notes|actor1|actor2"
        }
        try:
            response = requests.get(
                ACLED_CONFIG["api_read_url"],
                params=parameters,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                if data.get("data"):
                    df_country = pd.DataFrame(data["data"])
                    all_fetched_dfs.append(df_country)
            else:
                st.warning(f"API request failed for {country}: {data.get('message')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch data for {country}: {e}")
            continue

    if all_fetched_dfs:
        return pd.concat(all_fetched_dfs, ignore_index=True)
    else:
        return pd.DataFrame()

# --- Sidebar Configuration ---
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    with st.container():
        st.markdown("**🌐 Data Source**")
        
        # Credentials section
        try:
            email = st.secrets["acled"]["email"]
            password = st.secrets["acled"]["password"]
            st.success("✅ Credentials loaded")
        except KeyError:
            st.error("❌ Missing API credentials")
            st.info("Configure your .streamlit/secrets.toml file with 'email' and 'password'")
            st.stop()

        countries_input = st.text_input(
            "Countries (comma-separated)",
            "Palestine, Israel",
            help="Enter country names separated by commas"
        )
        countries_list = [c.strip() for c in countries_input.split(',') if c.strip()]
        
        today = date.today()
        default_start_date = today - timedelta(days=30)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("📅 From", value=default_start_date)
        with col2:
            end_date = st.date_input("📅 To", value=today)

    # Fetch data button
    st.markdown("---")
    fetch_button = st.button(
        "🚀 Fetch Data",
        type="primary",
        use_container_width=True,
        help="Click to retrieve latest data "
    )

# --- Data Fetching Logic ---
if fetch_button:
    if end_date < start_date:
        st.error("📅 Please correct the date range")
    else:
        with st.spinner("🔄 Authenticating and fetching data..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Authenticate
            status_text.text("Authenticating ...")
            progress_bar.progress(0.2)
            access_token = get_access_token(email, password, ACLED_CONFIG["token_url"])
            
            # Fetch data
            status_text.text("Fetching conflict data...")
            progress_bar.progress(0.8)
            fetched_df = fetch_acled_data(access_token, countries_list, start_date, end_date)
            
            if not fetched_df.empty:
                # Data processing
                if 'event_date' in fetched_df.columns:
                    fetched_df['event_date'] = pd.to_datetime(fetched_df['event_date'], errors='coerce')
                
                fetched_df["latitude"] = pd.to_numeric(fetched_df["latitude"], errors="coerce")
                fetched_df["longitude"] = pd.to_numeric(fetched_df["longitude"], errors="coerce")
                fetched_df["fatalities"] = pd.to_numeric(fetched_df["fatalities"], errors="coerce").fillna(0)
                fetched_df = fetched_df.dropna(subset=["latitude", "longitude"])
                
                st.session_state.original_df = fetched_df.copy()
                st.session_state.data_fetched_successfully = True
                
                if not fetched_df.empty and 'event_date' in fetched_df.columns:
                    st.session_state.selected_temporal_date = fetched_df['event_date'].min().date()

                progress_bar.empty()
                status_text.empty()
                st.success(f"✅ Successfully loaded {len(st.session_state.original_df)} events")
            else:
                st.error("❌ No data could be fetched for the selected criteria. Please check your inputs and try again.")

# --- Main Dashboard Content ---
if st.session_state.data_fetched_successfully and not st.session_state.original_df.empty:
    filtered_df = st.session_state.original_df.copy()

    # Professional sidebar filters
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🎯 Filter Data")
        
        with st.expander("🗺️ Geographic Filters", expanded=True):
            for admin_level, (icon, label) in enumerate([
                ("📍", "State/Province"),
                ("🏙️", "County/District")
            ], 1):
                admin_col = f"admin{admin_level}"
                if admin_col in filtered_df.columns:
                    unique_values = filtered_df[admin_col].dropna().unique().tolist()
                    if unique_values:
                        selected = st.multiselect(
                            f"{icon} {label}",
                            sorted(unique_values),
                            key=f"admin{admin_level}_select"
                        )
                        if selected:
                            filtered_df = filtered_df[filtered_df[admin_col].isin(selected)]
        
        with st.expander("🏷️ Event Categories", expanded=False):
            if "event_type" in filtered_df.columns:
                unique_event_types = filtered_df["event_type"].dropna().unique().tolist()
                if unique_event_types:
                    selected_event_types = st.multiselect(
                        "Select Event Type(s)",
                        sorted(unique_event_types)
                    )
                    if selected_event_types:
                        filtered_df = filtered_df[filtered_df["event_type"].isin(selected_event_types)]
    
        with st.expander("🎨 Map Customization", expanded=False):
            map_style_options = {
                "🌙 Dark": "mapbox://styles/mapbox/dark-v10",
                "☀️ Light": "mapbox://styles/mapbox/light-v10",
                "🛰️ Satellite": "mapbox://styles/mapbox/satellite-v9",
                "🗺️ Streets": "mapbox://styles/mapbox/streets-v11"
            }
            selected_style = st.selectbox(
                "Base Map Style",
                list(map_style_options.keys()),
                index=1
            )
            map_height = st.slider(
                "Map Height",
                min_value=400,
                max_value=800,
                value=600,
                step=50
            )

    # --- Main Content Area ---
    if not filtered_df.empty:
        st.markdown("---")
        
        # Enhanced metrics dashboard
        st.markdown("### 📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_events = len(filtered_df)
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{total_events:,}</div>
                <div class="metric-label">Total Events</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            total_fatalities = int(filtered_df["fatalities"].sum()) if "fatalities" in filtered_df.columns else 0
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{total_fatalities:,}</div>
                <div class="metric-label">Total Fatalities</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            unique_locations = filtered_df["admin1"].nunique() if "admin1" in filtered_df.columns else 0
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{unique_locations}</div>
                <div class="metric-label">Affected Regions</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            date_range = (filtered_df["event_date"].max() - filtered_df["event_date"].min()).days if "event_date" in filtered_df.columns else 0
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{date_range}</div>
                <div class="metric-label">Days Covered</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Enhanced visualization layout
        map_col, legend_col = st.columns([5, 1])
        
        with map_col:
            st.markdown("### 🗺️ Geospatial Distribution")
            
            # Map Type Selection Buttons
            st.markdown("#### Select Map Type:")
            map_buttons_cols = st.columns(4)
            with map_buttons_cols[0]:
                if st.button("🎨 Categories", key="categories_button", use_container_width=True):
                    st.session_state.map_selection = "Categorized Map (by Event Type)"
            with map_buttons_cols[1]:
                if st.button("🔥 Heatmap", key="heatmap_button", use_container_width=True):
                    st.session_state.map_selection = "Heatmap (Event Density)"
            with map_buttons_cols[2]:
                if st.button("🎯 Impact", key="impact_button", use_container_width=True):
                    st.session_state.map_selection = "Scatterplot (by Fatalities)"
            with map_buttons_cols[3]:
                if st.button("⏳ Temporal", key="temporal_button", use_container_width=True):
                    st.session_state.map_selection = "Temporal Map (Time Slider)"
            
            st.markdown("---")
            display_df = filtered_df.copy()

            # Temporal Slider Logic
            if st.session_state.map_selection == "Temporal Map (Time Slider)":
                if 'event_date' in display_df.columns and not display_df.empty:
                    unique_dates = sorted(display_df['event_date'].dt.date.unique())
                    if len(unique_dates) <= 1:
                        st.info("Only one date available for temporal analysis")
                        if unique_dates:
                            display_df = display_df[display_df['event_date'].dt.date == unique_dates[0]]
                    else:
                        min_date_slider = unique_dates[0]
                        max_date_slider = unique_dates[-1]

                        if st.session_state.selected_temporal_date is None or \
                           st.session_state.selected_temporal_date < min_date_slider or \
                           st.session_state.selected_temporal_date > max_date_slider:
                            st.session_state.selected_temporal_date = min_date_slider

                        selected_date = st.slider(
                            "Select Date for Temporal Map",
                            min_value=min_date_slider,
                            max_value=max_date_slider,
                            value=st.session_state.selected_temporal_date,
                            format="YYYY-MM-DD"
                        )
                        
                        play_col, stop_col = st.columns(2)
                        with play_col:
                            if st.button("▶️ Play Animation", use_container_width=True):
                                st.session_state.is_playing = True
                        with stop_col:
                            if st.button("⏸️ Stop Animation", use_container_width=True):
                                st.session_state.is_playing = False
                        
                        display_df = display_df[display_df['event_date'].dt.date == selected_date]
                        st.write(f"Displaying events for: **{selected_date.strftime('%Y-%m-%d')}**")
                        
                        if st.session_state.is_playing:
                            time.sleep(0.5)
                            current_index = unique_dates.index(selected_date)
                            next_index = (current_index + 1) % len(unique_dates)
                            st.session_state.selected_temporal_date = unique_dates[next_index]
                            st.rerun()

            if not display_df.empty:
                display_df['event_date_str'] = display_df['event_date'].dt.strftime('%Y-%m-%d')
            
            # Map rendering
            if not display_df.empty:
                view_state = pdk.ViewState(
                    latitude=display_df["latitude"].mean(),
                    longitude=display_df["longitude"].mean(),
                    zoom=7,
                    pitch=0,
                )
            else:
                view_state = pdk.ViewState(
                    latitude=31.9522,  # Center of Palestine
                    longitude=35.2332,
                    zoom=7,
                    pitch=0,
                )
            
            tooltip = {
                "html": """
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                             color: white; padding: 10px; border-radius: 8px; font-family: Arial;
                             max-width: 350px;">
                     <b>🎯 {event_type}</b><br/>
                    <b>📅 Date:</b> {event_date_str}<br/>
                    <b>📍 Location:</b> {location}<br/>
                    <b>💔 Fatalities:</b> {fatalities}<br/>
                    <b>📝 Notes:</b> {notes}
                </div>
                """,
                "style": {"backgroundColor": "transparent", "color": "white"},
            }
            
            layers = []
            legend_data = None
            map_type = st.session_state.map_selection
            
            if map_type == "Categorized Map (by Event Type)":
                if "event_type" in display_df.columns and not display_df.empty:
                    unique_event_types = st.session_state.original_df["event_type"].dropna().unique()
                    colors = plt.cm.get_cmap('Set3', len(unique_event_types))
                    event_type_colors = {
                        event_type: [int(c * 255) for c in colors(i)[:3]] + [180]
                        for i, event_type in enumerate(unique_event_types)
                    }
                    display_df['color'] = display_df['event_type'].map(event_type_colors)
                    legend_data = {
                        'type': 'categorized',
                        'items': [(event_type, f"rgb({color[0]}, {color[1]}, {color[2]})") 
                                  for event_type, color in event_type_colors.items()]
                    }
                    layers.append(
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=display_df,
                            get_position='[longitude, latitude]',
                            get_color='color',
                            get_radius=1000,
                            pickable=True,
                            auto_highlight=True
                        )
                    )
            elif map_type == "Heatmap (Event Density)" or map_type == "Temporal Map (Time Slider)":
                layers.append(
                    pdk.Layer(
                        "HeatmapLayer",
                        data=display_df,
                        get_position='[longitude, latitude]',
                        opacity=0.7,
                        threshold=0.04,
                        aggregation='SUM',
                        get_weight=1
                    )
                )
                legend_data = {'type': 'heatmap'}
            elif map_type == "Scatterplot (by Fatalities)":
                if "fatalities" in display_df.columns and display_df["fatalities"].max() > 0:
                    max_fatalities = display_df["fatalities"].max()
                    min_fatalities = display_df["fatalities"].min()
                    display_df['radius'] = (display_df['fatalities'] / max_fatalities) * 5000 + 500
                    legend_data = {
                        'type': 'fatalities',
                        'min_fatalities': int(min_fatalities),
                        'max_fatalities': int(max_fatalities)
                    }
                else:
                    display_df['radius'] = 600
                    legend_data = {'type': 'fatalities', 'min_fatalities': 0, 'max_fatalities': 0}
                layers.append(
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=display_df,
                        get_position='[longitude, latitude]',
                        get_color='[255, 100, 100, 180]',
                        get_radius='radius',
                        pickable=True,
                        auto_highlight=True
                    )
                )

            # Render the map
            st.pydeck_chart(pdk.Deck(
                layers=layers,
                initial_view_state=view_state,
                tooltip=tooltip,
                map_style=map_style_options[selected_style]
            ), use_container_width=True, height=map_height)

        # Professional legend
        with legend_col:
            st.markdown('<div class="legend-container">', unsafe_allow_html=True)
            st.markdown('<div class="legend-title">🏷️ Legend</div>', unsafe_allow_html=True)
            
            if legend_data:
                if legend_data['type'] == 'categorized':
                    for event_type, color in legend_data['items']:
                        st.markdown(
                            f'<div style="display: flex; align-items: center; margin-bottom: 8px;">'
                            f'<div style="width: 16px; height: 16px; border-radius: 50%; '
                            f'background-color: {color}; margin-right: 10px; '
                            f'box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div>'
                            f'<span style="font-size: 11px; color: #333;">{event_type}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                elif legend_data['type'] == 'heatmap':
                    gradient_html = '''
                    <div style="margin-bottom: 15px;">
                        <div style="background: linear-gradient(to right,
                                         rgba(0,0,255,0.2), rgba(0,255,0,0.6),
                                         rgba(255,255,0,0.8), rgba(255,0,0,1));
                                         height: 25px; width: 100%; border-radius: 12px;
                                         box-shadow: 0 2px 4px rgba(0,0,0,0.1);"></div>
                        <div style="display: flex; justify-content: space-between;
                                         font-size: 9px; color: #666; margin-top: 5px;">
                            <span>Low Density</span>
                            <span>High Density</span>
                        </div>
                    </div>
                    '''
                    st.markdown(gradient_html, unsafe_allow_html=True)
                elif legend_data['type'] == 'fatalities':
                    if legend_data['max_fatalities'] > 0:
                        sizes = [(legend_data['min_fatalities'], '10px')]
                        if legend_data['max_fatalities'] > 1:
                            mid_fatalities = int(legend_data['min_fatalities'] + (legend_data['max_fatalities'] - legend_data['min_fatalities']) / 2)
                            if mid_fatalities > legend_data['min_fatalities']:
                                sizes.append((mid_fatalities, '18px'))
                        sizes.append((legend_data['max_fatalities'], '26px'))
                        
                        for fatalities, size in sizes:
                            st.markdown(
                                f'<div style="display: flex; align-items: center; margin-bottom: 10px;">'
                                f'<div style="width: {size}; height: {size}; border-radius: 50%; '
                                f'background-color: rgba(255,100,100,0.8); margin-right: 10px; '
                                f'box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div>'
                                f'<span style="font-size: 10px; color: #333;">{fatalities} fatalities</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Enhanced analytics panel
        with st.container():
            st.markdown("### 📈 Analytics Dashboard")
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                if "event_type" in filtered_df.columns:
                    event_counts = filtered_df["event_type"].value_counts()
                    if not event_counts.empty:
                        fig = px.pie(
                            values=event_counts.values,
                            names=event_counts.index,
                            title="Event Distribution",
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig.update_layout(
                            font=dict(size=10),
                            showlegend=True,
                            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01),
                            margin=dict(l=0, r=0, t=30, b=0),
                            height=300
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with col_chart2:
                if "event_date" in filtered_df.columns:
                    daily_events = filtered_df.groupby(filtered_df['event_date'].dt.date).size().reset_index()
                    daily_events.columns = ['date', 'events']
                    if not daily_events.empty:
                        fig = px.line(
                            daily_events, 
                            x='date', 
                            y='events',
                            title="Event Timeline",
                            color_discrete_sequence=['#667eea']
                        )
                        fig.update_layout(
                            font=dict(size=10),
                            margin=dict(l=0, r=0, t=30, b=0),
                            height=300
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 📊 Regional Analysis")
            
            if "admin1" in filtered_df.columns:
                admin1_values = filtered_df["admin1"].dropna().unique().tolist()
                selected_admin1s = st.multiselect("🗂️ Select Regions for Bar Chart", sorted(admin1_values))
                if selected_admin1s:
                    admin1_filtered_df = filtered_df[filtered_df["admin1"].isin(selected_admin1s)]
                    if not admin1_filtered_df.empty and "admin2" in admin1_filtered_df.columns and "event_type" in admin1_filtered_df.columns:
                        chart_data = admin1_filtered_df.groupby(["admin2", "event_type"]).size().reset_index(name="count")
                        total_counts = chart_data.groupby("admin2")["count"].sum().reset_index(name="total")
                        chart_data = chart_data.merge(total_counts, on="admin2")
                        fig = px.bar(
                            chart_data,
                            y="admin2",
                            x="count",
                            color="event_type",
                            orientation="h",
                            labels={"count": "Number of Events", "admin2": "District"},
                            color_discrete_sequence=px.colors.qualitative.Set3,
                            title="Events by District and Event Type"
                        )
                        for trace in fig.data:
                            trace.text = [str(int(c)) for c in trace.x]
                            trace.textposition = "inside"
                        for admin2, total in total_counts.values:
                            fig.add_annotation(
                                x=total,
                                y=admin2,
                                text=f"{total}",
                                showarrow=False,
                                xanchor="left",
                                yanchor="middle",
                                font=dict(size=10, color="black", weight="bold"),
                                bgcolor="rgba(255,255,255,0.7)",
                            )
                        fig.update_layout(
                            barmode="stack",
                            height=600,
                            margin=dict(l=100, r=10, t=50, b=40),
                            yaxis_title="admin2",
                            xaxis_title="Number of Events"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
        # Enhanced data table
        st.markdown("---")
        with st.expander("📊 Detailed Data Explorer", expanded=False):
            search_term = st.text_input("🔍 Search in data:", placeholder="Enter search term...")
            
            if search_term:
                mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                display_data = filtered_df[mask]
            else:
                display_data = filtered_df
            
            # Select relevant columns to display
            display_columns = [
                'event_date', 'event_type', 'sub_event_type', 'country',
                'admin1', 'admin2', 'location', 'fatalities', 'actor1', 'actor2', 'notes'
            ]
            available_columns = [col for col in display_columns if col in display_data.columns]
            
            st.dataframe(
                display_data[available_columns],
                use_container_width=True,
                height=400
            )
            
            # Export functionality
            csv = display_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"acled_data_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("🔍 No events found matching the selected filters. Try adjusting your selections.")

else:
    # Professional welcome screen
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
        <h2 style="color: #1e3c72; font-weight: 700; font-size: 2rem;">Welcome to the  Data Explorer</h2>
        <p style="color: #555; font-size: 1.1rem; margin-top: 1rem;">
            This application allows you to explore security incidents data with advanced filtering,
            geospatial analysis, and interactive charts.
        </p>
        <p style="color: #777; font-size: 0.95rem; margin-top: 2rem;">
            To get started, please use the sidebar on the left to select your countries and date range,
            then click the <b>'Fetch Data'</b> button.
        </p>
    </div>
    """, unsafe_allow_html=True)
