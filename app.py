import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
from datetime import date, timedelta
import plotly.express as px
import time # Import for animation delay

# Professional page configuration
st.set_page_config(
    page_title="Events Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🌍"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main dashboard styling */
    .main-header {
        background: linear-gradient(90deg, #1e3c72 30%, #2a5298 70%);
        padding: 2rem 0;
        margin: 1rem 1rem 2rem 1rem;
        border-radius: 15px 15px 15px 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        opacity: 0.9;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Status indicators */
    .metric-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(120deg, #667eea 0%, #764ba2 75%);
    color: white;
    padding: 1.5rem;
    border-radius: 14px;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 700;
        line-height: 1.1;
    }
    
    .metric-label {
        font-size: 1.1rem;
        opacity: 0.95;
    }
    
    /* Map control buttons */
    .map-controls {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
    }
    
    .control-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin: 0.2rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .control-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Legend styling */
    .legend-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        height: fit-content;
    }
    
    .legend-title {
        color: #2a5298;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    
    /* Sidebar enhancements */
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 3px solid #2a5298;
    }
    
    /* Data table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Animation for loading */
    .loading-spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.8rem;
        }
        .metric-container {
            flex-direction: column;
            text-align: center;
        }
    }
</style>
""", unsafe_allow_html=True)

# Professional header
st.markdown("""
<div class="main-header">
    <h1>🌍 Events Intelligence Dashboard</h1>
    <p>crisis monitoring with advanced data analytics</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'original_df' not in st.session_state:
    st.session_state.original_df = pd.DataFrame()
if 'data_fetched_successfully' not in st.session_state:
    st.session_state.data_fetched_successfully = False
# Ensure map_selection is always initialized
if 'map_selection' not in st.session_state:
    st.session_state.map_selection = "Categorized Map (by Event Type)"
# New session state for temporal map slider's selected date
if 'selected_temporal_date' not in st.session_state:
    st.session_state.selected_temporal_date = None
# New session state for animation control
if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False
if 'date_index' not in st.session_state:
    st.session_state.date_index = 0

# --- Professional Sidebar ---
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    
    # Credentials section
    try:
        email = st.secrets["acled"]["email"]
        api_key = st.secrets["acled"]["api_key"]
        st.success("✅ Credentials loaded")
    except KeyError:
        st.error("❌ Missing API credentials")
        st.info("Configure your .streamlit/secrets.toml file")
        st.stop()
    
    # Data source configuration
    #st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("**🌍 Data Sources**")
    countries_input = st.text_input(
        "Countries (comma-separated)",
        "Palestine, Israel",
        help="Enter country names separated by commas"
    )
    countries_list = [c.strip() for c in countries_input.split(',') if c.strip()]
    
    today = date.today()
    default_start_date = today - timedelta(days=16)
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("📅 From", value=default_start_date)
    with col2:
        end_date = st.date_input("📅 To", value=today)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Fetch data button with enhanced styling
    fetch_button = st.button(
        "🚀 Fetch Data",
        type="primary",
        use_container_width=True,
        help="Click to retrieve latest data from ACLED"
    )

# --- Data Fetching Logic ---
if fetch_button:
    if end_date < start_date:
        st.error("📅 Please correct the date range. End date cannot be before start date.")
    else:
        # Professional loading interface
        with st.spinner("🔄 Fetching data from ACLED database..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_fetched_dfs = []
            st.session_state.data_fetched_successfully = False
            # Reset animation state on new data fetch
            st.session_state.is_playing = False
            st.session_state.date_index = 0
            
            formatted_start_date = start_date.strftime("%Y-%m-%d")
            formatted_end_date = end_date.strftime("%Y-%m-%d")

            for i, country in enumerate(countries_list):
                status_text.text(f"Fetching data for {country}...")
                progress_bar.progress((i + 1) / len(countries_list))
                
                url = (f"https://api.acleddata.com/acled/read?"
                       f"key={api_key}&email={email}&country={country}&"
                       f"event_date={formatted_start_date}|{formatted_end_date}&event_date_where=BETWEEN&limit=0")
                
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()

                    if "data" in data and data["data"]:
                        df_country = pd.DataFrame(data["data"])
                        all_fetched_dfs.append(df_country)
                    else:
                        st.warning(f"⚠️ No data found for {country}")
                except Exception as e:
                    st.error(f"❌ Error fetching data for {country}: {str(e)}")

            if all_fetched_dfs:
                full_df_raw = pd.concat(all_fetched_dfs, ignore_index=True)
                
                # Data processing
                if 'event_date' in full_df_raw.columns:
                    full_df_raw['event_date'] = pd.to_datetime(full_df_raw['event_date'], errors='coerce')
                    full_df_raw = full_df_raw[
                        (full_df_raw['event_date'].dt.date >= start_date) &
                        (full_df_raw['event_date'].dt.date <= end_date)
                    ]

                full_df_raw["latitude"] = pd.to_numeric(full_df_raw["latitude"], errors="coerce")
                full_df_raw["longitude"] = pd.to_numeric(full_df_raw["longitude"], errors="coerce")
                full_df_raw["fatalities"] = pd.to_numeric(full_df_raw["fatalities"], errors="coerce").fillna(0)
                full_df_raw = full_df_raw.dropna(subset=["latitude", "longitude"])
                
                st.session_state.original_df = full_df_raw.copy()
                st.session_state.data_fetched_successfully = True
                
                # Set initial temporal date to the earliest date in the fetched data
                if not full_df_raw.empty and 'event_date' in full_df_raw.columns:
                    st.session_state.selected_temporal_date = full_df_raw['event_date'].min().date()
                else:
                    st.session_state.selected_temporal_date = None

                progress_bar.empty()
                status_text.empty()
                st.success(f"✅ Successfully loaded {len(st.session_state.original_df)} events")
            else:
                st.error("❌ No data could be fetched. Please check your configuration.")

# --- Main Dashboard Content ---
if st.session_state.data_fetched_successfully and not st.session_state.original_df.empty:
    
    filtered_df = st.session_state.original_df.copy()

    # Professional sidebar filters
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🎯 Filter Fetched Data")
        
        # Administrative filters with enhanced UI
        for admin_level, (icon, label) in enumerate([
            ("📍", "State/Province"),
            ("🏙️", "County/District"),
            ("🏘️", "Locality")
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

        # Map customization
        st.markdown("---")
        st.markdown("### 🎨 Basemap Customization")
        
        map_style_options = {
            "🌙 Dark": "mapbox://styles/mapbox/dark-v10",
            "☀️ Light": "mapbox://styles/mapbox/light-v10",
            "🛰️ Satellite": "mapbox://styles/mapbox/satellite-v9",
            "🗺️ Streets": "mapbox://styles/mapbox/streets-v11",
            "🏔️ Outdoors": "mapbox://styles/mapbox/outdoors-v11"
        }
        
        selected_style = st.selectbox(
            "Base Map Style",
            list(map_style_options.keys()),
            index=1 # Default to Light style
        )
        
        map_height = st.slider(
            "Map Height",
            min_value=400,
            max_value=800,
            value=600,
            step=50,
            help="Adjust the height of the map visualization"
        )

    # --- Main Content Area ---
    if not filtered_df.empty:
        # Enhanced metrics dashboard
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_events = len(filtered_df)
            st.markdown(f"""
            <div class="metric-container">
                <div>
                    <div class="metric-value">{total_events:,}</div>
                    <div class="metric-label">📊 Total Events</div>
                </div>
                <div style="font-size: 2rem;">🎯</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_fatalities = int(filtered_df["fatalities"].sum()) if "fatalities" in filtered_df.columns else 0
            st.markdown(f"""
            <div class="metric-container">
                <div>
                    <div class="metric-value">{total_fatalities:,}</div>
                    <div class="metric-label">💔 Total Fatalities</div>
                </div>
                <div style="font-size: 2rem;">⚠️</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            unique_locations = filtered_df["admin1"].nunique() if "admin1" in filtered_df.columns else 0
            st.markdown(f"""
            <div class="metric-container">
                <div>
                    <div class="metric-value">{unique_locations}</div>
                    <div class="metric-label">📍 Affected Regions</div>
                </div>
                <div style="font-size: 2rem;">🌍</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            date_range = (filtered_df["event_date"].max() - filtered_df["event_date"].min()).days if "event_date" in filtered_df.columns else 0
            st.markdown(f"""
            <div class="metric-container">
                <div>
                    <div class="metric-value">{date_range}</div>
                    <div class="metric-label">📅 Days Covered</div>
                </div>
                <div style="font-size: 2rem;">⏱️</div>
            </div>
            """, unsafe_allow_html=True)

        # Enhanced visualization layout
        st.markdown("---")
        
        # Map and analytics section
        map_col, legend_col = st.columns([5, 1])
        
        with map_col:
            st.markdown("### 🗺️ Geospatial Distribution")
            
            # --- Map Type Selection Buttons ---
            st.markdown("#### Select Map Type:")
            map_buttons_cols = st.columns(4) # Increased to 4 columns for the new option
            with map_buttons_cols[0]:
                if st.button("🎨 Categories", key="categories_button", use_container_width=True):
                    st.session_state.map_selection = "Categorized Map (by Event Type)"
                    st.session_state.is_playing = False # Stop animation if map type changes
            with map_buttons_cols[1]:
                if st.button("🔥 Heatmap", key="heatmap_button", use_container_width=True):
                    st.session_state.map_selection = "Heatmap (Event Density)"
                    st.session_state.is_playing = False # Stop animation if map type changes
            with map_buttons_cols[2]:
                if st.button("🎯 Impact", key="impact_button", use_container_width=True):
                    st.session_state.map_selection = "Scatterplot (by Fatalities)"
                    st.session_state.is_playing = False # Stop animation if map type changes
            with map_buttons_cols[3]: # New button for Temporal Map
                if st.button("⏳ Temporal", key="temporal_button", use_container_width=True):
                    st.session_state.map_selection = "Temporal Map (Time Slider)"
                    # Don't change is_playing state here, let the play/stop buttons control it

            st.markdown("---") # Separator after map type buttons

            display_df = filtered_df.copy()
            
            # --- Temporal Slider and Play/Stop Button Logic ---
            if st.session_state.map_selection == "Temporal Map (Time Slider)":
                if 'event_date' in display_df.columns and not display_df.empty:
                    unique_dates = sorted(display_df['event_date'].dt.date.unique())
                    min_date_slider = unique_dates[0]
                    max_date_slider = unique_dates[-1]

                    if len(unique_dates) <= 1:
                        st.info(f"Only one or no dates ({min_date_slider if unique_dates else 'N/A'}) available for the current filters. Animation not available.")
                        selected_date = min_date_slider if unique_dates else None # Set selected_date if only one
                        if selected_date:
                            display_df = display_df[display_df['event_date'].dt.date == selected_date]
                        else:
                            display_df = pd.DataFrame() # No dates, so empty df
                    else:
                        # Ensure date_index is within bounds
                        if st.session_state.date_index >= len(unique_dates):
                            st.session_state.date_index = 0 # Loop back
                        
                        # Set selected_temporal_date based on current date_index if playing
                        if st.session_state.is_playing:
                             st.session_state.selected_temporal_date = unique_dates[st.session_state.date_index]
                        # Else, if selected_temporal_date is outside the current range, set it to min_date
                        elif st.session_state.selected_temporal_date is None or \
                             st.session_state.selected_temporal_date < min_date_slider or \
                             st.session_state.selected_temporal_date > max_date_slider:
                            st.session_state.selected_temporal_date = min_date_slider


                        # Slider for manual control
                        selected_date = st.slider(
                            "Select Date for Temporal Map",
                            min_value=min_date_slider,
                            max_value=max_date_slider,
                            value=st.session_state.selected_temporal_date,
                            format="YYYY-MM-DD",
                            help="Drag to view events on a specific date",
                            key="temporal_date_slider"
                        )
                        
                        # Update date_index if slider is moved manually
                        st.session_state.date_index = unique_dates.index(selected_date)

                        # Play/Stop buttons
                        play_col, stop_col = st.columns(2)
                        with play_col:
                            if st.button("▶️ Play Animation", use_container_width=True, key="play_button"):
                                st.session_state.is_playing = True
                        with stop_col:
                            if st.button("⏸️ Stop Animation", use_container_width=True, key="stop_button"):
                                st.session_state.is_playing = False
                        
                        # Filter data based on selected date (manual or animated)
                        display_df = display_df[display_df['event_date'].dt.date == selected_date]
                        st.write(f"Displaying events for: **{selected_date.strftime('%Y-%m-%d')}**")
                        
                        if display_df.empty:
                            st.warning(f"No events found for {selected_date.strftime('%Y-%m-%d')}.")
                        
                        # Animation logic for auto-play
                        if st.session_state.is_playing:
                            time.sleep(0.5) # Control animation speed
                            st.session_state.date_index = (st.session_state.date_index + 1) % len(unique_dates)
                            st.rerun() # Force rerun to update slider and map

                else:
                    st.warning("No date data available to create a temporal map. Please check your filters or data source.")
                    display_df = pd.DataFrame() # Ensure display_df is empty to prevent errors

            display_df['event_date_str'] = display_df['event_date'].dt.strftime('%Y-%m-%d')
            map_type = st.session_state.map_selection
            
            # Ensure a valid center for the map, handle empty display_df
            if not display_df.empty:
                view_state = pdk.ViewState(
                    latitude=display_df["latitude"].mean(),
                    longitude=display_df["longitude"].mean(),
                    zoom=7,
                    pitch=0,
                )
            elif not filtered_df.empty: # Fallback to filtered_df if display_df is empty due to temporal filter
                view_state = pdk.ViewState(
                    latitude=filtered_df["latitude"].mean(),
                    longitude=filtered_df["longitude"].mean(),
                    zoom=7,
                    pitch=0,
                )
            else:
                # Default view state if no data is filtered at all
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
            
            # Enhanced map rendering with professional styling
            if map_type == "Categorized Map (by Event Type)":
                if "event_type" in display_df.columns and not display_df["event_type"].empty:
                    # Use original_df for consistent colors across all temporal frames
                    unique_event_types = st.session_state.original_df["event_type"].dropna().unique() 
                    colors = plt.cm.get_cmap('Set3', len(unique_event_types))
                    event_type_colors = {
                        event_type: [int(c * 255) for c in colors(i)[:3]] + [180]
                        for i, event_type in enumerate(unique_event_types)
                    }
                    
                    display_df['color'] = display_df['event_type'].map(event_type_colors)
                    # For temporal map, legend should still reflect all possible event types from the original data for consistency
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
                else:
                    st.info("ℹ️ No events found for the selected view or filters.")

            elif map_type == "Heatmap (Event Density)" or map_type == "Temporal Map (Time Slider)":
                # Both general heatmap and temporal heatmap will use HeatmapLayer
                layers.append(
                    pdk.Layer(
                        "HeatmapLayer",
                        data=display_df,
                        get_position='[longitude, latitude]',
                        opacity=0.7,
                        threshold=0.04,
                        aggregation='SUM', # Sum weights (defaults to 1 per point)
                        get_weight=1 # Each event contributes equally to heatmap density
                    )
                )
                legend_data = {'type': 'heatmap'} # Consistent heatmap legend

            elif map_type == "Scatterplot (by Fatalities)":
                if "fatalities" in display_df.columns and display_df["fatalities"].max() > 0:
                    max_fatalities = display_df["fatalities"].max()
                    min_fatalities = display_df["fatalities"].min()
                    # Ensure minimum radius for visibility even with 0 fatalities
                    display_df['radius'] = (display_df['fatalities'] / max_fatalities) * 5000 + 500
                    legend_data = {
                        'type': 'fatalities',
                        'min_fatalities': int(min_fatalities),
                        'max_fatalities': int(max_fatalities)
                    }
                else:
                    display_df['radius'] = 600 # Default radius if no fatalities or all are zero
                    legend_data = {'type': 'fatalities', 'min_fatalities': 0, 'max_fatalities': 0}

                layers.append(
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=display_df,
                        get_position='[longitude, latitude]',
                        get_color='[255, 100, 100, 180]', # Consistent color for fatality map, opaque
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
                        # Define representative sizes for the legend based on fatality range
                        sizes = []
                        if legend_data['min_fatalities'] == 0 and legend_data['max_fatalities'] == 0:
                             sizes.append((0, '12px'))
                        elif legend_data['max_fatalities'] > 0:
                            sizes.append((legend_data['min_fatalities'], '10px'))
                            if legend_data['max_fatalities'] > 1: # Add a mid-range if applicable
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
                # Event type distribution with professional styling
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
                    else:
                        st.info("ℹ️ No event types to display.")
                else:
                    st.info("ℹ️ 'event_type' column not found in data.")

            with col_chart2:
                # Timeline analysis
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
                            height=300 # Adjusted height to align with pie chart
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("ℹ️ No event dates to display a timeline.")
                else:
                    st.info("ℹ️ 'event_date' column not found in data.")

            st.markdown("---")
            st.markdown("### 📊 Create Custom Chart")
            # Multiselect admin1 filter for the chart
            if "admin1" in filtered_df.columns:
                admin1_values = filtered_df["admin1"].dropna().unique().tolist()
                selected_admin1s = st.multiselect("🗂️ Select Regions (admin1) for Bar Chart", sorted(admin1_values))

                admin1_filtered_df = filtered_df[filtered_df["admin1"].isin(selected_admin1s)]

                if not admin1_filtered_df.empty and "admin2" in admin1_filtered_df.columns and "event_type" in admin1_filtered_df.columns:
                    # Group and count events (subtotals)
                    chart_data = admin1_filtered_df.groupby(["admin2", "event_type"]).size().reset_index(name="count")

                    # Compute total per admin2
                    total_counts = chart_data.groupby("admin2")["count"].sum().reset_index(name="total")
                    chart_data = chart_data.merge(total_counts, on="admin2")

                    # Create base figure
                    fig = px.bar(
                        chart_data,
                        y="admin2",
                        x="count",
                        color="event_type",
                        orientation="h",
                        labels={"count": "Number of Events", "admin2": "District"},
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        title="📊 Events by admin2 and Event Type"
                    )

                    # Add subtotal labels (per segment)
                    for trace in fig.data:
                        trace.text = [str(int(c)) for c in trace.x]
                        trace.textposition = "inside"

                    # Add total labels at the end of each admin2 bar
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
                else:
                    st.info("ℹ️ No data available for the selected region(s) to generate the bar chart.")

        # Enhanced data table
        st.markdown("---")
        with st.expander("📊 Detailed Data Explorer", expanded=False):
            # Add search and filter functionality
            search_term = st.text_input("🔍 Search in data:", placeholder="Enter search term...")
            
            if search_term:
                # Convert all columns to string before searching to avoid errors with mixed types
                mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                display_data = filtered_df[mask]
            else:
                display_data = filtered_df
            
            st.dataframe(
                display_data,
                use_container_width=True,
                height=400
            )
            
            # Export functionality
            csv = display_data.to_csv(index=False).encode('utf-8') # Ensure UTF-8 encoding
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"events_data_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    else:
        st.warning("🔍 No events found matching the selected filters. Try adjusting your selections.")

else:
    # Professional welcome screen
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                  border-radius: 15px; margin: 2rem 0;">
        <h2 style="color: #2a5298; margin-bottom: 1rem;">🚀 Welcome to Events Intelligence</h2>
        <p style="font-size: 1.1rem; color: #666; margin-bottom: 2rem;">
            Configure your data sources in the control panel and click "Fetch Data" to begin your analysis.
        </p>
        <div style="background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h4 style="color: #2a5298; margin-bottom: 1rem;">✨ Key Features</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; text-align: left;">
                <div>🗺️ Interactive geospatial mapping</div>
                <div>📊 Real-time analytics dashboard</div>
                <div>🎯 Advanced filtering system</div>
                <div>📈 Temporal trend analysis</div>
                <div>🔍 Smart data exploration</div>
                <div>📥 Export capabilities</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)