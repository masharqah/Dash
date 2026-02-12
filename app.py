import streamlit as st
import requests
import json
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import time

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
# CSS — Modern Light "Command & Control" Theme
# Palette: off-white canvas · steel-blue authority · amber alerts · crimson danger
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --bg:             #f0f3f8;
    --surface:        #ffffff;
    --surface2:       #eaeff7;
    --navy:           #1b2a4a;
    --steel:          #2e5fa3;
    --steel-light:    #e8eef8;
    --steel-mid:      #b8cce8;
    --amber:          #d97706;
    --amber-light:    #fef3c7;
    --crimson:        #b91c1c;
    --crimson-light:  #fdecea;
    --green:          #15803d;
    --green-light:    #dcfce7;
    --text:           #1e2b3c;
    --text-sub:       #4e5f72;
    --text-muted:     #94a3b8;
    --border:         #d1dae8;
    --shadow:         0 1px 8px rgba(27,42,74,0.07), 0 2px 4px rgba(27,42,74,0.04);
    --shadow-md:      0 4px 20px rgba(27,42,74,0.10), 0 2px 8px rgba(27,42,74,0.06);
}

html, body, .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.2rem 2rem !important; max-width: 1600px; }

/* ─── HEADER ─── */
.main-header {
    background: linear-gradient(125deg, #1b2a4a 0%, #2c4580 55%, #2e5fa3 100%);
    border-radius: 12px;
    padding: 1.8rem 2.5rem;
    margin-bottom: 1.8rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: var(--shadow-md);
    position: relative;
    overflow: hidden;
}
.main-header::after {
    content: '';
    position: absolute; right: -30px; top: -40px;
    width: 220px; height: 220px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
    pointer-events: none;
}
.main-header::before {
    content: '';
    position: absolute; right: 80px; bottom: -50px;
    width: 150px; height: 150px;
    background: rgba(255,255,255,0.03);
    border-radius: 50%;
    pointer-events: none;
}
.header-left h1 {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 2.1rem; font-weight: 700;
    color: #ffffff !important;
    margin: 0; letter-spacing: 0.03em;
}
.header-left p {
    color: rgba(255,255,255,0.60);
    font-size: 0.78rem; margin: 0.3rem 0 0;
    letter-spacing: 0.12em; text-transform: uppercase;
}
.header-badge {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 6px;
    padding: 0.45rem 1rem;
    color: rgba(255,255,255,0.80);
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.78rem; letter-spacing: 0.14em;
    text-transform: uppercase; font-weight: 600;
}

/* ─── SECTION TITLES ─── */
.section-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.78rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.18em;
    color: var(--steel); padding: 0.3rem 0 0.6rem;
    border-bottom: 2px solid var(--steel-light);
    margin: 1.4rem 0 1rem;
    display: flex; align-items: center; gap: 0.5rem;
}

/* ─── METRIC CARDS ─── */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    text-align: center;
    box-shadow: var(--shadow);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    position: relative; overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, var(--steel), var(--navy));
    border-radius: 10px 10px 0 0;
}
.metric-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.metric-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.3rem; font-weight: 700;
    color: var(--navy); line-height: 1.1;
}
.metric-label {
    font-size: 0.7rem; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.12em;
    margin-top: 0.25rem; font-weight: 600;
}
.metric-card.danger::before  { background: linear-gradient(90deg, var(--crimson), #e97316); }
.metric-card.danger .metric-value { color: var(--crimson); }
.metric-card.info .metric-value   { color: var(--steel); }

/* ─── BUTTONS ─── */
.stButton > button {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text-sub) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    border-radius: 8px !important;
    transition: all 0.15s ease !important;
    padding: 0.45rem 1rem !important;
}
.stButton > button:hover {
    border-color: var(--steel) !important;
    color: var(--steel) !important;
    background: var(--steel-light) !important;
    box-shadow: 0 2px 8px rgba(46,95,163,0.14) !important;
}
.stButton > button[kind="primary"] {
    background: var(--steel) !important;
    border-color: var(--steel) !important;
    color: #fff !important;
    box-shadow: 0 2px 10px rgba(46,95,163,0.28) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--navy) !important;
    border-color: var(--navy) !important;
}

/* ─── SIDEBAR ─── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1b2a4a 0%, #1e3158 100%) !important;
    border-right: none;
}
[data-testid="stSidebar"] > div { padding-top: 1.5rem; }
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stDateInput label,
[data-testid="stSidebar"] .stSlider label {
    color: rgba(255,255,255,0.65) !important;
    font-size: 0.78rem !important;
}
[data-testid="stSidebar"] .section-title {
    color: rgba(255,255,255,0.40) !important;
    border-bottom-color: rgba(255,255,255,0.08) !important;
}
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stDateInput input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    color: #fff !important;
    border-radius: 7px !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    color: #fff !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: var(--steel) !important;
    border-color: transparent !important;
    color: #fff !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #3a70b8 !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.09) !important; }
[data-testid="stSidebar"] .stSuccess { background: rgba(21,128,61,0.2) !important; }
[data-testid="stSidebar"] .stError   { background: rgba(185,28,28,0.2) !important; }
[data-testid="stSidebar"] .stInfo    { background: rgba(46,95,163,0.2) !important; }

/* ─── FILTERS EXPANDER ─── */
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    box-shadow: var(--shadow) !important;
}

/* ─── MAIN INPUT FIELDS ─── */
.stTextInput input, .stDateInput input,
.stSelectbox > div > div, .stMultiSelect > div > div,
.stNumberInput input {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 7px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.87rem !important;
}
.stTextInput input:focus {
    border-color: var(--steel) !important;
    box-shadow: 0 0 0 3px rgba(46,95,163,0.10) !important;
}
.stMultiSelect span[data-baseweb="tag"] {
    background: var(--steel-light) !important;
    color: var(--steel) !important;
    border: 1px solid var(--steel-mid) !important;
    border-radius: 4px !important;
    font-size: 0.74rem !important;
}

/* ─── STATUS BANNER ─── */
.status-bar {
    background: var(--steel-light);
    border: 1px solid var(--steel-mid);
    border-radius: 8px;
    padding: 0.5rem 1.1rem;
    font-size: 0.82rem; color: var(--steel);
    font-weight: 500; margin-bottom: 0.8rem;
}

/* ─── LEGEND CARD ─── */
.legend-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px; padding: 1rem 1.1rem;
    box-shadow: var(--shadow);
}
.legend-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.12em;
    color: var(--text-sub); margin-bottom: 0.8rem;
}
.legend-item {
    display: flex; align-items: center;
    gap: 8px; margin: 5px 0;
    font-size: 0.71rem; color: var(--text-sub);
    line-height: 1.4;
}
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

/* ─── BRIEFING BOX ─── */
.briefing-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--steel);
    border-radius: 10px;
    padding: 2rem 2.4rem;
    font-family: 'Inter', sans-serif;
    line-height: 1.9; font-size: 0.9rem;
    color: var(--text); white-space: pre-wrap;
    box-shadow: var(--shadow-md);
}
.briefing-stamp {
    display: inline-flex; align-items: center; gap: 0.6rem;
    background: var(--navy); color: #fff;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.16em; text-transform: uppercase;
    padding: 0.32rem 0.9rem; border-radius: 5px;
    margin-bottom: 1.3rem;
}
.risk-critical { background: var(--crimson-light); color: var(--crimson); font-weight: 700; padding: 1px 6px; border-radius: 3px; }
.risk-high     { background: #fef3c7; color: #b45309; font-weight: 700; padding: 1px 6px; border-radius: 3px; }
.risk-medium   { background: #fefce8; color: #92400e; font-weight: 600; padding: 1px 6px; border-radius: 3px; }
.risk-low      { background: var(--green-light); color: var(--green); font-weight: 600; padding: 1px 6px; border-radius: 3px; }

/* ─── DATAFRAME ─── */
.stDataFrame { border: 1px solid var(--border) !important; border-radius: 8px !important; overflow: hidden; }

/* ─── WELCOME SCREEN ─── */
.welcome-wrap { text-align: center; padding: 5rem 2rem; }
.welcome-icon { font-size: 3.8rem; margin-bottom: 1.2rem; }
.welcome-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.5rem; font-weight: 700;
    color: var(--navy); letter-spacing: 0.04em; margin-bottom: 0.7rem;
}
.welcome-sub {
    font-size: 0.9rem; color: var(--text-sub);
    max-width: 540px; margin: 0 auto; line-height: 1.75;
}
.welcome-steps {
    display: flex; justify-content: center; gap: 1.5rem;
    margin-top: 2.8rem; flex-wrap: wrap;
}
.step-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.3rem 1.6rem;
    width: 158px; box-shadow: var(--shadow);
    transition: transform 0.15s;
}
.step-card:hover { transform: translateY(-3px); }
.step-num {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.6rem; font-weight: 700; color: var(--steel);
}
.step-text { font-size: 0.78rem; color: var(--text-sub); margin-top: 0.4rem; line-height: 1.45; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
ACLED_CONFIG = {
    "token_url":    "https://acleddata.com/oauth/token",
    "api_read_url": "https://acleddata.com/api/acled/read?_format=json",
}

BASEMAPS = {
    "🗺️ Voyager (Recommended)":   "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
    "⬜ Positron (Clean Light)":   "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "🌲 Stadia Outdoors":          "https://tiles.stadiamaps.com/styles/outdoors.json",
    "🌑 Dark Matter":              "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    "🌆 Stadia Smooth Dark":       "https://tiles.stadiamaps.com/styles/alidade_smooth_dark.json",
}

EVENT_COLORS = {
    "Battles":                    [185, 28,  28,  215],
    "Violence against civilians": [217, 119,  6,  215],
    "Explosions/Remote violence": [161, 100,  0,  215],
    "Protests":                   [37,   99, 235, 215],
    "Riots":                      [124,  58, 237, 215],
    "Strategic developments":     [5,   150, 105, 215],
}
DEFAULT_COLOR = [71, 85, 105, 180]

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
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# API FUNCTIONS
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
# LLM BRIEFING
# ─────────────────────────────────────────────────────────────────────────────
def call_ollama(prompt: str, model: str = "mistral", host: str = "http://localhost:11434") -> str:
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
        return None


def call_huggingface(prompt: str, hf_token: str = "") -> str:
    """
    STRICT FIX for 410 Error: 
    Combines the new 'router' domain with the mandatory '/hf-inference/' prefix.
    """
    # This is the exact URL required to bypass the 410 error
    url = "https://router.huggingface.co/hf-inference/v1/chat/completions"

    if not hf_token:
        return "❌ Error: Please enter your Hugging Face Token in the sidebar."

    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json"
    }

    # Using Mistral v0.3 via the OpenAI-compatible Chat format
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "messages": [
            {
                "role": "system", 
                "content": "You are a professional security analyst. Write a structured briefing based on the data provided."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "max_tokens": 1500,
        "temperature": 0.3
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        # Handle the model loading state
        if response.status_code == 503:
            return "⏳ Model is loading on Hugging Face servers. Please wait 30 seconds and try again."
        
        # Raise error for 410, 404, 401, etc.
        response.raise_for_status()
        
        result = response.json()
        
        # Parse the OpenAI-style response format
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
            
        return f"Unexpected response: {str(result)}"

    except requests.exceptions.HTTPError as err:
        return f"HF API Error: {err.response.status_code} - {err.response.text}"
    except Exception as e:
        return f"Unexpected Error: {str(e)}"

def build_briefing_prompt(df: pd.DataFrame, context: str = "") -> str:
    total_events     = len(df)
    total_fatalities = int(df["fatalities"].sum())
    date_range       = (f"{df['event_date'].min().strftime('%d %b %Y')} – "
                        f"{df['event_date'].max().strftime('%d %b %Y')}")
    regions     = df["admin1"].dropna().value_counts().head(5).to_dict()
    event_types = df["event_type"].dropna().value_counts().to_dict()
    actors      = df["actor1"].dropna().value_counts().head(8).to_dict()
    deadliest   = (df.nlargest(3, "fatalities")
                     [["event_date", "event_type", "location", "fatalities", "notes"]]
                     .to_dict("records"))

    notes_col = df["notes"].dropna().loc[df["notes"].str.strip() != ""]
    notes_sample = notes_col.sample(min(20, len(notes_col)), random_state=42).tolist()
    notes_block  = "\n".join(f"- {n[:400]}" for n in notes_sample)

    deadliest_block = "\n".join(
        f"  [{r['event_date'].strftime('%d %b %Y') if hasattr(r['event_date'], 'strftime') else r['event_date']}] "
        f"{r['event_type']} in {r['location']} – {int(r['fatalities'])} fatalities. "
        f"{str(r.get('notes', ''))[:200]}"
        for r in deadliest
    )

    prompt = f"""You are a professional security analyst. Write a structured intelligence briefing in plain text.
Use the verified data below. Be concise, analytical, and objective.
Do NOT use markdown symbols like ** or ##. Use plain section titles in ALL CAPS.

--- DATA SUMMARY ---
Period          : {date_range}
Total Events    : {total_events}
Total Fatalities: {total_fatalities}
Top Regions     : {json.dumps(regions)}
Event Types     : {json.dumps(event_types)}
Key Actors      : {json.dumps(actors)}

DEADLIEST INCIDENTS:
{deadliest_block}

SAMPLE INCIDENT NOTES:
{notes_block}

{"ANALYST FOCUS: " + context if context else ""}

--- REQUIRED OUTPUT STRUCTURE (use exactly these ALL-CAPS titles) ---

SITUATION OVERVIEW
[2-3 sentences on the overall security situation]

KEY FINDINGS
[3-5 bullet points with the most significant patterns and numbers]

THREAT ACTORS
[Brief paragraph on dominant actors and their activity patterns]

GEOGRAPHIC HOTSPOTS
[2-3 most affected areas with specific data points]

TREND ANALYSIS
[Describe escalation, de-escalation, or tactical shifts based on the notes]

RISK ASSESSMENT
[One line: Overall risk level is LOW / MEDIUM / HIGH / CRITICAL — one-sentence justification]

RECOMMENDATIONS
[2-3 actionable recommendations for operational or policy planning]

--- END BRIEFING ---
"""
    return prompt


def generate_briefing(df, context, llm_source, ollama_host, ollama_model, hf_token):
    prompt = build_briefing_prompt(df, context)
    if llm_source == "Ollama (Local)":
        result = call_ollama(prompt, model=ollama_model, host=ollama_host)
        if result is None:
            return "❌ Cannot connect to Ollama. Ensure it is running at the configured host."
        return result
    elif llm_source == "HuggingFace Router (Free)":
        return call_huggingface(prompt, hf_token)
    return "No LLM source configured."


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
today_str = date.today().strftime("%d %b %Y").upper()
st.markdown(f"""
<div class="main-header">
  <div class="header-left">
    <h1>🛡️ Security Data Explorer</h1>
    <p>ACLED — Advanced Conflict Intelligence Platform</p>
  </div>
  <div class="header-badge">⬤ &nbsp;Live · {today_str}</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-title">⚙ Data Source</div>', unsafe_allow_html=True)

    try:
        email    = st.secrets["acled"]["email"]
        password = st.secrets["acled"]["password"]
        st.success("✅ Credentials loaded")
    except Exception:
        st.error("❌ Missing ACLED credentials")
        st.info("Add [acled] email + password to .streamlit/secrets.toml")
        st.stop()

    countries_input = st.text_input("Countries (comma-separated)", "Palestine, Israel")
    countries_list  = [c.strip() for c in countries_input.split(",") if c.strip()]

    col1, col2 = st.columns(2)
    start_date = col1.date_input("From", date.today() - timedelta(days=30))
    end_date   = col2.date_input("To",   date.today())

    fetch_button = st.button("🚀 Fetch Data", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="section-title">🗺 Map Settings</div>', unsafe_allow_html=True)

    basemap_choice     = st.selectbox("Basemap", list(BASEMAPS.keys()), index=0)
    selected_map_style = BASEMAPS[basemap_choice]
    point_radius       = st.slider("Point Radius (m)", 500, 8000, 2000, 250)
    point_opacity      = st.slider("Point Opacity",    0.1, 1.0,  0.75, 0.05)
    zoom_level         = st.slider("Default Zoom",     4,   14,   7)

    st.markdown("---")
    st.markdown('<div class="section-title">🤖 Briefing LLM</div>', unsafe_allow_html=True)

    llm_source = st.selectbox(
        "LLM Backend",
        ["Ollama (Local)", "HuggingFace Router (Free)"],
        help="Ollama: private local inference. HuggingFace: free cloud API (router endpoint)."
    )

    if llm_source == "Ollama (Local)":
        ollama_host  = st.text_input("Ollama Host", "http://localhost:11434")
        ollama_model = st.text_input("Model", "mistral",
                                     help="mistral · llama3 · phi3 · gemma2")
        hf_token = ""
    else:
        st.caption("Free: `microsoft/phi-2` (no token)  |  Better: `Mistral-7B` with token")
        hf_token     = st.text_input("HF Token (optional)", type="password",
                                     help="Free token at huggingface.co/settings/tokens")
        ollama_host  = ""
        ollama_model = ""

# ─────────────────────────────────────────────────────────────────────────────
# FETCH DATA
# ─────────────────────────────────────────────────────────────────────────────
if fetch_button:
    token = get_access_token(email, password, ACLED_CONFIG["token_url"])
    if token:
        with st.spinner("Fetching conflict data from ACLED…"):
            raw_df = fetch_acled_data(token, tuple(countries_list), start_date, end_date)
            if not raw_df.empty:
                raw_df["event_date"] = pd.to_datetime(raw_df["event_date"])
                raw_df["latitude"]   = pd.to_numeric(raw_df["latitude"],   errors="coerce")
                raw_df["longitude"]  = pd.to_numeric(raw_df["longitude"],  errors="coerce")
                raw_df["fatalities"] = pd.to_numeric(raw_df["fatalities"], errors="coerce").fillna(0)
                raw_df = raw_df.dropna(subset=["latitude", "longitude"])

                st.session_state.original_df  = raw_df
                st.session_state.data_fetched = True
                st.session_state.selected_temporal_date = raw_df["event_date"].min().date()
                st.session_state.briefing_text = ""
                st.rerun()
            else:
                st.warning("No data returned. Try different countries or a wider date range.")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.data_fetched:
    full_df = st.session_state.original_df.copy()

    # ══════════════════════════════════════════════════════════════════════════
    # FILTERS
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("🔍  Advanced Filters", expanded=True):
        fc1, fc2, fc3, fc4 = st.columns(4)

        all_event_types = sorted(full_df["event_type"].dropna().unique().tolist())
        sel_event_types = fc1.multiselect("Event Type", all_event_types,
                                          default=all_event_types, key="f_et")

        all_sub = sorted(full_df["sub_event_type"].dropna().unique().tolist())
        sel_sub = fc2.multiselect("Sub-Event Type", all_sub, default=all_sub, key="f_se")

        all_countries = sorted(full_df["country"].dropna().unique().tolist())
        sel_countries = fc3.multiselect("Country", all_countries,
                                        default=all_countries, key="f_co")

        all_admin1 = sorted(full_df["admin1"].dropna().unique().tolist())
        sel_admin1 = fc4.multiselect("Region (Admin1)", all_admin1,
                                     default=all_admin1, key="f_a1")

        fc5, fc6, fc7 = st.columns(3)

        avail_admin2 = sorted(
            full_df[full_df["admin1"].isin(sel_admin1)]["admin2"].dropna().unique().tolist()
        )
        sel_admin2 = fc5.multiselect("District (Admin2)", avail_admin2,
                                     default=avail_admin2, key="f_a2")

        all_actors = sorted(full_df["actor1"].dropna().unique().tolist())
        sel_actors = fc6.multiselect("Primary Actor", all_actors,
                                     default=all_actors, key="f_ac")

        max_fat   = int(full_df["fatalities"].max()) or 1
        fat_range = fc7.slider("Fatalities Range", 0, max_fat, (0, max_fat), key="f_fr")

    # Apply filters
    filtered_df = full_df[
        full_df["event_type"].isin(sel_event_types) &
        full_df["sub_event_type"].isin(sel_sub) &
        full_df["country"].isin(sel_countries) &
        full_df["admin1"].isin(sel_admin1) &
        full_df["actor1"].isin(sel_actors) &
        full_df["fatalities"].between(fat_range[0], fat_range[1])
    ].copy()
    if sel_admin2:
        filtered_df = filtered_df[filtered_df["admin2"].isin(sel_admin2)]

    st.markdown(
        f'<div class="status-bar">'
        f'🔎 Showing <strong>{len(filtered_df):,}</strong> events after filters'
        f'&nbsp;&nbsp;|&nbsp;&nbsp;{len(full_df):,} total records loaded'
        f'</div>',
        unsafe_allow_html=True
    )

    # ══════════════════════════════════════════════════════════════════════════
    # KEY METRICS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">📊 Key Metrics</div>', unsafe_allow_html=True)

    days_span = max((filtered_df["event_date"].max() - filtered_df["event_date"].min()).days, 1)
    avg_daily = len(filtered_df) / days_span

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-card info"><div class="metric-value">{len(filtered_df):,}</div><div class="metric-label">Total Events</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card danger"><div class="metric-value">{int(filtered_df["fatalities"].sum()):,}</div><div class="metric-label">Fatalities</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-value">{filtered_df["admin1"].nunique()}</div><div class="metric-label">Regions Affected</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-value">{days_span}</div><div class="metric-label">Day Span</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-card"><div class="metric-value">{avg_daily:.1f}</div><div class="metric-label">Avg Events / Day</div></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # MAP
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">🗺 Geospatial Distribution</div>', unsafe_allow_html=True)

    mc = st.columns(5)
    for idx, (label, key) in enumerate([
        ("🎨 Categories", "Categories"),
        ("🔥 Heatmap",    "Heatmap"),
        ("🎯 Impact",     "Impact"),
        ("⏳ Temporal",   "Temporal"),
        ("📍 Cluster",    "Cluster"),
    ]):
        if mc[idx].button(label, use_container_width=True):
            st.session_state.map_mode = key

    display_df = filtered_df.copy()

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
            pc1, pc2, _ = st.columns([1, 1, 5])
            if pc1.button("▶️ Play"):  st.session_state.is_playing = True
            if pc2.button("⏸️ Stop"):  st.session_state.is_playing = False
            st.caption(f"{selected_date}  ·  {len(display_df)} events")
            if st.session_state.is_playing and unique_dates:
                time.sleep(0.4)
                idx_now = unique_dates.index(selected_date)
                st.session_state.selected_temporal_date = unique_dates[(idx_now + 1) % len(unique_dates)]
                st.rerun()

    lat_c = display_df["latitude"].mean()  if not display_df.empty else 32.0
    lon_c = display_df["longitude"].mean() if not display_df.empty else 35.0
    view_state = pdk.ViewState(latitude=lat_c, longitude=lon_c, zoom=zoom_level, pitch=0)

    tooltip = {
        "html": (
            "<div style='font-family:Inter,sans-serif;font-size:12px;padding:8px 10px;line-height:1.6;'>"
            "<b style='color:#2e5fa3;font-size:13px;'>{event_type}</b><br/>"
            "📍 {location}<br/>"
            "👤 {actor1}<br/>"
            "💀 Fatalities: <b>{fatalities}</b><br/>"
            "<span style='color:#666;font-size:11px;'>{notes}</span>"
            "</div>"
        ),
        "style": {
            "background": "#ffffff",
            "color": "#1e2b3c",
            "border": "1px solid #d1dae8",
            "border-radius": "8px",
            "box-shadow": "0 4px 14px rgba(0,0,0,0.10)",
            "max-width": "300px",
        }
    }

    mode = st.session_state.map_mode

    if mode == "Heatmap":
        layers = [pdk.Layer(
            "HeatmapLayer", display_df,
            get_position="[longitude, latitude]",
            get_weight="fatalities",
            opacity=point_opacity, threshold=0.05, radiusPixels=40,
        )]
    elif mode == "Impact":
        dm = display_df.copy()
        max_f = dm["fatalities"].max() or 1
        dm["radius"] = (dm["fatalities"] / max_f) * 15000 + 800
        dm["color"]  = dm["fatalities"].apply(
            lambda f: [185, 28, 28, min(220, int(120 + f * 4))]
        )
        layers = [pdk.Layer(
            "ScatterplotLayer", dm,
            get_position="[longitude, latitude]",
            get_radius="radius", get_fill_color="color",
            pickable=True, stroked=True,
            get_line_color=[255, 255, 255], line_width_min_pixels=1,
        )]
    elif mode == "Cluster":
        layers = [pdk.Layer(
            "ScatterplotLayer", display_df,
            get_position="[longitude, latitude]",
            get_radius=int(point_radius * 0.6),
            get_fill_color=[46, 95, 163, 160], pickable=True,
        )]
    else:
        dm = display_df.copy()
        dm["color"] = dm["event_type"].apply(lambda e: EVENT_COLORS.get(e, DEFAULT_COLOR))
        layers = [pdk.Layer(
            "ScatterplotLayer", dm,
            get_position="[longitude, latitude]",
            get_radius=point_radius, get_fill_color="color",
            opacity=point_opacity, pickable=True,
            auto_highlight=True, highlight_color=[255, 200, 0, 255],
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
            lines = '<div class="legend-card"><div class="legend-title">Event Types</div>'
            for etype, rgba in EVENT_COLORS.items():
                hc = "#{:02x}{:02x}{:02x}".format(*rgba[:3])
                lines += (f'<div class="legend-item">'
                          f'<div class="legend-dot" style="background:{hc};"></div>'
                          f'{etype}</div>')
            lines += '</div>'
            st.markdown(lines, unsafe_allow_html=True)
        elif mode == "Heatmap":
            st.markdown('<div class="legend-card"><div class="legend-title">Heatmap</div>'
                        '<p style="font-size:0.71rem;color:#5a6b7e;">Intensity weighted by fatality count.</p></div>',
                        unsafe_allow_html=True)
        elif mode == "Impact":
            st.markdown('<div class="legend-card"><div class="legend-title">Impact</div>'
                        '<p style="font-size:0.71rem;color:#5a6b7e;">Circle size and colour reflect fatality count.</p></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="legend-card"><div class="legend-title">Cluster</div>'
                        '<p style="font-size:0.71rem;color:#5a6b7e;">Events as uniform blue dots.</p></div>',
                        unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">📈 Analytics Dashboard</div>', unsafe_allow_html=True)

    PALETTE     = ["#2e5fa3", "#b91c1c", "#d97706", "#7c3aed", "#15803d", "#0891b2"]
    PLOT_LAYOUT = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#1e2b3c", font_family="Inter",
        title_font_color="#1b2a4a", title_font_size=14,
        margin=dict(l=10, r=10, t=42, b=10),
    )

    ac1, ac2 = st.columns(2)

    with ac1:
        fig_pie = px.pie(
            filtered_df, names="event_type",
            title="Event Type Distribution",
            color_discrete_sequence=PALETTE, hole=0.42,
        )
        fig_pie.update_layout(**PLOT_LAYOUT)
        fig_pie.update_traces(textfont_size=11)
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
            name="Events", marker_color="#c8d9f0", opacity=0.9
        ))
        fig_tl.add_trace(go.Scatter(
            x=timeline["event_date"], y=timeline["fatalities"],
            name="Fatalities", mode="lines+markers",
            line=dict(color="#b91c1c", width=2.5),
            marker=dict(size=4), yaxis="y2"
        ))
        fig_tl.update_layout(
            **PLOT_LAYOUT, title="Events & Fatalities Timeline",
            xaxis=dict(gridcolor="rgba(0,0,0,0.05)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0.05)", title="Events"),
            yaxis2=dict(overlaying="y", side="right", title="Fatalities",
                        gridcolor="rgba(0,0,0,0)"),
            legend=dict(orientation="h", y=1.1, font=dict(size=11)), bargap=0.15,
        )
        st.plotly_chart(fig_tl, use_container_width=True)

    ac3, ac4 = st.columns(2)

    with ac3:
        top_regions = (
            filtered_df.groupby("admin1")
            .agg(events=("event_id_cnty", "count"), fatalities=("fatalities", "sum"))
            .sort_values("fatalities", ascending=True).tail(12).reset_index()
        )
        fig_bar = px.bar(
            top_regions, x="fatalities", y="admin1", orientation="h",
            title="Top Regions by Fatalities",
            color="events", color_continuous_scale=["#c8d9f0", "#1b2a4a"],
        )
        fig_bar.update_layout(
            **PLOT_LAYOUT,
            xaxis=dict(gridcolor="rgba(0,0,0,0.06)"), yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            coloraxis_colorbar=dict(tickfont=dict(color="#4e5f72", size=10)),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with ac4:
        top_actors = (
            filtered_df.groupby("actor1")
            .agg(events=("event_id_cnty", "count"), fatalities=("fatalities", "sum"))
            .sort_values("events", ascending=False).head(10).reset_index()
        )
        fig_act = px.bar(
            top_actors, x="actor1", y="events",
            title="Top 10 Actors by Event Count",
            color="fatalities", color_continuous_scale=["#fde8e8", "#b91c1c"],
        )
        fig_act.update_layout(
            **PLOT_LAYOUT,
            xaxis=dict(tickangle=-35, gridcolor="rgba(0,0,0,0.06)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
            coloraxis_colorbar=dict(tickfont=dict(color="#4e5f72", size=10)),
        )
        st.plotly_chart(fig_act, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # DATA EXPLORER  (always visible, no expander)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">📋 Detailed Data Explorer</div>', unsafe_allow_html=True)

    cols_to_show = [c for c in [
        "event_date", "event_type", "sub_event_type", "country",
        "admin1", "admin2", "location", "actor1", "actor2",
        "fatalities", "notes", "source"
    ] if c in filtered_df.columns]

    search_term = st.text_input(
        "Search within results",
        placeholder="Filter by keyword — searches all text columns…",
        key="table_search"
    )
    show_df = filtered_df[cols_to_show].copy()
    if search_term.strip():
        mask = show_df.apply(
            lambda col: col.astype(str).str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        show_df = show_df[mask]
        st.caption(f'Showing {len(show_df):,} matching rows for "{search_term}"')

    st.dataframe(
        show_df,
        use_container_width=True,
        height=420,
        column_config={
            "event_date":    st.column_config.DateColumn("Date", format="DD MMM YYYY"),
            "fatalities":    st.column_config.NumberColumn("Fatalities", format="%d ☠"),
            "notes":         st.column_config.TextColumn("Notes", width="large"),
            "event_type":    st.column_config.TextColumn("Event Type", width="medium"),
            "sub_event_type":st.column_config.TextColumn("Sub-Type", width="medium"),
        }
    )

    dl1, dl2 = st.columns(2)
    dl1.download_button(
        "📥 Download Filtered Data (CSV)",
        filtered_df.to_csv(index=False),
        f"acled_filtered_{date.today()}.csv",
        "text/csv", use_container_width=True,
    )
    dl2.download_button(
        "📥 Download Current Table View",
        show_df.to_csv(index=False),
        f"acled_view_{date.today()}.csv",
        "text/csv", use_container_width=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # AUTO BRIEFING
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">📝 Auto Briefing Generator</div>', unsafe_allow_html=True)

    bg1, bg2 = st.columns([3, 1])
    with bg1:
        analyst_context = st.text_area(
            "Analyst Focus / Custom Instructions (optional)",
            placeholder="e.g. Focus on civilian impact in northern districts. Highlight any IED usage patterns.",
            height=85,
        )
    with bg2:
        max_events_llm = st.number_input(
            "Max Events for LLM", min_value=10, max_value=500, value=150, step=10,
            help="More events = richer briefing but slower generation."
        )
        gen_btn = st.button("⚡ Generate Briefing", type="primary", use_container_width=True)

    if gen_btn:
        if filtered_df.empty:
            st.warning("No data available. Adjust filters and try again.")
        else:
            sample_df = (
                filtered_df.sample(min(max_events_llm, len(filtered_df)), random_state=42)
                if len(filtered_df) > max_events_llm else filtered_df.copy()
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
        text_html = (
            text.replace("CRITICAL", '<span class="risk-critical">CRITICAL</span>')
                .replace(" HIGH ",   ' <span class="risk-high">HIGH</span> ')
                .replace(" MEDIUM ", ' <span class="risk-medium">MEDIUM</span> ')
                .replace(" LOW ",    ' <span class="risk-low">LOW</span> ')
        )
        st.markdown(
            f'<div class="briefing-box">'
            f'<div class="briefing-stamp">🛡️ Intelligence Briefing &nbsp;·&nbsp; Auto-Generated &nbsp;·&nbsp; {today_str}</div>'
            f'{text_html}</div>',
            unsafe_allow_html=True,
        )
        bc1, bc2 = st.columns(2)
        bc1.download_button(
            "📥 Download Briefing (.txt)",
            data=st.session_state.briefing_text,
            file_name=f"briefing_{date.today()}.txt",
            mime="text/plain", use_container_width=True,
        )
        if bc2.button("🗑️ Clear Briefing", use_container_width=True):
            st.session_state.briefing_text = ""
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# WELCOME STATE
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div class="welcome-wrap">
        <div class="welcome-icon">🛡️</div>
        <div class="welcome-title">Security Data Explorer</div>
        <div class="welcome-sub">
            Configure your parameters in the sidebar and click <strong>Fetch Data</strong> to load
            ACLED conflict events. Explore interactive maps, analytics, and generate
            AI-powered intelligence briefings.
        </div>
        <div class="welcome-steps">
            <div class="step-card">
                <div class="step-num">01</div>
                <div class="step-text">Set countries &amp; date range in the sidebar</div>
            </div>
            <div class="step-card">
                <div class="step-num">02</div>
                <div class="step-text">Click Fetch Data to load ACLED events</div>
            </div>
            <div class="step-card">
                <div class="step-num">03</div>
                <div class="step-text">Filter, explore maps &amp; review analytics</div>
            </div>
            <div class="step-card">
                <div class="step-num">04</div>
                <div class="step-text">Generate an AI intelligence briefing</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)






