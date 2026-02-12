import streamlit as st
import requests
import json
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import time
import re

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Security Data Explorer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS  – Dark intelligence-grade aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

:root {
    --bg-primary:   #0a0e1a;
    --bg-card:      #111827;
    --bg-hover:     #1a2236;
    --accent:       #00d4ff;
    --accent2:      #ff6b35;
    --accent3:      #39ff14;
    --text-primary: #e2e8f0;
    --text-muted:   #64748b;
    --border:       rgba(0,212,255,0.15);
    --danger:       #ef4444;
    --warning:      #f59e0b;
}

html, body, .stApp {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem !important; max-width: 1600px; }

/* ── HEADER ── */
.main-header {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2a4a 50%, #0d1b2a 100%);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    padding: 1.8rem 2.5rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg, transparent, transparent 30px,
        rgba(0,212,255,0.02) 30px, rgba(0,212,255,0.02) 31px
    );
}
.main-header h1 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.8rem; font-weight: 600;
    color: var(--accent) !important;
    margin: 0; letter-spacing: 0.05em;
    text-shadow: 0 0 20px rgba(0,212,255,0.4);
}
.main-header p {
    color: var(--text-muted); font-size: 0.85rem;
    margin: 0.3rem 0 0; letter-spacing: 0.08em; text-transform: uppercase;
}

/* ── METRIC CARDS ── */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-top: 2px solid var(--accent);
    border-radius: 6px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    transition: border-color 0.2s, background 0.2s;
}
.metric-card:hover { background: var(--bg-hover); border-top-color: var(--accent2); }
.metric-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem; font-weight: 600;
    color: var(--accent); line-height: 1.1;
}
.metric-label {
    font-size: 0.75rem; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.3rem;
}
.metric-delta { font-size: 0.8rem; color: var(--accent3); margin-top: 0.2rem; }

/* ── SECTION HEADERS ── */
.section-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.15em;
    color: var(--accent); padding: 0.4rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}

/* ── BUTTONS ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-muted) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-radius: 4px !important;
    transition: all 0.2s !important;
    padding: 0.5rem 1rem !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: rgba(0,212,255,0.05) !important;
    box-shadow: 0 0 12px rgba(0,212,255,0.15) !important;
}
.stButton > button[kind="primary"] {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: rgba(0,212,255,0.08) !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background-color: #080d18 !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label { color: var(--text-muted) !important; }

/* ── INPUTS ── */
.stTextInput input, .stDateInput input,
.stSelectbox > div > div, .stMultiSelect > div > div {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 4px !important;
}
.stSlider > div { color: var(--text-muted) !important; }
.stSlider .stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] { color: var(--text-muted) !important; }

/* ── BRIEFING BOX ── */
.briefing-box {
    background: #0a1628;
    border: 1px solid rgba(0,212,255,0.2);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 1.5rem 2rem;
    font-family: 'IBM Plex Sans', sans-serif;
    line-height: 1.8;
    color: var(--text-primary);
    white-space: pre-wrap;
}
.briefing-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem; letter-spacing: 0.2em;
    text-transform: uppercase; color: var(--accent);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.6rem; margin-bottom: 1rem;
}
.status-ok   { color: var(--accent3); }
.status-warn { color: var(--warning); }
.status-crit { color: var(--danger); }

/* ── DATAFRAME ── */
.stDataFrame { border: 1px solid var(--border) !important; border-radius: 6px; }
[data-testid="stDataFrameResizable"] { background: var(--bg-card) !important; }

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
ACLED_CONFIG = {
    "token_url": "https://acleddata.com/oauth/token",
    "api_read_url": "https://acleddata.com/api/acled/read?_format=json",
}

# Open-source basemap tile providers (all free, no API key needed)
BASEMAPS = {
    "🌑 Dark Matter (Carto)":        "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    "🗺️ OpenStreetMap Positron":     "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "🏔️ OpenStreetMap Voyager":      "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
    "🌲 Stadia Outdoors":            "https://tiles.stadiamaps.com/styles/outdoors.json",
    "🌆 Stadia Alidade Smooth Dark": "https://tiles.stadiamaps.com/styles/alidade_smooth_dark.json",
    "🛰️ Satellite (no-key fallback)": "mapbox://styles/mapbox/satellite-v9",
}

# Event type color palette
EVENT_COLORS = {
    "Battles":                    [220, 38,  38,  200],
    "Violence against civilians": [249, 115, 22,  200],
    "Explosions/Remote violence": [234, 179, 8,   200],
    "Protests":                   [59,  130, 246, 200],
    "Riots":                      [139, 92,  246, 200],
    "Strategic developments":     [16,  185, 129, 200],
}
DEFAULT_COLOR = [100, 116, 139, 160]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for k, v in {
    "original_df": pd.DataFrame(),
    "data_fetched": False,
    "map_mode": "Categories",
    "selected_temporal_date": None,
    "is_playing": False,
    "briefing_text": "",
    "briefing_loading": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# CORE API FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400)
def get_access_token(username, password, token_url):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"username": username, "password": password,
            "grant_type": "password", "client_id": "acled"}
    try:
        r = requests.post(token_url, headers=headers, data=data, timeout=15)
        r.raise_for_status()
        return r.json()["access_token"]
    except Exception as e:
        st.error(f"Auth error: {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_acled_data(token, countries, start_date, end_date):
    headers = {"Authorization": f"Bearer {token}"}
    dfs = []
    for country in countries:
        params = {
            "country": country,
            "event_date": f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
            "event_date_where": "BETWEEN",
            "limit": "5000",
        }
        try:
            r = requests.get(ACLED_CONFIG["api_read_url"],
                             params=params, headers=headers, timeout=30)
            d = r.json()
            if d.get("status") == 200 and d.get("data"):
                dfs.append(pd.DataFrame(d["data"]))
        except Exception as e:
            st.warning(f"Error fetching {country}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# BRIEFING GENERATOR  (free LLM via Ollama HTTP or HuggingFace Inference API)
# ─────────────────────────────────────────────────────────────────────────────
def call_ollama(prompt: str, model: str = "mistral", host: str = "http://localhost:11434") -> str:
    """Call a locally-running Ollama instance."""
    try:
        r = requests.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        if r.status_code == 200:
            return r.json().get("response", "No response from Ollama.")
        return f"Ollama error {r.status_code}: {r.text[:300]}"
    except requests.exceptions.ConnectionError:
        return None  # signal to try fallback


def call_huggingface(prompt: str, hf_token: str = "") -> str:
    """Call HuggingFace Inference API (free tier – no key needed for public models)."""
    model_id = "HuggingFaceH4/zephyr-7b-beta"
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Content-Type": "application/json"}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.4,
            "return_full_text": False,
        },
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=90)
        if r.status_code == 200:
            result = r.json()
            if isinstance(result, list) and result:
                return result[0].get("generated_text", "Empty response.")
            return str(result)
        return f"HuggingFace API error {r.status_code}: {r.text[:400]}"
    except Exception as e:
        return f"HuggingFace request failed: {e}"


def build_briefing_prompt(df: pd.DataFrame, context: str = "") -> str:
    total_events   = len(df)
    total_fatalities = int(df["fatalities"].sum())
    date_range     = f"{df['event_date'].min().strftime('%d %b %Y')} – {df['event_date'].max().strftime('%d %b %Y')}"
    regions        = df["admin1"].dropna().value_counts().head(5).to_dict()
    event_types    = df["event_type"].dropna().value_counts().to_dict()
    actors         = df["actor1"].dropna().value_counts().head(8).to_dict()
    deadliest      = df.nlargest(3, "fatalities")[["event_date","event_type","location","fatalities","notes"]].to_dict("records")

    # Collect a sample of incident notes (up to 20, non-empty)
    notes_sample = (
        df["notes"]
        .dropna()
        .loc[df["notes"].str.strip() != ""]
        .sample(min(20, len(df)), random_state=42)
        .tolist()
    )
    notes_block = "\n".join(f"- {n[:400]}" for n in notes_sample)

    deadliest_block = "\n".join(
        f"  [{r['event_date'].strftime('%d %b %Y') if hasattr(r['event_date'],'strftime') else r['event_date']}] "
        f"{r['event_type']} in {r['location']} – {int(r['fatalities'])} fatalities. {str(r.get('notes',''))[:200]}"
        for r in deadliest
    )

    prompt = f"""You are a professional security analyst. Write a structured intelligence briefing in plain text.
Use the following verified data. Be concise, analytical, and objective.
Do NOT use markdown formatting symbols like ** or ##. Use plain section titles in ALL CAPS.

--- DATA SUMMARY ---
Period        : {date_range}
Total Events  : {total_events}
Total Fatalities: {total_fatalities}
Top Regions   : {json.dumps(regions)}
Event Types   : {json.dumps(event_types)}
Key Actors    : {json.dumps(actors)}

DEADLIEST INCIDENTS:
{deadliest_block}

SAMPLE INCIDENT NOTES:
{notes_block}

{"ANALYST FOCUS: " + context if context else ""}

--- REQUIRED STRUCTURE ---
SITUATION OVERVIEW
[2-3 sentences on overall security situation]

KEY FINDINGS
[3-5 bullet points with the most significant patterns and numbers]

THREAT ACTORS
[Brief paragraph on dominant actors and their activity]

GEOGRAPHIC HOTSPOTS
[Identify 2-3 most affected areas with specific details]

TREND ANALYSIS
[Describe escalation, de-escalation, or shifts in tactics based on the notes]

RISK ASSESSMENT
[Overall risk level: LOW / MEDIUM / HIGH / CRITICAL with justification]

RECOMMENDATIONS
[2-3 actionable recommendations for operational planning]

--- END BRIEFING ---
"""
    return prompt


def generate_briefing(df: pd.DataFrame, context: str, llm_source: str,
                      ollama_host: str, ollama_model: str, hf_token: str) -> str:
    prompt = build_briefing_prompt(df, context)

    if llm_source == "Ollama (Local)":
        result = call_ollama(prompt, model=ollama_model, host=ollama_host)
        if result is None:
            return "❌ Could not connect to Ollama. Make sure it is running at the configured host."
        return result

    elif llm_source == "HuggingFace Inference API (Free)":
        return call_huggingface(prompt, hf_token)

    return "No LLM source selected."


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🛡️ SECURITY DATA EXPLORER</h1>
  <p>ACLED — Advanced Conflict Intelligence Platform</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR  — Control Panel
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-title">⚙ CONTROL PANEL</div>', unsafe_allow_html=True)

    # Credentials
    try:
        email    = st.secrets["acled"]["email"]
        password = st.secrets["acled"]["password"]
        st.success("✅ ACLED credentials loaded")
    except Exception:
        st.error("❌ Missing ACLED credentials in Secrets")
        st.info("Add [acled] email / password to .streamlit/secrets.toml")
        st.stop()

    # Countries
    countries_input = st.text_input("Countries (comma-separated)", "Palestine, Israel")
    countries_list  = [c.strip() for c in countries_input.split(",") if c.strip()]

    # Date range
    col1, col2 = st.columns(2)
    start_date = col1.date_input("From", date.today() - timedelta(days=30))
    end_date   = col2.date_input("To",   date.today())

    fetch_button = st.button("🚀 Fetch Data", type="primary", use_container_width=True)

    st.markdown("---")
    # ── MAP SETTINGS ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🗺 MAP SETTINGS</div>', unsafe_allow_html=True)

    basemap_choice = st.selectbox(
        "Basemap",
        list(BASEMAPS.keys()),
        index=0,
        help="Open-source tile providers – no API key required for Carto/Stadia"
    )
    selected_map_style = BASEMAPS[basemap_choice]

    point_radius = st.slider("Point Radius (m)", 500, 8000, 2000, 250)
    point_opacity = st.slider("Point Opacity", 0.1, 1.0, 0.75, 0.05)
    zoom_level = st.slider("Default Zoom", 4, 14, 7)

    st.markdown("---")
    # ── LLM SETTINGS ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🤖 BRIEFING LLM</div>', unsafe_allow_html=True)

    llm_source = st.selectbox(
        "LLM Backend",
        ["Ollama (Local)", "HuggingFace Inference API (Free)"],
        help="Ollama: run locally for free. HuggingFace: free API (rate-limited)."
    )

    if llm_source == "Ollama (Local)":
        ollama_host  = st.text_input("Ollama Host", "http://localhost:11434")
        ollama_model = st.text_input("Model", "mistral",
                                     help="e.g. mistral, llama3, phi3, gemma2")
        hf_token = ""
    else:
        hf_token     = st.text_input("HF Token (optional)", type="password",
                                     help="Increases rate limits. Leave blank for anonymous use.")
        ollama_host  = ""
        ollama_model = ""

# ─────────────────────────────────────────────────────────────────────────────
# FETCH DATA
# ─────────────────────────────────────────────────────────────────────────────
if fetch_button:
    token = get_access_token(email, password, ACLED_CONFIG["token_url"])
    if token:
        with st.spinner("Fetching conflict data…"):
            raw_df = fetch_acled_data(token, tuple(countries_list), start_date, end_date)
            if not raw_df.empty:
                raw_df["event_date"]  = pd.to_datetime(raw_df["event_date"])
                raw_df["latitude"]    = pd.to_numeric(raw_df["latitude"],  errors="coerce")
                raw_df["longitude"]   = pd.to_numeric(raw_df["longitude"], errors="coerce")
                raw_df["fatalities"]  = pd.to_numeric(raw_df["fatalities"],errors="coerce").fillna(0)
                raw_df = raw_df.dropna(subset=["latitude", "longitude"])

                st.session_state.original_df  = raw_df
                st.session_state.data_fetched = True
                st.session_state.selected_temporal_date = raw_df["event_date"].min().date()
                st.session_state.briefing_text = ""
                st.rerun()
            else:
                st.warning("No data returned for the selected parameters.")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.data_fetched:
    full_df = st.session_state.original_df.copy()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — FILTERS
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("🔍  ADVANCED FILTERS", expanded=True):
        fc1, fc2, fc3, fc4 = st.columns(4)

        # Event type
        all_event_types = sorted(full_df["event_type"].dropna().unique().tolist())
        sel_event_types = fc1.multiselect(
            "Event Type", all_event_types, default=all_event_types, key="f_et"
        )

        # Sub-event type
        all_sub_events = sorted(full_df["sub_event_type"].dropna().unique().tolist())
        sel_sub_events = fc2.multiselect(
            "Sub-Event Type", all_sub_events, default=all_sub_events, key="f_se"
        )

        # Country
        all_countries = sorted(full_df["country"].dropna().unique().tolist())
        sel_countries = fc3.multiselect(
            "Country", all_countries, default=all_countries, key="f_co"
        )

        # Admin 1 (Region)
        all_admin1 = sorted(full_df["admin1"].dropna().unique().tolist())
        sel_admin1 = fc4.multiselect(
            "Region (Admin1)", all_admin1, default=all_admin1, key="f_a1"
        )

        fc5, fc6, fc7 = st.columns(3)

        # Admin 2 (District) — cascaded
        available_admin2 = sorted(
            full_df[full_df["admin1"].isin(sel_admin1)]["admin2"].dropna().unique().tolist()
        )
        sel_admin2 = fc5.multiselect(
            "District (Admin2)", available_admin2, default=available_admin2, key="f_a2"
        )

        # Actor
        all_actors = sorted(full_df["actor1"].dropna().unique().tolist())
        sel_actors = fc6.multiselect(
            "Primary Actor", all_actors, default=all_actors, key="f_ac"
        )

        # Fatalities range
        max_fat = int(full_df["fatalities"].max()) or 1
        fat_range = fc7.slider(
            "Fatalities Range", 0, max_fat, (0, max_fat), key="f_fr"
        )

    # Apply filters
    filtered_df = full_df[
        full_df["event_type"].isin(sel_event_types) &
        full_df["sub_event_type"].isin(sel_sub_events) &
        full_df["country"].isin(sel_countries) &
        full_df["admin1"].isin(sel_admin1) &
        full_df["actor1"].isin(sel_actors) &
        full_df["fatalities"].between(fat_range[0], fat_range[1])
    ]
    if sel_admin2:
        filtered_df = filtered_df[filtered_df["admin2"].isin(sel_admin2)]

    st.caption(f"Showing **{len(filtered_df):,}** events after filters (from {len(full_df):,} total)")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — KEY METRICS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">📊 KEY METRICS</div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)

    days_span = max((filtered_df["event_date"].max() - filtered_df["event_date"].min()).days, 1)

    m1.markdown(f'<div class="metric-card"><div class="metric-value">{len(filtered_df):,}</div><div class="metric-label">Total Events</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-value">{int(filtered_df["fatalities"].sum()):,}</div><div class="metric-label">Fatalities</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-value">{filtered_df["admin1"].nunique()}</div><div class="metric-label">Regions Affected</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-value">{days_span}</div><div class="metric-label">Day Span</div></div>', unsafe_allow_html=True)
    avg_daily = len(filtered_df) / days_span if days_span else 0
    m5.markdown(f'<div class="metric-card"><div class="metric-value">{avg_daily:.1f}</div><div class="metric-label">Avg Events/Day</div></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — MAP
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">🗺 GEOSPATIAL DISTRIBUTION</div>', unsafe_allow_html=True)

    mode_cols = st.columns(5)
    for idx, (label, key) in enumerate([
        ("🎨 Categories", "Categories"),
        ("🔥 Heatmap",    "Heatmap"),
        ("🎯 Impact",     "Impact"),
        ("⏳ Temporal",   "Temporal"),
        ("📍 Cluster",    "Cluster"),
    ]):
        if mode_cols[idx].button(label, use_container_width=True):
            st.session_state.map_mode = key

    display_df = filtered_df.copy()

    # Temporal controls
    if st.session_state.map_mode == "Temporal":
        unique_dates = sorted(filtered_df["event_date"].dt.date.unique())
        if unique_dates:
            if st.session_state.selected_temporal_date not in unique_dates:
                st.session_state.selected_temporal_date = unique_dates[0]
            selected_date = st.slider(
                "Timeline",
                min_value=unique_dates[0], max_value=unique_dates[-1],
                value=st.session_state.selected_temporal_date,
            )
            display_df = filtered_df[filtered_df["event_date"].dt.date == selected_date].copy()
            pc1, pc2, pc3 = st.columns([1, 1, 4])
            if pc1.button("▶️ Play"):  st.session_state.is_playing = True
            if pc2.button("⏸️ Stop"):  st.session_state.is_playing = False
            st.caption(f"{selected_date} — {len(display_df)} events")
            if st.session_state.is_playing and unique_dates:
                time.sleep(0.4)
                idx_now = unique_dates.index(selected_date)
                st.session_state.selected_temporal_date = unique_dates[(idx_now + 1) % len(unique_dates)]
                st.rerun()

    # Build layers
    lat_c = display_df["latitude"].mean()  if not display_df.empty else 32.0
    lon_c = display_df["longitude"].mean() if not display_df.empty else 35.0

    view_state = pdk.ViewState(latitude=lat_c, longitude=lon_c, zoom=zoom_level, pitch=0)

    tooltip = {"html": "<b>{event_type}</b><br/>{location}<br/>Actor: {actor1}<br/>Fatalities: {fatalities}<br/><i>{notes}</i>",
               "style": {"background": "#0a0e1a", "color": "#e2e8f0",
                         "font-family": "'IBM Plex Mono', monospace",
                         "font-size": "12px", "padding": "8px", "border": "1px solid #00d4ff"}}

    mode = st.session_state.map_mode

    if mode == "Heatmap":
        layers = [pdk.Layer(
            "HeatmapLayer", display_df,
            get_position="[longitude, latitude]",
            get_weight="fatalities",
            opacity=point_opacity,
            threshold=0.05,
            radiusPixels=40,
        )]

    elif mode == "Impact":
        df_map = display_df.copy()
        max_f = df_map["fatalities"].max() or 1
        df_map["radius"] = (df_map["fatalities"] / max_f) * 15000 + 800
        df_map["color"]  = df_map["fatalities"].apply(
            lambda f: [255, int(max(0, 100 - f * 3)), 50, 200]
        )
        layers = [pdk.Layer(
            "ScatterplotLayer", df_map,
            get_position="[longitude, latitude]",
            get_radius="radius",
            get_fill_color="color",
            pickable=True,
        )]

    elif mode == "Cluster":
        layers = [pdk.Layer(
            "IconClusterLayer",
            display_df,
            get_position="[longitude, latitude]",
            pickable=True,
            size_scale=40,
        )]

    else:  # Categories (default) + Temporal
        def get_color(et):
            return EVENT_COLORS.get(et, DEFAULT_COLOR)
        df_map = display_df.copy()
        df_map["color"] = df_map["event_type"].apply(get_color)
        layers = [pdk.Layer(
            "ScatterplotLayer", df_map,
            get_position="[longitude, latitude]",
            get_radius=point_radius,
            get_fill_color="color",
            opacity=point_opacity,
            pickable=True,
            auto_highlight=True,
        )]

    map_col, leg_col = st.columns([5, 1])
    with map_col:
        st.pydeck_chart(pdk.Deck(
            map_style=selected_map_style,
            layers=layers,
            initial_view_state=view_state,
            tooltip=tooltip,
        ))

    with leg_col:
        if mode in ("Categories", "Temporal"):
            st.markdown("**Legend**")
            for etype, rgba in EVENT_COLORS.items():
                hex_col = "#{:02x}{:02x}{:02x}".format(*rgba[:3])
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
                    f'<div style="width:12px;height:12px;border-radius:50%;background:{hex_col};flex-shrink:0;"></div>'
                    f'<span style="font-size:0.72rem;color:#94a3b8;">{etype}</span></div>',
                    unsafe_allow_html=True,
                )
        elif mode == "Heatmap":
            st.markdown("**Heatmap**")
            st.markdown('<div style="font-size:0.72rem;color:#94a3b8;">Intensity = fatality weight</div>', unsafe_allow_html=True)
        elif mode == "Impact":
            st.markdown("**Impact**")
            st.markdown('<div style="font-size:0.72rem;color:#94a3b8;">Radius & color = fatality count</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">📈 ANALYTICS DASHBOARD</div>', unsafe_allow_html=True)

    chart_theme = "plotly_dark"
    ac1, ac2 = st.columns(2)

    with ac1:
        fig_pie = px.pie(
            filtered_df, names="event_type",
            title="Event Type Distribution",
            color_discrete_sequence=["#00d4ff","#ff6b35","#39ff14","#a855f7","#f59e0b","#ef4444"],
            hole=0.45,
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", title_font_color="#00d4ff",
            legend=dict(font=dict(color="#94a3b8", size=10)),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with ac2:
        timeline = (
            filtered_df.groupby(filtered_df["event_date"].dt.date)
            .agg(events=("event_id_cnty", "count"), fatalities=("fatalities", "sum"))
            .reset_index()
        )
        fig_tl = go.Figure()
        fig_tl.add_trace(go.Bar(
            x=timeline["event_date"], y=timeline["events"],
            name="Events", marker_color="#00d4ff", opacity=0.7
        ))
        fig_tl.add_trace(go.Scatter(
            x=timeline["event_date"], y=timeline["fatalities"],
            name="Fatalities", mode="lines+markers",
            line=dict(color="#ff6b35", width=2),
            yaxis="y2"
        ))
        fig_tl.update_layout(
            title="Events & Fatalities Timeline",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", title_font_color="#00d4ff",
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(255,255,255,0.0)"),
            legend=dict(font=dict(color="#94a3b8")),
            bargap=0.1,
        )
        st.plotly_chart(fig_tl, use_container_width=True)

    ac3, ac4 = st.columns(2)
    with ac3:
        top_regions = (
            filtered_df.groupby("admin1")
            .agg(events=("event_id_cnty","count"), fatalities=("fatalities","sum"))
            .sort_values("fatalities", ascending=True).tail(12).reset_index()
        )
        fig_bar = px.bar(
            top_regions, x="fatalities", y="admin1", orientation="h",
            title="Top Regions by Fatalities",
            color="events",
            color_continuous_scale=["#1e3a5f","#00d4ff"],
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", title_font_color="#00d4ff",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"), yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            coloraxis_colorbar=dict(tickfont=dict(color="#94a3b8")),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with ac4:
        top_actors = (
            filtered_df.groupby("actor1")
            .agg(events=("event_id_cnty","count"), fatalities=("fatalities","sum"))
            .sort_values("events", ascending=False).head(10).reset_index()
        )
        fig_act = px.bar(
            top_actors, x="actor1", y="events",
            title="Top 10 Actors by Event Count",
            color="fatalities",
            color_continuous_scale=["#1e3a5f","#ff6b35"],
        )
        fig_act.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", title_font_color="#00d4ff",
            xaxis=dict(tickangle=-35, gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            coloraxis_colorbar=dict(tickfont=dict(color="#94a3b8")),
        )
        st.plotly_chart(fig_act, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — AUTO BRIEFING GENERATOR
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">📝 AUTO BRIEFING GENERATOR</div>', unsafe_allow_html=True)

    bg_col1, bg_col2 = st.columns([3, 1])
    with bg_col1:
        analyst_context = st.text_area(
            "Analyst Focus / Custom Instructions (optional)",
            placeholder="e.g. Focus on civilian impact in northern districts. Highlight any shift in IED usage patterns.",
            height=80,
        )
    with bg_col2:
        max_events_for_llm = st.number_input(
            "Max Events for LLM", min_value=10, max_value=500, value=150, step=10,
            help="Larger samples = richer briefing but slower generation."
        )
        generate_btn = st.button("⚡ Generate Briefing", type="primary", use_container_width=True)

    if generate_btn:
        if filtered_df.empty:
            st.warning("No data to generate a briefing from. Adjust your filters.")
        else:
            sample_df = (
                filtered_df.sample(min(max_events_for_llm, len(filtered_df)), random_state=42)
                if len(filtered_df) > max_events_for_llm else filtered_df.copy()
            )
            with st.spinner(f"Generating intelligence briefing via {llm_source}…"):
                briefing = generate_briefing(
                    sample_df, analyst_context,
                    llm_source, ollama_host, ollama_model, hf_token
                )
            st.session_state.briefing_text = briefing
            st.rerun()

    if st.session_state.briefing_text:
        text = st.session_state.briefing_text
        # Color-code risk level keywords
        text_html = (
            text.replace("CRITICAL", '<span class="status-crit">CRITICAL</span>')
                .replace("HIGH",     '<span class="status-warn">HIGH</span>')
                .replace("MEDIUM",   '<span class="status-ok">MEDIUM</span>')
                .replace("LOW",      '<span class="status-ok">LOW</span>')
        )
        st.markdown(
            f'<div class="briefing-box">'
            f'<div class="briefing-header">// INTELLIGENCE BRIEFING — AUTO-GENERATED — {date.today().strftime("%d %b %Y").upper()}</div>'
            f'{text_html}</div>',
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns(2)
        col_a.download_button(
            "📥 Download Briefing (.txt)",
            data=st.session_state.briefing_text,
            file_name=f"briefing_{date.today()}.txt",
            mime="text/plain",
            use_container_width=True,
        )
        if col_b.button("🗑️ Clear Briefing", use_container_width=True):
            st.session_state.briefing_text = ""
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 6 — DATA EXPLORER
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("📊  DETAILED DATA EXPLORER"):
        cols_to_show = [
            c for c in [
                "event_date","event_type","sub_event_type","country",
                "admin1","admin2","location","actor1","actor2",
                "fatalities","notes","source"
            ] if c in filtered_df.columns
        ]
        st.dataframe(filtered_df[cols_to_show], use_container_width=True, height=400)
        st.download_button(
            "📥 Download Filtered CSV",
            filtered_df.to_csv(index=False),
            f"acled_filtered_{date.today()}.csv",
            "text/csv",
            use_container_width=True,
        )

else:
    # ── Welcome state ─────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem; color: #475569;">
        <div style="font-family:'IBM Plex Mono',monospace; font-size:3rem; color:#1e3a5f; margin-bottom:1rem;">◈</div>
        <div style="font-family:'IBM Plex Mono',monospace; font-size:0.85rem; letter-spacing:0.2em; text-transform:uppercase; color:#334155;">
            Configure parameters in the sidebar and click <b style="color:#00d4ff">🚀 Fetch Data</b> to begin.
        </div>
        <div style="margin-top:1.5rem; font-size:0.8rem; color:#334155; max-width:600px; margin-left:auto; margin-right:auto; line-height:1.8;">
            This platform integrates ACLED conflict data with open-source basemaps, 
            multi-level geographic filters, and an AI-powered briefing engine 
            using local (Ollama) or free cloud (HuggingFace) LLMs.
        </div>
    </div>
    """, unsafe_allow_html=True)
