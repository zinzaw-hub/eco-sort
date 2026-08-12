import streamlit as st
from ultralytics import YOLO
from PIL import Image
import os
from datetime import datetime
import plotly.graph_objects as go
from groq import Groq
import base64
import io
import json

# ==========================================
# PAGE CONFIGURATION & SETUP
# ==========================================
st.set_page_config(
    page_title="EcoSort",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

STATS_FILE = "global_stats.json"

# ==========================================
# GLOBAL STATS FUNCTIONS
# ==========================================
def load_global_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"total_scans": 0, "plastic_types": {}, "history": []}
    else:
        return {"total_scans": 0, "plastic_types": {}, "history": []}

def save_global_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)

if "global_stats" not in st.session_state:
    st.session_state.global_stats = load_global_stats()

# ==========================================
# THEME STYLING
# ==========================================
def apply_theme(dark):
    if dark:
        bg        = "#14213D"
        card_bg   = "#1B2A4A"
        sidebar   = "#0F1830"
        text      = "#F1FAEE"
        muted     = "#8D99AE"
        accent    = "#06D6A0"
        accent2   = "#FFD166"
        border    = "#2A3B5C"
        success_bg = "#16352A"
        success_c  = "#06D6A0"
        error_bg   = "#3D1F2B"
        error_c    = "#EF476F"
        uploader_bg = "#1B2A4A"
        uploader_border = "#2A3B5C"
    else:
        bg        = "#F0FBF4"
        card_bg   = "#FFFFFF"
        sidebar   = "#E8F8ED"
        text      = "#1B4332"
        muted     = "#5C8374"
        accent    = "#06D6A0"
        accent2   = "#FFD166"
        border    = "#C8F0D9"
        success_bg = "#D8F5E0"
        success_c  = "#06A77D"
        error_bg   = "#FFE3E3"
        error_c    = "#EF476F"
        uploader_bg = "#FFFFFF"
        uploader_border = "#C8F0D9"

    st.session_state["_theme"] = dict(
        bg=bg, card_bg=card_bg, text=text, muted=muted,
        accent=accent, accent2=accent2, border=border,
    )

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Nunito:wght@300;400;600;700&display=swap');

    .stApp {{
        background-color: {bg} !important;
        font-family: 'Nunito', sans-serif;
    }}
    .stApp, .stApp p, .stApp div, .stApp span, .stApp label {{
        color: {text} !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {sidebar} !important;
        border-right: 1px solid {border};
    }}
    section[data-testid="stSidebar"] * {{
        color: {text} !important;
    }}
    [data-testid="stFileUploader"] {{
        background-color: {uploader_bg} !important;
        border: 3px dashed {accent} !important;
        border-radius: 20px !important;
        padding: 1rem !important;
    }}
    [data-testid="stFileUploader"] section {{
        background-color: {uploader_bg} !important;
    }}
    [data-testid="stFileUploader"] * {{
        color: {text} !important;
        fill: {text} !important;
    }}
    [data-testid="stFileUploaderFileName"] {{
        color: {text} !important;
    }}
    [data-testid="stFileUploaderDeleteBtn"] button {{
        color: {text} !important;
    }}
    [data-testid="stFileUploader"] button {{
        background-color: {card_bg} !important;
        color: {text} !important;
        border: 1px solid {border} !important;
    }}
    .eco-header {{
        text-align: center;
        padding: 1.5rem 0 1rem;
    }}
    .eco-title {{
        font-family: 'Baloo 2', sans-serif;
        font-size: 3.2rem;
        font-weight: 800;
        color: {accent} !important;
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1.1;
    }}
    .eco-subtitle {{
        font-size: 0.8rem;
        color: {muted} !important;
        margin-top: 0.4rem;
        font-weight: 600;
        letter-spacing: 3px;
        text-transform: uppercase;
    }}
    .result-card {{
        background: {card_bg};
        border: 2px solid {border};
        border-radius: 28px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 24px rgba(6,214,160,0.12);
        position: relative;
        overflow: hidden;
    }}
    .result-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 6px;
        background: linear-gradient(90deg, {accent}, {accent2});
        border-radius: 28px 28px 0 0;
    }}
    .plastic-name {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {text} !important;
        margin: 0.3rem 0 0.1rem;
    }}
    .plastic-fullname {{
        font-size: 0.82rem;
        color: {muted} !important;
        font-weight: 500;
        letter-spacing: 0.5px;
    }}
    .badge-recyclable {{
        display: inline-block;
        background: {success_bg};
        color: {success_c} !important;
        border: 2px solid {success_c}88;
        padding: 0.35rem 1.2rem;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 700;
        margin-top: 0.8rem;
    }}
    .badge-non {{
        display: inline-block;
        background: {error_bg};
        color: {error_c} !important;
        border: 2px solid {error_c}88;
        padding: 0.35rem 1.2rem;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 700;
        margin-top: 0.8rem;
    }}
    .conf-label {{
        font-size: 0.75rem;
        color: {muted} !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 1rem 0 0.4rem;
        font-weight: 700;
    }}
    .conf-bar-bg {{
        background: {border};
        border-radius: 8px;
        height: 10px;
        overflow: hidden;
    }}
    .examples-text {{
        font-size: 1rem;
        color: {muted} !important;
        margin-top: 0.5rem;
    }}
    .guidance-box {{
        background: {accent}20;
        border-left: 4px solid {accent};
        border-radius: 0 16px 16px 0;
        padding: 1rem 1.5rem;
        margin-top: 0.5rem;
        font-size: 0.9rem;
        color: {text} !important;
        line-height: 1.7;
    }}
    .guidance-list {{
        list-style: none;
        margin: 0;
        padding: 0;
    }}
    .guidance-list li {{
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        margin-bottom: 0.5rem;
    }}
    .guidance-list li:last-child {{
        margin-bottom: 0;
    }}
    .guidance-list li::before {{
        content: "♻";
        flex-shrink: 0;
        color: {accent};
        font-weight: 700;
    }}
    .divider {{
        border: none;
        border-top: 2px solid {border};
        margin: 1.2rem 0;
    }}
    .section-title {{
        font-family: 'Baloo 2', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
        color: {text} !important;
        margin: 1.5rem 0 0.8rem;
    }}
    .empty-state {{
        text-align: center;
        padding: 5rem 2rem;
        color: {muted};
    }}
    .sidebar-logo {{
        font-family: 'Baloo 2', sans-serif;
        font-size: 1.5rem;
        font-weight: 800;
        color: {accent} !important;
    }}
    .sidebar-info {{
        background: {card_bg};
        border: 2px solid {border};
        border-radius: 16px;
        padding: 1rem;
        margin-top: 1rem;
        font-size: 0.8rem;
        color: {muted} !important;
        line-height: 1.8;
    }}
    .class-chip {{
        display: inline-block;
        background: {accent}22;
        border: 1px solid {accent}55;
        border-radius: 20px;
        padding: 0.25rem 0.8rem;
        font-size: 0.75rem;
        font-weight: 700;
        margin: 0.2rem;
        color: {text} !important;
    }}
    .about-p {{
        font-size: 0.95rem;
        line-height: 1.8;
        color: {text} !important;
        margin-bottom: 0.8rem;
    }}
    .chart-caption {{
        font-size: 0.72rem;
        color: {muted} !important;
        line-height: 1.6;
        margin-top: 0.5rem;
    }}
    .metric-card {{
        background: {card_bg};
        border: 2px solid {border};
        border-radius: 20px;
        padding: 1.2rem;
        text-align: center;
    }}
    .metric-value {{
        font-family: 'Baloo 2', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: {accent} !important;
        line-height: 1.1;
    }}
    .metric-label {{
        font-size: 0.75rem;
        color: {muted} !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 700;
        margin-top: 0.3rem;
    }}
    [data-testid="stSidebar"] button[kind="secondary"] {{
        background: {card_bg} !important;
        color: {text} !important;
        border: 2px solid {border} !important;
        border-radius: 14px !important;
        justify-content: flex-start !important;
        padding: 0.65rem 1rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }}
    [data-testid="stSidebar"] button[kind="secondary"]:hover {{
        background: {accent}22 !important;
        border-color: {accent} !important;
        color: {accent} !important;
    }}
    .nav-active-marker {{
        display: none;
    }}
    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.nav-active-marker)
        + div[data-testid="stElementContainer"] button,
    [data-testid="stSidebar"] div.element-container:has(.nav-active-marker)
        + div.element-container button,
    [data-testid="stSidebar"] .nav-active-marker + div[data-testid="stButton"] button {{
        background: {accent} !important;
        color: #FFFFFF !important;
        border: 2px solid {accent} !important;
        box-shadow: 0 4px 12px {accent}44 !important;
    }}
    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.nav-active-marker)
        + div[data-testid="stElementContainer"] button p,
    [data-testid="stSidebar"] div.element-container:has(.nav-active-marker)
        + div.element-container button p,
    [data-testid="stSidebar"] .nav-active-marker + div[data-testid="stButton"] button p {{
        color: #FFFFFF !important;
    }}
    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.nav-active-marker)
        + div[data-testid="stElementContainer"] button:hover,
    [data-testid="stSidebar"] div.element-container:has(.nav-active-marker)
        + div.element-container button:hover,
    [data-testid="stSidebar"] .nav-active-marker + div[data-testid="stButton"] button:hover {{
        background: {accent} !important;
        color: #FFFFFF !important;
        opacity: 0.92;
    }}
    [data-testid="stImage"] {{
        background: {card_bg};
        border: 2px solid {border};
        border-radius: 28px;
        padding: 0.75rem;
        box-shadow: 0 8px 24px rgba(6,214,160,0.12);
        width: 480px;
        height: 480px;
        max-width: 100%;
        box-sizing: border-box;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        margin: 0 auto;
    }}
    [data-testid="stImage"] img {{
        height: 100%;
        width: 100%;
        object-fit: cover;
        border-radius: 18px;
        display: block;
    }}
    .result-card {{
        width: 480px;
        height: 480px;
        max-width: 100%;
        box-sizing: border-box;
        margin: 1rem auto;
        overflow-y: auto;
    }}
    .result-card.result-card-flex {{
        width: 100%;
        height: auto;
        max-width: none;
        margin: 1rem 0;
        overflow-y: visible;
    }}
    [data-testid="stDownloadButton"] button {{
        background: transparent !important;
        color: {text} !important;
        border: 2px solid {border} !important;
        border-radius: 14px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        width: 100% !important;
        transition: all 0.15s ease !important;
    }}
    [data-testid="stDownloadButton"] button:hover {{
        background: {accent}22 !important;
        border-color: {accent} !important;
        color: {accent} !important;
    }}
    [data-testid="stDownloadButton"] button p {{
        color: {text} !important;
    }}
    [data-testid="stDownloadButton"] button:hover p {{
        color: {accent} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "page" not in st.session_state:
    st.session_state.page = "Classifier"
if "last_file_key" not in st.session_state:
    st.session_state.last_file_key = None

apply_theme(st.session_state.dark_mode)

# ==========================================
# CONSTANTS & METADATA DICTIONARIES
# ==========================================
RESIN_SYMBOLS = {
    "PET": "♳", "HDPE": "♴", "LDPE": "♶",
    "PP": "♷", "PS": "♸", "Others": "♹",
}

RECYCLABILITY = {
    "PET": {
        "recyclable": True, "code": "1", "name_en": "Polyethylene Terephthalate", 
        "examples": "Water bottles, soda bottles, food jars",
        "description": "PET (Polyethylene Terephthalate) is a clear, strong, and lightweight plastic widely used for packaging foods and beverages because it helps prevent oxygen from spoiling the product inside.",
        "properties": [
            "Clear and transparent — high optical clarity",
            "Strong and shatter-resistant — handles impact well",
            "Good gas and moisture barrier — preserves freshness",
            "100% recyclable — highly demanded by recycling facilities"
        ]
    },
    "HDPE": {
        "recyclable": True, "code": "2", "name_en": "High-Density Polyethylene", 
        "examples": "Milk jugs, detergent bottles, shampoo bottles",
        "description": "HDPE (High-Density Polyethylene) is a robust, stiff plastic known for its high tensile strength and resistance to various solvents, making it ideal for rigid containers.",
        "properties": [
            "Rigid and strong — withstands heavy stacking",
            "Chemical resistant — handles household cleaners safely",
            "Weather resistant — durable against environmental exposure",
            "Widely recyclable — accepted in almost all curbside programs"
        ]
    },
    "LDPE": {
        "recyclable": True, "code": "4", "name_en": "Low-Density Polyethylene", 
        "examples": "Bread bags, squeeze bottles, shrink wrap",
        "description": "LDPE (Low-Density Polyethylene) is a flexible, soft plastic with good chemical resistance. It is less rigid than HDPE and commonly used for films and flexible packaging.",
        "properties": [
            "Flexible and soft — bends without breaking",
            "Lightweight — adds minimal weight to packaging",
            "Moisture resistant — keeps contents dry",
            "Partially recyclable — accepted at some drop-off points"
        ]
    },
    "PP": {
        "recyclable": True, "code": "5", "name_en": "Polypropylene", 
        "examples": "Yogurt tubs, bottle caps, takeout containers",
        "description": "PP (Polypropylene) is a tough, heat-resistant plastic that acts as a strong barrier against moisture, grease, and chemicals, making it great for hot-fill liquids and food storage.",
        "properties": [
            "High heat tolerance — safe for microwave and hot liquids",
            "Tough and fatigue resistant — handles repeated flexing",
            "Moisture and grease barrier — excellent for food packaging",
            "Recyclable — increasingly accepted by local programs"
        ]
    },
    "PS": {
        "recyclable": False, "code": "6", "name_en": "Polystyrene", 
        "examples": "Foam cups, takeout clamshells, packing peanuts",
        "description": "PS (Polystyrene) can be rigid or foamed (Styrofoam). It is lightweight and provides great insulation, but it is fragile and notoriously difficult to recycle economically.",
        "properties": [
            "Lightweight and insulating — keeps temperature steady",
            "Rigid or foamed variants — versatile for cheap packaging",
            "Brittle and fragile — breaks or shatters easily",
            "Generally non-recyclable — rarely accepted in standard curbside bins"
        ]
    },
    "Others": {
        "recyclable": False, "code": "7", "name_en": "Other / Mixed Plastics", 
        "examples": "Multi-layer packaging, some bioplastics",
        "description": "Others (Category 7) includes any plastic that does not fit into categories 1 through 6, often consisting of multi-layered combinations or polycarbonate plastics.",
        "properties": [
            "Mixed composition — often made of bonded layers",
            "Customizable strength and durability",
            "Hard to separate into base components",
            "Non-recyclable — goes to general landfill or specialized processing"
        ]
    },
}

COLORS = {
    "PET": "#EF476F", "HDPE": "#06D6A0", "LDPE": "#FFD166",
    "PP": "#118AB2", "PS": "#7209B7", "Others": "#FF6B35",
}

LEARN_TIPS = {
    "PET": "Empty and rinse the bottle, leave the cap on (most facilities now recycle caps too), and flatten it to save space. Avoid tossing in food-contaminated PET like oily takeout containers without rinsing first.",
    "HDPE": "Rinse out any residue (milk, detergent, shampoo), remove pumps/spray tops if possible, and recycle with the cap on. HDPE is one of the most widely and easily recycled plastics.",
    "LDPE": "Bags, wraps, and film plastic usually can't go in regular household recycling bins — check for a store drop-off point (many supermarkets collect plastic bags separately). Rigid LDPE items can often go in standard recycling.",
    "PP": "Rinse thoroughly, especially food containers and yogurt tubs. PP is recyclable but is accepted less often than PET/HDPE, so check your local program before assuming it's collected.",
    "PS": "Foam polystyrene (like packing peanuts and foam cups) is rarely accepted by curbside recycling due to its low density and contamination risk — it generally goes in general waste. Some specialized drop-off centers accept clean rigid PS.",
    "Others": "Mixed or multi-layer plastics (like chip bags and some pouches) can't be separated into a single material, so they're almost never recyclable through standard programs — dispose of them as general waste, and look for reduce/reuse alternatives where possible.",
}

# ==========================================
# AI GUIDANCE & REPORT GENERATION FUNCTIONS
# ==========================================
@st.cache_data(show_spinner=False)
def get_guidance(plastic_type, recyclable):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return ["Guidance unavailable: GROQ_API_KEY not configured."]
    try:
        client = Groq(api_key=api_key)
        prompt = (
            f"Give exactly 5 short, practical bullet points on how to properly "
            f"{'recycle' if recyclable else 'dispose of'} {plastic_type} plastic. "
            f"Each bullet must be a single short actionable sentence (under 15 words). "
            f"Reply with ONLY the bullet points, one per line, each starting with '- '. "
            f"No intro, no summary, no extra text."
        )
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=220,
        )
        raw = resp.choices[0].message.content.strip()
        points = [
            line.lstrip("-•* ").strip()
            for line in raw.splitlines()
            if line.strip()
        ]
        return points if points else [raw]
    except Exception as e:
        return [f"Guidance unavailable: {e}"]

def generate_pdf_report(image, plastic_type, confidence, info, guidance_points):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    recyclable_text = "Recyclable" if info["recyclable"] else "Non-recyclable"
    properties_list = info.get("properties", [])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @page {{ size: A4; margin: 10mm; background-color: #fdfbf7; }}
        body {{ font-family: 'Arial', sans-serif; color: #333; font-size: 13px; line-height: 2.5; }}
        .header {{ border-bottom: 1.5px solid #06D6A0; padding-bottom: 4px; margin-bottom: 8px; }}
        .title {{ color: #06D6A0; font-size: 16px; font-weight: bold; }}
        .img-container {{ text-align: center; margin-bottom: 8px; }}
        .img-container img {{ max-width: 250px; height: 200px; border-radius: 6px; border: 2px solid #ddd; }}
        .card {{ background: #ffffff; padding: 8px 10px; border-radius: 6px; border: 1px solid #ddd; margin-bottom: 8px; }}
        .info-box {{ background-color: #e8f5e9; padding: 8px 10px; border-radius: 6px; border-left: 4px solid #06D6A0; margin-bottom: 8px; }}
        h3 {{ font-size: 13px; margin: 0 0 4px 0; color: #1B4332; }}
        p {{ margin: 0 0 3px 0; }}
        ul {{ margin: 0; padding-left: 15px; }}
        li {{ margin-bottom: 2px; }}
    </style>
    </head>
    <body>
        <div class="header">
            <div class="title">♻️ EcoSort - Plastic Recycling Report</div>
            <p style="font-size: 9px; color: #666;">Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="img-container">
            <img src="data:image/png;base64,{img_str}" alt="Scanned Plastic">
        </div>

        <div class="card">
            <h3>Analysis Results & Identified Plastic Details</h3>
            <p><strong>Plastic Type:</strong> {plastic_type} ({info['name_en']}) </br><strong>Resin Code:</strong> #{info['code']} </br><strong>Confidence:</strong> {confidence:.1f}%  </br><strong>Status:</strong> {recyclable_text}</p>
            <p><strong>Description:</strong> {info['description']}</p>
        </div>

        <div class="card">
            <h3>Key Properties & Common Uses</h3>
            <ul>
                {"".join([f"<li>{prop}</li>" for prop in properties_list])}
            </ul>
            <p style="margin-top: 4px;"><strong>Common Uses:</strong> {info['examples']}.</p>
        </div>

        <div class="info-box">
            <h3>Recycling Guidance</h3>
            <ul>
                {"".join([f"<li>{point}</li>" for point in guidance_points])}
            </ul>
        </div>
    </body>
    </html>
    """
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception as e:
        return None

# ==========================================
# LOAD YOLO MODEL
# ==========================================
@st.cache_resource
def load_model():
    return YOLO("best_model_yolov8_ft2.pt")

model = load_model()

# ==========================================
# PAGE VIEWS: WASTE CHART & ABOUT PAGE
# ==========================================
def render_waste_chart():
    th = st.session_state["_theme"]
    st.markdown('<div class="section-title">Global vs. Myanmar Plastic Recycling</div>', unsafe_allow_html=True)

    years = [2000, 2005, 2010, 2015, 2019, 2022, 2023, 2024, 2025]
    global_rate = [5, 7, 9, 11, 13, 9.5, 9.8, 10.2, 10.5]
    myanmar_rate = [3, 3.5, 4, 5, 6, 7, 7.5, 8, 8.5]

    color_global = "#118AB2"
    color_myanmar = "#EF476F"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=global_rate, mode="lines+markers", name="Global",
        line=dict(color=color_global, width=4, shape="spline"),
        marker=dict(size=9, color=color_global),
    ))
    fig.add_trace(go.Scatter(
        x=years, y=myanmar_rate, mode="lines+markers", name="Myanmar (regional estimate)",
        line=dict(color=color_myanmar, width=4, dash="dash", shape="spline"),
        marker=dict(size=9, color=color_myanmar),
    ))
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Nunito, sans-serif", color=th["text"], size=13),
        margin=dict(l=10, r=10, t=10, b=10),
        height=340,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            font=dict(color=th["text"], size=13),
        ),
        xaxis=dict(title=None, gridcolor=th["border"], zeroline=False, tickfont=dict(color=th["text"])),
        yaxis=dict(
            title="Recycling rate (%)", gridcolor=th["border"], zeroline=False, ticksuffix="%",
            tickfont=dict(color=th["text"]), title_font=dict(color=th["text"]),
        ),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("""
    <div class="chart-caption">
        Sources: OECD / Our World in Data (global waste-recycling-rate trend, 2000–2019); 
        global recycled-content share ~9.5% in 2022 (Tsinghua University, 2025).
        2023–2025 values are projections based on current trends.
        Myanmar line reflects OECD regional estimate for lower/middle-income ASEAN countries
        (OECD <i>Regional Plastics Outlook for Southeast and East Asia</i>, 2023).
    </div>
    """, unsafe_allow_html=True)

def render_about_page():
    st.markdown("""
    <div class="eco-header">
        <div class="eco-title">♻ About EcoSort</div>
        <div class="eco-subtitle">AI · Plastic Classifier · Recycling Guide</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="result-card result-card-flex">
        <div class="about-p">
            <b>EcoSort</b> is an AI-powered plastic identification and recycling-guidance tool,
            built as a bachelor's project. It uses a YOLOv8 deep learning model to recognize the
            resin type of a plastic item from a photo (PET, HDPE, LDPE, PP, PS, or Other), then tells
            you whether it's recyclable and how to properly recycle or dispose of it.
        </div>
        <div class="about-p">
            <b>Why this matters:</b> globally, less than 10% of plastic waste is effectively recycled,
            and manual sorting by resin type is one of the biggest bottlenecks in the recycling chain.
            EcoSort explores how computer vision can make correct sorting easier for everyday people.
        </div>
        <div class="about-p">
            <b>Tech stack:</b> YOLOv8 (Ultralytics) for classification, Streamlit for the interface,
            and an LLM (via Groq) for generating plain-language disposal guidance.
        </div>
        <div class="about-p">
            <b>Author:</b> Zin Wut Yee Zaw, UCSPyay, Computer Science Student.<br>
            <b>Contact:</b> wyee659@gmail.com.
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_waste_chart()

# ==========================================
# PAGE VIEW: DASHBOARD
# ==========================================
def render_dashboard_page():
    th = st.session_state["_theme"]
    st.markdown("""
    <div class="eco-header">
        <div class="eco-title">Dashboard</div>
        <div class="eco-subtitle">Global Scan History &amp; Stats</div>
    </div>
    """, unsafe_allow_html=True)

    stats = st.session_state.global_stats
    history = stats.get("history", [])
    total = stats.get("total_scans", 0)
    type_counts = stats.get("plastic_types", {})

    if total == 0:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:4rem; margin-bottom:1rem"></div>
            <div style="font-size:1.1rem; font-weight:500; margin-bottom:0.5rem">No scans yet</div>
            <div style="font-size:0.85rem; opacity:0.7">Classify a plastic item on the Classifier page to see stats here.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    recyclable_count = sum(
        type_counts.get(k, 0) for k, info in RECYCLABILITY.items() if info["recyclable"]
    )
    recyclable_pct = round(recyclable_count / total * 100) if total > 0 else 0
    most_common = max(type_counts, key=type_counts.get) if type_counts else "N/A"
    
    avg_conf = 0
    if history:
        avg_conf = round(sum(h["confidence"] for h in history) / len(history))

    m1, m2, m3, m4 = st.columns(4)
    for col, value, label in [
        (m1, total, "Total Scans"),
        (m2, f"{recyclable_pct}%", "Recyclable"),
        (m3, most_common, "Most Common"),
        (m4, f"{avg_conf}%", "Avg. Confidence"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Scans by Plastic Type</div>', unsafe_allow_html=True)
    bar_fig = go.Figure(go.Bar(
        x=list(type_counts.keys()),
        y=list(type_counts.values()),
        marker_color=[COLORS.get(k, th["accent"]) for k in type_counts.keys()],
        text=list(type_counts.values()),
        textposition="outside",
    ))
    bar_fig.update_layout(
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Nunito, sans-serif", color=th["text"], size=13),
        margin=dict(l=10, r=10, t=20, b=10),
        height=300,
        xaxis=dict(title=None, gridcolor=th["border"], tickfont=dict(color=th["text"])),
        yaxis=dict(title="Count", gridcolor=th["border"], tickfont=dict(color=th["text"]),
                    title_font=dict(color=th["text"])),
        showlegend=False,
    )
    st.plotly_chart(bar_fig, use_container_width=True, config={"displayModeBar": False})

    col_a, col_b = st.columns([1, 1.4], gap="large")
    with col_a:
        st.markdown('<div class="section-title">♻️ Recyclable Split</div>', unsafe_allow_html=True)
        pie_fig = go.Figure(go.Pie(
            labels=["Recyclable", "Non-recyclable"],
            values=[recyclable_count, max(0, total - recyclable_count)],
            hole=0.55,
            marker=dict(colors=["#06D6A0", "#EF476F"]),
            textfont=dict(color="#FFFFFF", size=13),
        ))
        pie_fig.update_layout(
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Nunito, sans-serif", color=th["text"], size=13),
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
            legend=dict(font=dict(color=th["text"])),
        )
        st.plotly_chart(pie_fig, use_container_width=True, config={"displayModeBar": False})

    with col_b:
        st.markdown('<div class="section-title">Recent Scans</div>', unsafe_allow_html=True)
        rows = "".join(
            f"""<div style="display:flex; justify-content:space-between; align-items:center;
                     padding:0.6rem 0; border-bottom:1px solid {th['border']}; font-size:0.85rem;">
                <span>{RESIN_SYMBOLS.get(h['type'], '♹')} <b>{h['type']}</b></span>
                <span style="color:{th['muted']}">{h['confidence']}%</span>
                <span style="color:{th['muted']}">{h['time']}</span>
            </div>"""
            for h in reversed(history[-10:])
        )
        st.markdown(f'<div class="result-card result-card-flex" style="max-height:280px; overflow-y:auto;">{rows}</div>', unsafe_allow_html=True)

    if st.button("🗑️ Clear global stats"):
        st.session_state.global_stats = {"total_scans": 0, "plastic_types": {}, "history": []}
        save_global_stats(st.session_state.global_stats)
        st.session_state.last_file_key = None
        st.rerun()

# ==========================================
# PAGE VIEW: LEARN SECTION (FIXED - IMAGE & CARD ALIGNED)
# ==========================================
def render_learn_page():
    th = st.session_state["_theme"]
    
    st.markdown("""
    <div class="eco-header">
        <div class="eco-title">Learn</div>
        <div class="eco-subtitle">Plastic Types &amp; Recycling Basics</div>
    </div>
    """, unsafe_allow_html=True)

    # ---------- VIDEO SECTION ----------
    # st.markdown('<div class="section-title">🎬 Recycling Example Video</div>', unsafe_allow_html=True)
    # st.video("https://youtu.be/cNPEH0GOhRw?si=tRo2Ova9xcnoMTNz")

    # HTML5 Video Tag 
video_html = """
<video width="100%" controls>
    <source src="https://drive.google.com/uc?export=download&id=1lDlYJQ7ZwCcjRTyHn4-0V-7MnW_7pT7d" type="video/mp4">
    Your browser does not support the video tag.
</video>
"""
st.markdown(video_html, unsafe_allow_html=True)

    # ---------- RECYCLING PROCESS ----------
    st.markdown('<div class="section-title">♻️ How Plastic Recycling Works (Step by Step)</div>', unsafe_allow_html=True)

    # All images same size: 300x200
    step_images = {
        "step1": "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=400&h=300&fit=crop",
        "step2": "https://images.unsplash.com/photo-1611273426858-450e5a3f0f7c?w=400&h=300&fit=crop",
        "step3": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=400&h=300&fit=crop",
        "step4": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=400&h=300&fit=crop",
        "step5": "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=400&h=300&fit=crop",
    }

    # ===== STEP 1 =====
    st.markdown(f"""
    <div style="display:flex; gap:1.5rem; align-items:stretch; margin-bottom:1.5rem; flex-wrap:wrap;">
        <div style="flex:0 0 300px; min-width:200px;">
            <img src="{step_images['step1']}" 
                 style="width:100%; height:auto; border-radius:20px; border:3px solid {th['border']};">
            <div style="text-align:center; margin-top:0.5rem; color:{th['muted']}; font-size:0.8rem;">
                Step 1: Collection
            </div>
        </div>
        <div style="flex:1; min-width:250px; background:{th['card_bg']}; border:3px solid {th['accent']}; border-radius:20px; padding:1.5rem;">
            <div style="font-size:1.2rem; font-weight:700; color:{th['accent']};">Step 1: Collection</div>
            <div style="margin-top:0.8rem; line-height:1.8;">
                <b>What happens:</b> Plastic waste is collected from households, businesses, 
                and recycling drop-off points. This is the first and most important step — 
                without proper collection, recycling can't happen.
            </div>
            <div style="margin-top:1rem; background:{th['bg']}; padding:0.8rem 1.2rem; border-radius:14px; border-left:4px solid {th['accent']};">
                💡 <b>Tip:</b> Separate your plastics by type (bottles, containers, bags) 
                before putting them in the recycling bin.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ===== STEP 2 =====
    st.markdown(f"""
    <div style="display:flex; gap:1.5rem; align-items:stretch; margin-bottom:1.5rem; flex-wrap:wrap;">
        <div style="flex:0 0 300px; min-width:200px;">
            <img src="{step_images['step2']}" 
                 style="width:100%; height:auto; border-radius:20px; border:3px solid {th['border']};">
            <div style="text-align:center; margin-top:0.5rem; color:{th['muted']}; font-size:0.8rem;">
                Step 2: Sorting
            </div>
        </div>
        <div style="flex:1; min-width:250px; background:{th['card_bg']}; border:3px solid {th['accent']}; border-radius:20px; padding:1.5rem;">
            <div style="font-size:1.2rem; font-weight:700; color:{th['accent']};">Step 2: Sorting</div>
            <div style="margin-top:0.8rem; line-height:1.8;">
                <b>What happens:</b> Plastics are sorted by resin type (PET, HDPE, PP, etc.) 
                using advanced optical sorters and manual labor. Different types can't be 
                recycled together.
            </div>
            <div style="margin-top:1rem; background:{th['bg']}; padding:0.8rem 1.2rem; border-radius:14px; border-left:4px solid {th['accent']};">
                💡 <b>Tip:</b> Check the resin code (♳-♹) on the bottom of your plastic 
                items — this is how they're sorted!
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ===== STEP 3 =====
    st.markdown(f"""
    <div style="display:flex; gap:1.5rem; align-items:stretch; margin-bottom:1.5rem; flex-wrap:wrap;">
        <div style="flex:0 0 300px; min-width:200px;">
            <img src="{step_images['step3']}" 
                 style="width:100%; height:auto; border-radius:20px; border:3px solid {th['border']};">
            <div style="text-align:center; margin-top:0.5rem; color:{th['muted']}; font-size:0.8rem;">
                Step 3: Cleaning
            </div>
        </div>
        <div style="flex:1; min-width:250px; background:{th['card_bg']}; border:3px solid {th['accent']}; border-radius:20px; padding:1.5rem;">
            <div style="font-size:1.2rem; font-weight:700; color:{th['accent']};">Step 3: Cleaning</div>
            <div style="margin-top:0.8rem; line-height:1.8;">
                <b>What happens:</b> Plastics are washed to remove labels, glue, food residue, 
                and dirt. This is critical — contaminated plastics can ruin an entire batch.
            </div>
            <div style="margin-top:1rem; background:{th['bg']}; padding:0.8rem 1.2rem; border-radius:14px; border-left:4px solid {th['accent']};">
                💡 <b>Tip:</b> Rinse your plastic items before recycling! A quick rinse 
                makes a huge difference at the cleaning facility.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ===== STEP 4 =====
    st.markdown(f"""
    <div style="display:flex; gap:1.5rem; align-items:stretch; margin-bottom:1.5rem; flex-wrap:wrap;">
        <div style="flex:0 0 300px; min-width:200px;">
            <img src="{step_images['step4']}" 
                 style="width:100%; height:auto; border-radius:20px; border:3px solid {th['border']};">
            <div style="text-align:center; margin-top:0.5rem; color:{th['muted']}; font-size:0.8rem;">
                ⚙️ Step 4: Shredding
            </div>
        </div>
        <div style="flex:1; min-width:250px; background:{th['card_bg']}; border:3px solid {th['accent']}; border-radius:20px; padding:1.5rem;">
            <div style="font-size:1.2rem; font-weight:700; color:{th['accent']};">Step 4: Shredding</div>
            <div style="margin-top:0.8rem; line-height:1.8;">
                <b>What happens:</b> Clean plastic is shredded into small flakes or pellets. 
                This increases the surface area and makes it easier to melt and reform.
            </div>
            <div style="margin-top:1rem; background:{th['bg']}; padding:0.8rem 1.2rem; border-radius:14px; border-left:4px solid {th['accent']};">
                💡 <b>Tip:</b> Shredded plastic flakes are the raw material for making 
                new plastic products — from bottles to clothing!
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ===== STEP 5 =====
    st.markdown(f"""
    <div style="display:flex; gap:1.5rem; align-items:stretch; margin-bottom:1.5rem; flex-wrap:wrap;">
        <div style="flex:0 0 300px; min-width:200px;">
            <img src="{step_images['step5']}" 
                 style="width:100%; height:auto; border-radius:20px; border:3px solid {th['border']};">
            <div style="text-align:center; margin-top:0.5rem; color:{th['muted']}; font-size:0.8rem;">
                ♻️ Step 5: Pelletizing
            </div>
        </div>
        <div style="flex:1; min-width:250px; background:{th['card_bg']}; border:3px solid {th['accent']}; border-radius:20px; padding:1.5rem;">
            <div style="font-size:1.2rem; font-weight:700; color:{th['accent']};">Step 5: Pelletizing</div>
            <div style="margin-top:0.8rem; line-height:1.8;">
                <b>What happens:</b> Shredded plastic is melted and formed into small pellets 
                (nurdles). These pellets are then sold to manufacturers to make new plastic 
                products — closing the recycling loop!
            </div>
            <div style="margin-top:1rem; background:{th['bg']}; padding:0.8rem 1.2rem; border-radius:14px; border-left:4px solid {th['accent']};">
                💡 <b>Tip:</b> Look for products made from recycled plastic (often labeled 
                "Post-Consumer Recycled" or "PCR") to support the circular economy.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<hr style="border-color:{th["border"]}; margin:2rem 0;">', unsafe_allow_html=True)

    # ---------- RESIN TYPES SECTION (Original) ----------
    st.markdown('<div class="section-title">The Resin Types</div>', unsafe_allow_html=True)

    for cls, info in RECYCLABILITY.items():
        sym = RESIN_SYMBOLS.get(cls, "♹")
        color = COLORS.get(cls, "#5C8374")
        badge = (
            '<span class="badge-recyclable">✓ Recyclable</span>'
            if info["recyclable"]
            else '<span class="badge-non">✗ Non-recyclable</span>'
        )
        with st.expander(f"{sym}  #{info['code']} · {cls} — {info['name_en']}"):
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.8rem; flex-wrap:wrap;">
                <div style="font-size:2.5rem; color:{color}">{sym}</div>
                {badge}
            </div>
            <div class="examples-text" style="margin-bottom:0.6rem;">📦 <b>Common items:</b> {info['examples']}</div>
            <div class="guidance-box">💡 {LEARN_TIPS.get(cls, "")}</div>
            """, unsafe_allow_html=True)

    # ---------- GENERAL TIPS ----------
    st.markdown('<div class="section-title">🌱 General Tips</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="result-card result-card-flex">
        <div class="about-p">
            <b>1. Reduce first.</b> The most effective plastic is the one never produced — reusable
            bottles, bags, and containers beat recycling every time.
        </div>
        <div class="about-p">
            <b>2. Rinse before you bin it.</b> Food or liquid residue can contaminate an entire batch
            of recyclables at the sorting facility, sending otherwise-recyclable material to landfill.
        </div>
        <div class="about-p">
            <b>3. Don't "wishcycle."</b> Tossing non-recyclable items into recycling bins hoping
            they'll somehow get sorted usually does more harm than good — when in doubt, check your
            local program's accepted materials list.
        </div>
        <div class="about-p">
            <b>4. Know your local rules.</b> What's accepted varies a lot by city and country —
            use the Classifier page here as a starting point, but always double-check against your
            local waste authority's guidelines.
        </div>
    </div>
    """, unsafe_allow_html=True)
# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown('<div class="sidebar-logo">♻ EcoSort</div>', unsafe_allow_html=True)
    st.markdown("---")

    _pages = [
        ("Classifier", "", "Classifier"),
        ("Dashboard", "", "Dashboard"),
        ("Learn", "", "Learn"),
        ("About", "", "About Us"),
    ]
    _nav_placeholders = []
    _clicked_key = None
    for _key, _icon, _label in _pages:
        _ph = st.empty()
        _nav_placeholders.append((_ph, _key))
        if st.button(
            f"{_icon}  {_label}",
            key=f"navbtn_{_key}",
            use_container_width=True,
        ):
            _clicked_key = _key

    if _clicked_key is not None:
        st.session_state.page = _clicked_key

    for _ph, _key in _nav_placeholders:
        if st.session_state.page == _key:
            _ph.markdown('<div class="nav-active-marker"></div>', unsafe_allow_html=True)

    st.markdown("---")
    dark = st.toggle("🌙 Dark mode", value=st.session_state.dark_mode)
    if dark != st.session_state.dark_mode:
        st.session_state.dark_mode = dark
        st.rerun()

# ==========================================
# PAGE ROUTING CONTROLLER
# ==========================================
if st.session_state.page == "About":
    render_about_page()
    st.stop()

if st.session_state.page == "Dashboard":
    render_dashboard_page()
    st.stop()

if st.session_state.page == "Learn":
    render_learn_page()
    st.stop()

# ==========================================
# MAIN PAGE VIEW: CLASSIFIER
# ==========================================
st.markdown("""
<div class="eco-header">
    <div class="eco-title">♻ EcoSort</div>
    <div class="eco-subtitle">AI · Plastic Classifier · Recycling Guide</div>
</div>
""", unsafe_allow_html=True)

with st.expander("Supported Classes & How to Use", expanded=False):
    chip_html = "".join(
        f'<span class="class-chip">{RESIN_SYMBOLS.get(cls, "♹")} {cls}</span>'
        for cls in RECYCLABILITY.keys()
    )
    st.markdown(f'<div style="margin-bottom:0.8rem;">{chip_html}</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-info" style="margin-top:0;">
        <b>How to use:</b><br>
        1. Upload a plastic item photo<br>
        2. Get instant AI classification<br>
        3. Follow recycling guidance<br><br>
        <b>Tips for best results:</b><br>
        • Clear, well-lit photos<br>
        • Show the recycling symbol if visible<br>
        • Single item per photo
    </div>
    """, unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload a photo of plastic waste",
    type=["jpg", "jpeg", "png"],
    help="Clear photos work best. Try to capture the recycling symbol if visible."
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.image(image, caption="📷 Uploaded Image", use_container_width=False)

    with st.spinner("🔍 Analyzing..."):
        results = model(image)

    r = results[0]
    probs = r.probs
    top1_idx = probs.top1
    top1_cls = model.names[top1_idx]
    top1_conf = float(probs.top1conf)

    info = RECYCLABILITY.get(top1_cls, RECYCLABILITY["Others"])
    symbol = RESIN_SYMBOLS.get(top1_cls, "♹")
    color = COLORS.get(top1_cls, "#5C8374")
    conf_pct = int(top1_conf * 100)

    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.last_file_key != file_key:
        stats = st.session_state.global_stats
        stats["total_scans"] += 1
        stats["plastic_types"][top1_cls] = stats["plastic_types"].get(top1_cls, 0) + 1
        
        if "history" not in stats:
            stats["history"] = []
            
        stats["history"].append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "type": top1_cls,
            "confidence": conf_pct,
            "recyclable": info["recyclable"],
        })
        save_global_stats(stats)
        st.session_state.last_file_key = file_key

    with col2:
        badge = (
            '<span class="badge-recyclable">✓ Recyclable</span>'
            if info["recyclable"]
            else '<span class="badge-non">✗ Non-recyclable</span>'
        )
        st.markdown(f"""
        <div class="result-card">
            <div style="display:flex; align-items:center; gap:1.5rem; flex-wrap:wrap;">
                <div style="font-size:3.5rem; color:{color}">{symbol}</div>
                <div>
                    <div style="font-family:'Baloo 2',sans-serif; font-size:3rem; font-weight:800; color:{color}; line-height:1">#{info['code']}</div>
                    <div class="plastic-name">{top1_cls}</div>
                    <div class="plastic-fullname">{info['name_en']}</div>
                    {badge}
                </div>
            </div>
            <div class="conf-label">Confidence Level</div>
            <div style="display:flex; align-items:center; gap:1rem;">
                <div class="conf-bar-bg" style="flex:1">
                    <div style="height:10px; width:{conf_pct}%; background:linear-gradient(90deg,{color},{color}99); border-radius:8px;"></div>
                </div>
                <div style="font-weight:800; color:{color}; min-width:48px; font-size:1rem">{conf_pct}%</div>
            </div>
            <div class="examples-text">📦 Common items: {info['examples']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Identified Plastic Details</div>', unsafe_allow_html=True)
    
    props_md = "".join(f"- {prop}\n" for prop in info.get("properties", []))
    
    st.markdown(f"""
    <div style="margin: 1rem 0; line-height: 1.8;">
        <b>{top1_cls} ({info['name_en']})</b> — {info['description']} Identified by recycling number #{info['code']}.
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**Key Properties**")
    st.markdown(props_md)

    st.markdown(f"**📦 Common Uses**")
    st.markdown(f"<div class='examples-text' style='margin-bottom:1rem;'>{info['examples']}.</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">♻️ Recycling Guidance</div>', unsafe_allow_html=True)
    with st.spinner("Getting guidance..."):
        guidance_points = get_guidance(top1_cls, info["recyclable"])
    guidance_html = "".join(f"<li>{point}</li>" for point in guidance_points)
    st.markdown(
        f'<div class="guidance-box"><ul class="guidance-list">{guidance_html}</ul></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.subheader("Export Report")
    
    pdf_data = generate_pdf_report(image, top1_cls, float(top1_conf * 100), info, guidance_points)
    
    if pdf_data:
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_data,
            file_name=f"EcoSort_Report_{top1_cls}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.error("Failed to generate PDF. WeasyPrint dependencies might be missing.")

else:
    st.markdown("""
    <div class="empty-state">
        <div style="font-size:4rem; margin-bottom:1rem">📷</div>
        <div style="font-size:1.1rem; font-weight:500; margin-bottom:0.5rem">Upload a plastic item photo to get started</div>
        <div style="font-size:0.85rem; opacity:0.7">Supports JPG, JPEG, PNG · AI-powered classification</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)
render_waste_chart()
