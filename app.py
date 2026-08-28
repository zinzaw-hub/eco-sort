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
if "lang" not in st.session_state:
    st.session_state.lang = "en"

is_mm = (st.session_state.lang == "mm")

st.set_page_config(
    page_title="EcoSort" if is_mm else "EcoSort",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Use absolute path for global_stats.json to guarantee data persistence across restarts
STATS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "global_stats.json")

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
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
    except Exception as e:
        st.error(f"Error saving stats: {e}")

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
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Nunito:wght@300;400;600;700&family=Pyidaungsu:wght@400;600;700&display=swap');

    .stApp {{
        background-color: {bg} !important;
        font-family: 'Pyidaungsu', 'Nunito', sans-serif;
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
        font-family: 'Baloo 2', 'Pyidaungsu', sans-serif;
        font-size: 3.2rem;
        font-weight: 800;
        color: {accent} !important;
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1.1;
    }}
    .eco-subtitle {{
        font-size: 0.9rem;
        color: {muted} !important;
        margin-top: 0.4rem;
        font-weight: 600;
        letter-spacing: 1px;
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
        font-size: 0.85rem;
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
        font-size: 0.8rem;
        color: {muted} !important;
        letter-spacing: 1px;
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
        font-size: 0.95rem;
        color: {muted} !important;
        margin-top: 0.5rem;
    }}
    .guidance-box {{
        background: {accent}20;
        border-left: 4px solid {accent};
        border-radius: 0 16px 16px 0;
        padding: 1rem 1.5rem;
        margin-top: 0.5rem;
        font-size: 0.95rem;
        color: {text} !important;
        line-height: 1.8;
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
        font-family: 'Baloo 2', 'Pyidaungsu', sans-serif;
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
        font-family: 'Baloo 2', 'Pyidaungsu', sans-serif;
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
        font-size: 0.85rem;
        color: {muted} !important;
        line-height: 1.8;
    }}
    .class-chip {{
        display: inline-block;
        background: {accent}22;
        border: 1px solid {accent}55;
        border-radius: 20px;
        padding: 0.25rem 0.8rem;
        font-size: 0.8rem;
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
        font-size: 0.78rem;
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
        font-family: 'Baloo 2', 'Pyidaungsu', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: {accent} !important;
        line-height: 1.1;
    }}
    .metric-label {{
        font-size: 0.8rem;
        color: {muted} !important;
        letter-spacing: 0.5px;
        font-weight: 700;
        margin-top: 0.3rem;
    }}
    /* SECONDARY SIDEBAR BUTTONS */
    [data-testid="stSidebar"] button[kind="secondary"] {{
        background: {card_bg} !important;
        color: {text} !important;
        border: 2px solid {border} !important;
        border-radius: 14px !important;
        justify-content: center !important;
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
    /* PRIMARY SIDEBAR BUTTONS - Styled in soft accent green (#06D6A0) */
    [data-testid="stSidebar"] button[kind="primary"] {{
        background: {accent} !important;
        color: #FFFFFF !important;
        border: 2px solid {accent} !important;
        border-radius: 14px !important;
        justify-content: center !important;
        padding: 0.65rem 1rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
        box-shadow: 0 4px 12px {accent}44 !important;
    }}
    [data-testid="stSidebar"] button[kind="primary"] p,
    [data-testid="stSidebar"] button[kind="primary"] span {{
        color: #FFFFFF !important;
    }}
    [data-testid="stSidebar"] button[kind="primary"]:hover {{
        background: {accent} !important;
        color: #FFFFFF !important;
        opacity: 0.92;
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

    /* ========================================== */
    /* LEARN PAGE QUIZ BUTTON OVERRIDE           */
    /* Force primary buttons to use accent color  */
    /* ========================================== */
    .stApp .element-container button[kind="primary"] {{
        background: {accent} !important;
        color: #FFFFFF !important;
        border: 2px solid {accent} !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px {accent}44 !important;
        transition: all 0.15s ease !important;
    }}
    .stApp .element-container button[kind="primary"] p,
    .stApp .element-container button[kind="primary"] span {{
        color: #FFFFFF !important;
    }}
    .stApp .element-container button[kind="primary"]:hover {{
        background: {accent} !important;
        color: #FFFFFF !important;
        opacity: 0.92;
        box-shadow: 0 4px 16px {accent}66 !important;
    }}

    /* Keep sidebar primary buttons as they are */
    [data-testid="stSidebar"] .element-container button[kind="primary"] {{
        background: {accent} !important;
        color: #FFFFFF !important;
        border: 2px solid {accent} !important;
        border-radius: 14px !important;
        justify-content: center !important;
        padding: 0.65rem 1rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
        box-shadow: 0 4px 12px {accent}44 !important;
    }}
    [data-testid="stSidebar"] .element-container button[kind="primary"] p,
    [data-testid="stSidebar"] .element-container button[kind="primary"] span {{
        color: #FFFFFF !important;
    }}
    [data-testid="stSidebar"] .element-container button[kind="primary"]:hover {{
        background: {accent} !important;
        color: #FFFFFF !important;
        opacity: 0.92;
    }}

    /* Previous button styling */
    .stApp .element-container button[kind="secondary"] {{
        background: transparent !important;
        color: {text} !important;
        border: 2px solid {border} !important;
        border-radius: 14px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }}
    .stApp .element-container button[kind="secondary"]:hover {{
        background: {accent}22 !important;
        border-color: {accent} !important;
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

RECYCLABILITY_EN = {
    "PET": {
        "recyclable": True, "code": "1", "name_en": "Polyethylene Terephthalate", 
        "examples": "Water bottles, soda bottles, food jars, Cooking oil containers, fruit and food containers.",
        "description": "PET (Polyethylene Terephthalate) is a clear, strong, and lightweight plastic widely used for packaging foods and beverages because it helps prevent oxygen from spoiling the product inside.PET is identified by Resin Identification Code (RIC) #1, and the code system was originally established by the Society of the Plastics Industry (SPI).",
        "properties": [
            "Clear and transparent — high optical clarity",
            "Strong and shatter-resistant — handles impact well",
            "Good gas and moisture barrier — preserves freshness",
            "100% recyclable — highly demanded by recycling facilities"
        ]
    },
    "HDPE": {
        "recyclable": True, "code": "2", "name_en": "High-Density Polyethylene", 
        "examples": "Recycle bins, Milk jugs, detergent bottles, shampoo bottles, cutting boards ",
        "description": "HDPE (High-Density Polyethylene) is a robust, stiff plastic known for its high tensile strength and resistance to various solvents, making it ideal for rigid containers.HDPE is identified by Resin Identification Code (RIC) #2, and the code system was originally established by the Society of the Plastics Industry (SPI).",
        "properties": [
            "Rigid and strong — withstands heavy stacking",
            "Chemical resistant — handles household cleaners safely",
            "Weather resistant — durable against environmental exposure",
            "Widely recyclable — accepted in almost all curbside programs"
        ]
    },
    "LDPE": {
        "recyclable": True, "code": "4", "name_en": "Low-Density Polyethylene", 
        "examples": "Bread bags, squeeze bottles, shrink wrap, cling wrap, food wrapping film, plastic shopping bags",
        "description": "LDPE (Low-Density Polyethylene) is a flexible, soft plastic with good chemical resistance. It is less rigid than HDPE and commonly used for films and flexible packaging. LDPE (Low-Density Polyethylene) is identified by Resin Identification Code (RIC) #4, and the code system was originally established by the Society of the Plastics Industry (SPI).",
        "properties": [
            "Flexible and soft — bends without breaking",
            "Lightweight — adds minimal weight to packaging",
            "Moisture resistant — keeps contents dry",
            "Partially recyclable — accepted at some drop-off points"
        ]
    },
    "PP": {
        "recyclable": True, "code": "5", "name_en": "Polypropylene", 
        "examples": "Yogurt tubs, straws, bottle caps, takeout containers, food storage containers (microwave-safe food containers), plastic baskets and bowls, drinking cups, and plastic plates.",
        "description": "PP (Polypropylene) is a tough, heat-resistant plastic that acts as a strong barrier against moisture, grease, and chemicals, making it great for hot-fill liquids and food storage.PP is identified by Resin Identification Code (RIC) #5, and the code system was originally established by the Society of the Plastics Industry (SPI).",
        "properties": [
            "High heat tolerance — safe for microwave and hot liquids",
            "Tough and fatigue resistant — handles repeated flexing",
            "Moisture and grease barrier — excellent for food packaging",
            "Recyclable — increasingly accepted by local programs"
        ]
    },
    "PS": {
        "recyclable": False, "code": "6", "name_en": "Polystyrene", 
        "examples": "Foam cups, takeout clamshells, packing peanuts, rigid disposable spoons used at parties and in shops, rigid and transparent CD cases, and brittle clear cups used for drinking juice or cold water,",
        "description": "PS (Polystyrene) can be rigid or foamed (Styrofoam). It is lightweight and provides great insulation, but it is fragile and notoriously difficult to recycle economically.PS is identified by Resin Identification Code (RIC) #6, and the code system was originally established by the Society of the Plastics Industry (SPI).",
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
        "description": "Others (Category 7) includes any plastic that does not fit into categories 1 through 6, often consisting of multi-layered combinations or polycarbonate plastics.Other Plastics are identified by Resin Identification Code (RIC) #7 and include plastic types that do not fall under codes #1–#6.",
        "properties": [
            "Mixed composition — often made of bonded layers",
            "Customizable strength and durability",
            "Hard to separate into base components",
            "Non-recyclable — goes to general landfill or specialized processing"
        ]
    },
}

RECYCLABILITY_MM = {
    "PET": {
        "recyclable": True, "code": "1", "name_en": "Polyethylene Terephthalate (ပေါလီအက်သလင်း တာရက်သလိတ်)", 
        "examples": "ရေသန့်ဗူး၊ Coca Cola, Max Plus, Speed, Royal D ကဲ့သို့သော အအေးဗူးများ၊ စားသုံးဆီဗူးများ၊ သစ်သီးနှင့် အစားအစာထည့်ဗူးများ။",
        "description": "PET (Polyethylene Terephthalate) သည် ကြည်လင်၊ ခိုင်မာပြီး ပေါ့ပါးသော ပလတ်စတစ်ဖြစ်ပြီး အောက်ဆီဂျင်ကြောင့် အစားအသောက်များ ပျက်စီးခြင်းမှ ကာကွယ်ပေးသဖြင့် အစားအသောက်နှင့် သောက်ရေသန့် ထုပ်ပိုးရာတွင် အများဆုံး အသုံးပြုကြသည်။ PET သည် Resin Identification Code (RIC) နံပါတ် #1 ဖြင့် သတ်မှတ်ထားပြီး၊ အဆိုပါ code စနစ်ကို Society of the Plastics Industry (SPI) မှ မူလအစပြုကာ သတ်မှတ်ခဲ့ပါသည်။",
        "properties": [
            "ကြည်လင်ပြတ်သားခြင်း — အလင်းပေါက်မှု မြင့်မားခြင်း",
            "ခိုင်ခံ့ပြီး ရိုက်ခတ်ဒဏ် ခံနိုင်ခြင်း — ရိုက်ခတ်မှုများကို ကောင်းစွာ တောင့်ခံနိုင်ခြင်း",
            "လေနှင့် စိုထိုင်းဆကို ကောင်းစွာ ကာကွယ်ပေးနိုင်ခြင်း — လတ်ဆတ်မှုကို ထိန်းသိမ်းပေးခြင်း",
            "၁၀၀% ပြန်လည်အသုံးပြုနိုင်ခြင်း — ပြန်လည်အသုံးပြုရေး စက်ရုံများမှ အလိုရှိဆုံး ပလတ်စတစ်ဖြစ်ခြင်း"
        ]
    },
    "HDPE": {
        "recyclable": True, "code": "2", "name_en": "High-Density Polyethylene (သိပ်သည်းဆမြင့် ပေါလီအက်သလင်း)", 
        "examples": "အမှိုက်ခွဲခြားစွန့်ပစ်နိုင်သည့် အမှိုက်ပုံးများ၊ နို့ဗူး၊ ဆပ်ပြာဆီဗူး၊ ခေါင်းလျှော်ရည်ဗူးများ၊ အစွန်းချွတ်ဆေးဗူးများ၊ ရေချိုးခန်းသုံး ဆပ်ပြာရည်ဗူးများ၊ ဟင်းသီးဟင်းရွက်နှင့် အစားအစာတင်ကာလှီးဖြတ်သည့် ကော်ပြားများ၊ ကလေးကစားစရာ ပလတ်စတစ် အရုပ်များ၊  ",
        "description": "HDPE (High-Density Polyethylene) သည် မာကျောခိုင်မာပြီး ပျော်ရည်အမျိုးမျိုးကို ခံနိုင်ရည်ရှိသော ပလတ်စတစ်ဖြစ်သဖြင့် ခိုင်ခံ့သော ဗူးများနှင့် ကွန်တိန်းနားများ ပြုလုပ်ရာတွင် သင့်တော်သည်။ Resin Identification Code (RIC) နံပါတ် #2 ဖြင့် သတ်မှတ်ထားပြီး၊ အဆိုပါ code စနစ်ကို Society of the Plastics Industry (SPI) မှ မူလအစပြုကာ သတ်မှတ်ခဲ့ပါသည်။",
        "properties": [
            "မာကျောခိုင်ခံ့ခြင်း — လေးလံသော ပစ္စည်းများ ဆင့်စီရာတွင် ခံနိုင်ရည်ရှိခြင်း",
            "ဓာတုဗေဒဆေးဝါးများ ခံနိုင်ခြင်း — အိမ်သုံးသန့်ရှင်းရေး ဆေးဝါးများကို ဘေးကင်းစွာ ထည့်သွင်းနိုင်ခြင်း",
            "ရာသီဥတုဒဏ် ခံနိုင်ခြင်း — ပတ်ဝန်းကျင်ဒဏ်ကို တောင့်ခံနိုင်ခြင်း",
            "ကျယ်ပြန့်စွာ ပြန်လည်အသုံးပြုနိုင်ခြင်း — ပြန်လည်သိမ်းဆည်းရေး အစီအစဉ်တော်တော်များများတွင် လက်ခံခြင်း"
        ]
    },
    "LDPE": {
        "recyclable": True, "code": "4", "name_en": "Low-Density Polyethylene (သိပ်သည်းဆနည်း ပေါလီအက်သလင်း)", 
        "examples": "ပေါင်မုန့်အိတ်၊ ညှစ်ထုတ်ရသော ဗူးများ၊ စားသောက်ဆိုင်တွင်ထားလေ့ရှိသော အချဥ်ရည်ဗူးများ၊ ပလတ်စတစ်အိတ်များ၊ ဈေးဝယ်အိတ်များ၊ အစားအစာပတ်သည့် ပလတ်စတစ် ",
        "description": "LDPE (Low-Density Polyethylene) သည် ပျော့ပျောင်း ကွေးညွှတ်နိုင်ပြီး ဓာတုဗေဒဒဏ် ခံနိုင်သော ပလတ်စတစ်ဖြစ်သည်။ HDPE ထက် မာကျောမှုနည်းပါးပြီး အိတ်များနှင့် ပျော့ပျောင်းသော ထုပ်ပိုးမှုများတွင် အသုံးပြုသည်။ LDPE (Low-Density Polyethylene) သည် Resin Identification Code (RIC) နံပါတ် #4 ဖြင့် သတ်မှတ်ထားပြီး၊ အဆိုပါ code စနစ်ကို Society of the Plastics Industry (SPI) မှ မူလအစပြုကာ သတ်မှတ်ခဲ့ပါသည်။",
        "properties": [
            "ပျော့ပျောင်းကွေးညွှတ်နိုင်ခြင်း — မကျိုးပဲ့ဘဲ ကွေးညွှတ်နိုင်ခြင်း",
            "ပေါ့ပါးခြင်း — ထုပ်ပိုးမှု အလေးချိန်ကို နည်းပါးစေခြင်း",
            "စိုထိုင်းဆ ခံနိုင်ခြင်း — အတွင်းပစ္စည်းများကို ခြောက်သွေ့စေခြင်း",
            "အစိတ်အပိုင်းလိုက် ပြန်လည်အသုံးပြုနိုင်ခြင်း — အချို့သော ပြန်လည်သိမ်းဆည်းရေး စခန်းများတွင် လက်ခံခြင်း"
        ]
    },
    "PP": {
        "recyclable": True, "code": "5", "name_en": "Polypropylene (ပေါလီပရိုပလင်း)", 
        "examples": "ဒိန်ချဉ်ခွက်၊ အချိုရည်သောက်သည့် ပိုက်များ၊ ဗူးအဖုံးများ၊ အဆာပြေ အစားအသောက်ထည့် ဗူးများ၊ အစားအစာသိမ်းဆည်းသည့်ဗူးများ (Microwave ထဲထည့်၍ရသော အစားအစာဘူးများ)၊ ပလပ်စတစ်ခြင်းတောင်းနှင့် ဇလုံများ၊ ခိုင်ခံ့သောအင်္ကျီချိတ်အချို့၊ ရေသောက်ခွက်နှင့် ပလတ်စတစ် ပန်းကန်များ",
        "description": "PP (Polypropylene) သည် အပူဒဏ်ခံနိုင်ပြီး ခိုင်မာသော ပလတ်စတစ်ဖြစ်ကာ စိုထိုင်းဆ၊ ဆီနှင့် ဓာတုဗေဒပစ္စည်းများကို တားဆီးပေးနိုင်သဖြင့် အပူဖြည့် သောက်စရာများနှင့် အစားအသောက် သိုလှောင်ရန် သင့်တော်သည်။ Resin Identification Code (RIC) နံပါတ် #5 ဖြင့် သတ်မှတ်ထားပြီး၊ အဆိုပါ code စနစ်ကို Society of the Plastics Industry (SPI) မှ မူလအစပြုကာ သတ်မှတ်ခဲ့ပါသည်။",
        "properties": [
            "အပူဒဏ်ခံနိုင်မှု မြင့်မားခြင်း — မိုက်ခရိုဝေ့ဖ်နှင့် အပူချိန်မြင့် အရည်များအတွက် ဘေးကင်းခြင်း",
            "ခိုင်ခံ့ပြီး ကွေးညွှတ်ဒဏ် ခံနိုင်ခြင်း — ထပ်ခါထပ်ခါ မကြာခဏ အသုံးပြုနိုင်ခြင်း",
            "စိုထိုင်းဆနှင့် ဆီဒဏ် ကာကွယ်ပေးခြင်း — အစားအသောက် ထုပ်ပိုးမှုအတွက် အထူးကောင်းမွန်ခြင်း",
            "ပြန်လည်အသုံးပြုနိုင်ခြင်း — ဒေသတွင်း အစီအစဉ်များတွင် တိုးမြှင့်လက်ခံလာခြင်း"
        ]
    },
    "PS": {
        "recyclable": False, "code": "6", "name_en": "Polystyrene (ပေါလီစတိုရင်း)", 
        "examples": "ဖော့ခွက်များ၊ အစားအသောက်ထည့် ဖော့ဗူးများ၊ ပါတီပွဲနှင့် ဆိုင်များတွင်သုံးသော မာကြောသည့် တစ်ခါသုံးဇွန်းများ၊ စီဒီခွေထည့်သည့် မာကျောပြီး ဖောက်ထွင်းမြင်ရသော ကာဗာဘူးများ၊ ဖျော်ရည် သို့မဟုတ် ရေအေးသောက်ရန်သုံးသော ကြွပ်ဆတ်သည့် ခွက်အကြည်များ၊ ",
        "description": "PS (Polystyrene) ကို မာကျောသော ပုံစံ သို့မဟုတ် ဖော့ပုံစံ (Styrofoam) ဖြင့် တွေ့ရသည်။ ပေါ့ပါးပြီး အပူချိန် ထိန်းသိမ်းမှု ကောင်းသော်လည်း ကျိုးပဲ့လွယ်ပြီး စီးပွားရေးအရ ပြန်လည်အသုံးပြုရန် ခက်ခဲသည်။ PS (Polystyrene) သည် Resin Identification Code (RIC) နံပါတ် #6 ဖြင့် သတ်မှတ်ထားပြီး၊ အဆိုပါ code စနစ်ကို Society of the Plastics Industry (SPI) မှ မူလအစပြုကာ သတ်မှတ်ခဲ့ပါသည်။",
        "properties": [
            "ပေါ့ပါးပြီး အပူချိန်ထိန်းနိုင်ခြင်း — အပူချိန်ကို တည်ငြိမ်စေခြင်း",
            "ဈေးသက်သာသော ထုပ်ပိုးမှုများအတွက် အမျိုးမျိုး အသုံးပြုနိုင်ခြင်း",
            "ကြွပ်ဆတ်ပြီး ကျိုးပဲ့လွယ်ခြင်း — လွယ်ကူစွာ ကွဲရှပဲ့နိုင်ခြင်း",
            "ပုံမှန်အားဖြင့် ပြန်လည်အသုံးပြု၍ မရခြင်း — သာမန် အမှိုက်ပုံးများတွင် လက်ခံလေ့မရှိခြင်း"
        ]
    },
    "Others": {
        "recyclable": False, "code": "7", "name_en": "Other / Mixed Plastics (အခြား / ရောနှော ပလတ်စတစ်များ)", 
        "examples": "အလွှာပေါင်းစုံ ထုပ်ပိုးမှုများ၊ ဇီဝပလတ်စတစ် အချို့",
        "description": "Others (အမျိုးအစား ၇) တွင် အမျိုးအစား ၁ မှ ၆ အတွင်း မပါဝင်သော ပလတ်စတစ်များ ပါဝင်ပြီး အလွှာပေါင်းစုံ ရောနှောထားသော သို့မဟုတ် ပေါလီကာဗိုနိတ် ပလတ်စတစ်များ ဖြစ်လေ့ရှိသည်။ Other Plastics သည် PET, HDPE, PVC, LDPE, PP နှင့် PS တို့မှ မပါဝင်သော အခြားပလတ်စတစ်အမျိုးအစားများကို Resin Identification Code (RIC) နံပါတ် #7 ဖြင့် သတ်မှတ်ထားခြင်းဖြစ်သည်။",
        "properties": [
            "ရောနှောပါဝင်မှု — အလွှာပေါင်းစုံ ပေါင်းစပ်ပြုလုပ်ထားခြင်း",
            "ခိုင်ခံ့မှုနှင့် ရေရှည်ခံမှု အမျိုးမျိုး ပြုလုပ်နိုင်ခြင်း",
            "မူလ ပါဝင်ပစ္စည်းများအဖြစ် သီးခြားခွဲထုတ်ရန် ခက်ခဲခြင်း",
            "ပြန်လည်အသုံးပြု၍ မရခြင်း — အထွေထွေ အမှိုက်စွန့်ပစ်ရာသို့ စွန့်ပစ်ရခြင်း"
        ]
    },
}

RECYCLABILITY = RECYCLABILITY_MM if is_mm else RECYCLABILITY_EN

COLORS = {
    "PET": "#EF476F", "HDPE": "#06D6A0", "LDPE": "#FFD166",
    "PP": "#118AB2", "PS": "#7209B7", "Others": "#FF6B35",
}

LEARN_TIPS_EN = {
    "PET": "Empty and rinse the bottle, leave the cap on (most facilities now recycle caps too), and flatten it to save space. Avoid tossing in food-contaminated PET like oily takeout containers without rinsing first.",
    "HDPE": "Rinse out any residue (milk, detergent, shampoo), remove pumps/spray tops if possible, and recycle with the cap on. HDPE is one of the most widely and easily recycled plastics.",
    "LDPE": "Bags, wraps, and film plastic usually can't go in regular household recycling bins — check for a store drop-off point (many supermarkets collect plastic bags separately). Rigid LDPE items can often go in standard recycling.",
    "PP": "Rinse thoroughly, especially food containers and yogurt tubs. PP is recyclable but is accepted less often than PET/HDPE, so check your local program before assuming it's collected.",
    "PS": "Foam polystyrene (like packing peanuts and foam cups) is rarely accepted by curbside recycling due to its low density and contamination risk — it generally goes in general waste. Some specialized drop-off centers accept clean rigid PS.",
    "Others": "Mixed or multi-layer plastics (like chip bags and some pouches) can't be separated into a single material, so they're almost never recyclable through standard programs — dispose of them as general waste, and look for reduce/reuse alternatives where possible.",
}

LEARN_TIPS_MM = {
    "PET": "ဗူးကို လွတ်အောင်ပြုလုပ်ပြီး ရေဆေးပါ၊ အဖုံးကို ပိတ်ထားပါ (ယခုအခါ စက်ရုံအများစုသည် အဖုံးများကိုပါ ပြန်လည်အသုံးပြုပါသည်)၊ နေရာလွတ်သက်သာစေရန် ပြားအောင် ဖိပေးပါ။ ဆီပေကျံနေသော အစားအသောက်ဗူးများကို ရေမဆေးဘဲ မစွန့်ပစ်ပါနှင့်။",
    "HDPE": "ပါဝင်ပစ္စည်းများကို ရေဆေးထုတ်ပါ၊ ရနိုင်ပါက ပန်းကန်ဆေးဆီ/စပရေးခေါင်းများကို ဖြုတ်ပါ၊ အဖုံးတပ်လျက် ပြန်လည်အသုံးပြုပါ။ HDPE သည် စက်ရုံများတွင် အလွယ်ကူဆုံးနှင့် အကျယ်ပြန့်ဆုံး ပြန်လည်အသုံးပြုနိုင်သည့် ပလတ်စတစ်ဖြစ်သည်။",
    "LDPE": "အိတ်များ၊ အုပ်အိတ်များနှင့် ဖလင်ပလတ်စတစ်များကို ပုံမှန် အိမ်သုံး အမှိုက်ပုံးများတွင် ထည့်လေ့မရှိပါ — ကုန်စုံဆိုင် သို့မဟုတ် စူပါမားကတ်များရှိ သီးသန့် စွန့်ပစ်နိုင်သည့် နေရာများကို စစ်ဆေးပါ။ မာကျောသော LDPE ပစ္စည်းများကိုမူ ပုံမှန် ပြန်လည်အသုံးပြုပုံးများတွင် ထည့်နိုင်ပါသည်။",
    "PP": "အစားအသောက် ထည့်သည့်ဗူးများနှင့် ဒိန်ချဉ်ခွက်များကို သေချာ ရေဆေးပါ။ PP ကို ပြန်လည်အသုံးပြုနိုင်သော်လည်း PET/HDPE လောက် အစွန့်ခံလေ့မရှိသဖြင့် ဒေသတွင်း သတ်မှတ်ချက်များကို စစ်ဆေးပါ။",
    "PS": "ဖော့ပလတ်စတစ်များ (ပစ္စည်းထုပ်သုံး ဖော့စေ့များနှင့် ဖော့ခွက်များ) သည် ၎င်း၏ သိပ်သည်းဆနည်းပါးမှုနှင့် ညစ်နွမ်းမှုကြောင့် ပုံမှန် ပြန်လည်အသုံးပြုပုံးများတွင် လက်ခံလေ့မရှိပါ — အထွေထွေ အမှိုက်တွင်သာ ထည့်ရလေ့ရှိသည်။ သန့်ရှင်းသော မာကျောသည့် PS များကို အထူး စွန့်ပစ်စခန်းများတွင် လက်ခံလေ့ရှိသည်။",
    "Others": "အလွှာပေါင်းစုံ ရောနှောထားသော ပလတ်စတစ်များ (အာလူးကြော်အိတ်များကဲ့သို့) ကို သီးခြားခွဲထုတ်၍ မရနိုင်ပါ — ထို့ကြောင့် ပုံမှန် ပြန်လည်အသုံးပြုခြင်း ပြုလုပ်၍မရဘဲ အထွေထွေ အမှိုက်အဖြစ်သာ စွန့်ပစ်ရမည် ဖြစ်သည်။",
}

LEARN_TIPS = LEARN_TIPS_MM if is_mm else LEARN_TIPS_EN

# ==========================================
# STATIC RECYCLING GUIDANCE (No API)
# ==========================================
def get_guidance(plastic_type, recyclable, lang="en"):
    """
    Return static recycling/disposal guidance for each plastic type.
    No API call needed — works offline and always consistent.
    """
    # ---- Myanmar Guidance ----
    guidance_mm = {
        "PET": [
            "ဗူးကို ရေဆေးပြီး အဖုံးကို ပိတ်ထားပါ",
            "နေရာလွတ်သက်သာစေရန် ဗူးကို ပြားအောင် ဖိပေးပါ",
            "အစားအစာ၊ အချိုရည် သို့မဟုတ် ဆီအကြွင်းအကျန်များကို ဖယ်ရှားပြီးမှ ပြန်လည်အသုံးပြုပါ",
            "PET ဗူးများကို သတ်မှတ်ထားသော recycling bin သို့မဟုတ် recycling center များတွင် စွန့်ပစ်ပါ",
            "PET ဗူးအောက်ခြေရှိ Resin Code #1 ကို စစ်ဆေးပါ",
            "ဗူးနှင့်အတူ ပါရှိသော label အပတ်များကို recycling စည်းမျဉ်းအတိုင်း စွန့်ပစ်ပါ",
            "အခြားပလတ်စတစ်အမျိုးအစားများနှင့် မရောနှောဘဲ သတ်မှတ်ထားသည့် PET recycling stream ထဲတွင် ခွဲထားပါ",
            "အလွန်ညစ်ပတ်ခြင်း၊ အစားအစာအကြွင်းအကျန်များရှိခြင်း သို့မဟုတ် ဆီပေကျံခြင်းရှိသော ဗူးများကို သန့်ရှင်းအောင် ပြုလုပ်ပြီးမှ recycle လုပ်ပါ",
            "PET ဗူးများကို ပြန်လည်အသုံးပြုခြင်းဖြင့် ပလတ်စတစ်အမှိုက်ပမာဏကို လျှော့ချနိုင်ပါသည်",
            "Recycling မလုပ်မီ မိမိဒေသရှိ recycling facility ၏ လက်ခံသည့်ပစ္စည်းများနှင့် စည်းမျဉ်းများကို စစ်ဆေးပါ"
        ],
        "HDPE": [
            "ပါဝင်ပစ္စည်းများကို ရေဆေးထုတ်ပြီး ဗူးကို သန့်ရှင်းအောင်ထားပါ",
            "ဗူးအောက်ခြေရှိ Resin Identification Code #2 ကို စစ်ဆေးပါ",
            "ဖြစ်နိုင်ပါက spray head သို့မဟုတ် pump ကို သတ်မှတ်ထားသော recycling စည်းမျဉ်းအတိုင်း ခွဲထားပါ",
            "အဖုံးများကို recycling facility ၏ စည်းမျဉ်းအတိုင်း စီမံပါ",
            "နို့ဗူး၊ ပိုးသတ်ဆေးဗူး၊ ဆပ်ပြာဗူးနှင့် ခေါင်းလျှော်ရည်ဗူးများကဲ့သို့သော HDPE containers များကို သတ်မှတ်ထားသော recycling bins သို့မဟုတ် centers တွင် စွန့်ပစ်ပါ",
            "အခြားပလတ်စတစ်အမျိုးအစားများနှင့် မရောနှောဘဲ ပလတ်စတစ်အမျိုးအစားအလိုက် ခွဲထားပါ",
            "အစားအစာ သို့မဟုတ် အရည်အကြွင်းအကျန်များကို ဖယ်ရှားပြီးမှ recycle လုပ်ပါ",
            "ပြန်လည်အသုံးပြုနိုင်မှုသည် ဒေသအလိုက် ကွာခြားနိုင်သောကြောင့် local recycling facility ၏ စည်းမျဉ်းများကို စစ်ဆေးပါ"
        ],
        "LDPE": [
            "ကုန်စုံဆိုင် သို့မဟုတ် စူပါမားကတ်များရှိ သီးသန့် ပလတ်စတစ်အိတ်နှင့် plastic film စွန့်ပစ်နိုင်သည့်နေရာများကို ရှာပါ",
            "LDPE ပစ္စည်းများကို သတ်မှတ်ထားသော ပြန်လည်အသုံးပြုနိုင်သည့်နေရာများတွင် စွန့်ပစ်ပါ",
            "အိတ်များကို သန့်ရှင်းပြီး ခြောက်သွေ့အောင်ထားပါ",
            "အစားအစာအကြွင်းအကျန်၊ ဆီနှင့် အညစ်အကြေးများကို ဖယ်ရှားပြီးမှ recycle လုပ်ပါ",
            "ပလတ်စတစ်အိတ်၊ ပေါင်မုန့်အိတ်၊ stretch film နှင့် bubble wrap ကဲ့သို့သော LDPE film များကို သတ်မှတ်ထားသော recycling point များတွင် ပြန်လည်အသုံးပြုနိုင်ပါသည်",
            "Plastic ပေါ်တွင်ရှိ Resin Identification Code ပါရှိပါက Resin code ကို #4 ဖြစ်ကြောင်းစစ်ဆေးပြီး LDPE ဖြစ်ကြောင်း အတည်ပြုပါ",
            "Paper labels သို့မဟုတ် sticker များကို ဖြစ်နိုင်ပါက ဖယ်ရှားပြီး recycle လုပ်ပါ",
            "အခြားပလတ်စတစ်အမျိုးအစားများနှင့် ရောစပ်ထားသော multi-layer သို့မဟုတ် laminated plastic များကို သီးခြားစစ်ဆေးပါ",
            "ပြန်လည်အသုံးပြုရန် မသေချာပါက သင့်ဒေသရှိ recycling center ၏ စည်းမျဉ်းများကို စစ်ဆေးပါ",
            "Recycle မလုပ်နိုင်သေးသော LDPE အိတ်များကို ဖြစ်နိုင်ပါက အသုံးပြုပြီးနောက် စနစ်တကျ စွန့်ပစ်ပါ"
        ],
        "PP": [
            "အစားအသောက်ထည့်သည့်ဗူးများ၊ ဒိန်ချဉ်ခွက်များနှင့် အခြား PP ပစ္စည်းများကို ရေဆေးပြီး သန့်ရှင်းအောင်ထားပါ",
            "ဗူးအောက်ခြေရှိ Resin Identification Code #5 ကို စစ်ဆေးပါ",
            "အစားအသောက် သို့မဟုတ် အဆီအကြွင်းအကျန်များကို ဖယ်ရှားပြီးမှ recycle လုပ်ပါ",
            "PP ကို ပြန်လည်အသုံးပြုနိုင်သော်လည်း ဒေသအလိုက် recycling facility များတွင် လက်ခံမှုကွာခြားနိုင်ပါသည်",
            "အဖုံးများကို local recycling guidelines အတိုင်း ဗူးနှင့်အတူ သို့မဟုတ် သီးခြား recycle လုပ်ပါ",
            "မိုက်ခရိုဝေ့ဖ်သုံး food containers၊ yogurt cups နှင့် bottle caps များတွင် PP ကို အသုံးများပါသည်",
            "အခြားပလတ်စတစ်အမျိုးအစားများနှင့် မရောနှောဘဲ သတ်မှတ်ထားသော recycling bin တွင် စွန့်ပစ်ပါ",
            "ဒေသတွင်း recycling facility ၏ လက်ခံသည့်ပစ္စည်းများနှင့် စည်းမျဉ်းများကို စစ်ဆေးပါ",
            "PP အမျိုးအစား ခြင်းများ ထိုင်ခုံများလည်းရှိရာ ပစ္စည်းများ ပျက်စီးကျိုးပဲ့ပါက စနစ်တကျစွန့်ပစ်ခြင်းဖြင့်ပြန်လည်အသုံးပြုနိုင်ရန် ကူညီပါ",
        ],
        "PS": [
            "ဖော့ခွက်၊ ဖော့အစားအသောက်ဗူးများနှင့် packing foam များကို ပုံမှန် recycling bin ထဲ မထည့်ပါနှင့်",
            "PS ပစ္စည်းများကို ဒေသတွင်း recycling facility က လက်ခံမလက်ခံ စစ်ဆေးပါ",
            "သန့်ရှင်းသော မာကျောသည့် PS ပစ္စည်းများကို သတ်မှတ်ထားသော recycling center များတွင် လက်ခံနိုင်ပါသည်",
            "အစားအသောက်အကြွင်းအကျန်များနှင့် အညစ်အကြေးများကို ဖယ်ရှားပြီးမှ ပြန်လည်အသုံးပြုပါ",
            "PS အမျိုးအစားသည် ကျွတ်ဆတ် ပေါ့ပါးပြီး ပျက်စီးလွယ်သောကြောင့် အခြားပလတ်စတစ်များထက် ပြန်လည်အသုံးပြုရန် ပိုမိုခက်ခဲနိုင်ပါသည်",
            "PS ပစ္စည်းများကို မိုက်ခရိုဝေ့ဖ်တွင် အပူပေးအသုံးပြုခြင်းမှ ရှောင်ကြဉ်ပါ",
            "ဒေသအလိုက် recycling စည်းမျဉ်းများ ကွာခြားနိုင်သောကြောင့် local recycling facility ၏ လမ်းညွှန်ချက်များကို စစ်ဆေးပါ"
        ],
        "Others": [
            "အလွှာပေါင်းစုံ ရောနှောထားသော ပလတ်စတစ်များ (အာလူးကြော်အိတ်များကဲ့သို့) ကို သီးခြားခွဲထုတ်၍ မရနိုင်ပါ",
            "ပုံမှန် ပြန်လည်အသုံးပြုခြင်း ပြုလုပ်၍မရဘဲ ပျက်စီးသွားပါက အထွေထွေ အမှိုက်အဖြစ်သာ စွန့်ပစ်ရမည်",
            "ပလတ်စတစ်သုံးစွဲမှုကို လျှော့ချရန် ပြန်လည်အသုံးပြုနိုင်သော ထုပ်ပိုးမှုများကို ရှာဖွေပါ",
            "ဇီဝပလတ်စတစ်များသည် အထူးအခြေအနေများတွင်မှ ပြန်လည်အသုံးပြုနိုင်သည် — ဒေသတွင်း စစ်ဆေးပါ",
            "စနစ်တကျ စစ်‌ဆေးပြီး ပြန်လည်အသုံးပြုနိုင်သည့်ပစ္စည်းများရှိသော်ငြား အများစုမှာ ပျက်စီးပြီးနောက်ပြန်လည် အသုံးပြုရန်ခက်ခဲသည်",
            "ပလတ်စတစ်မဟုတ်သော အခြား အမျိုးအစားများမှာလည်း ပုံမှန်အခြေအနေထက်ယိုယွင်းပျက်စီးသွားပါက ပြန်လည်အသုံးပြု၍မရနိုင်သောကြောင့် သေချာစွန့်ပစ်ပါ",
        ]
    }
    
    # ---- English Guidance ----
    guidance_en = {
        "PET": [
            "Rinse the bottle and keep the cap attached, if required by the local recycling facility",
            "Flatten the bottle to save space",
            "Remove food, drink, or oil residue before recycling",
            "Dispose of PET bottles in designated recycling bins or recycling centers",
            "Check the Resin Identification Code #1 to identify PET plastic",
            "Follow local recycling guidelines for labels and bottle caps",
            "Keep PET bottles separate from other types of plastic when required",
            "Make sure the bottle is empty, clean, and dry before recycling",
            "Avoid mixing PET bottles with non-recyclable or contaminated plastics",
            "Check with the local recycling facility to confirm whether PET bottles are accepted"
        ],
        "HDPE": [
            "Rinse the container and keep it clean before recycling",
            "Check the Resin Identification Code #2 to identify HDPE",
            "Remove spray heads or pumps if required by the local recycling facility",
            "Follow local recycling guidelines for bottle caps",
            "Recycle HDPE containers such as milk, water, detergent, and shampoo bottles at designated recycling bins or centers",
            "Keep HDPE separate from other plastic types when required",
            "Remove food or liquid residue before recycling",
            "Check local recycling guidelines because HDPE recycling availability may vary by area"
        ],
        "LDPE": [
            "Find designated recycling points for plastic bags and films at grocery stores or supermarkets",
            "Check the Resin Identification Code #4 to identify LDPE plastic",
            "Keep plastic bags and films clean and dry before recycling",
            "Remove food, oil, and other residue before recycling",
            "Do not place plastic bags and films in regular recycling bins unless accepted by the local recycling facility",
            "LDPE is commonly used for plastic bags, bread bags, produce bags, and plastic films",
            "Keep LDPE separate from other types of plastic when required",
            "Reuse plastic bags when possible to reduce plastic waste",
            "Check local recycling guidelines because LDPE recycling availability varies by area"
        ],
        "PP": [
            "Rinse food containers, yogurt cups, and other PP items and keep them clean",
            "Check the Resin Identification Code #5 to identify PP plastic",
            "Remove food and grease residue before recycling",
            "PP can be recycled, but acceptance may vary depending on the local recycling facility",
            "Recycle caps with the container or separately according to local recycling guidelines",
            "PP is commonly used for microwave-safe food containers, yogurt cups, and bottle caps",
            "Keep PP separate from other types of plastic when required",
            "Check local recycling guidelines to confirm whether PP items are accepted"
        ],
        "PS": [
            "Do not place foam cups, foam food containers, or packing foam in regular recycling bins",
            "Check whether PS items are accepted by your local recycling facility",
            "Clean rigid PS items may be accepted at designated recycling centers",
            "Remove food residue and contamination before recycling",
            "PS can be more difficult to recycle because it is lightweight and easily broken",
            "Avoid heating PS food containers in the microwave unless they are specifically labeled as microwave-safe",
            "Follow local recycling guidelines because PS recycling availability varies by area"
        ],
        "Others": [
            "Mixed or multi-layer plastics (like chip bags and some pouches) can't be separated",
            "They are almost never recyclable through standard programs — dispose as general waste",
            "Look for reduce/reuse alternatives where possible",
            "Bioplastics may require special conditions to be recyclable — check local facilities",
            "Although there are items that can be reused after proper inspection, most are difficult to reuse once damaged",
            "Avoid purchasing items with 'Other' plastic labeling when possible",
            "For non-plastic items as well, please dispose of them properly, as they cannot be reused if they deteriorate beyond their normal condition.",
        ]
    }

    # Select language
    guidance_dict = guidance_mm if lang == "mm" else guidance_en
    
    # Return guidance for the given plastic type, fallback to "Others"
    return guidance_dict.get(plastic_type, guidance_dict["Others"])

def generate_pdf_report(image, plastic_type, confidence, info, guidance_points, lang="en"):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    if lang == "mm":
        recyclable_text = "ပြန်လည်အသုံးပြုနိုင်သည်" if info["recyclable"] else "ပြန်လည်အသုံးပြု၍မရပါ"
        doc_title = "♻️ EcoSort - ပလတ်စတစ် ပြန်လည်အသုံးပြုရေး အစီရင်ခံစာ"
        date_lbl = "ရက်စွဲ"
        card1_title = "စစ်ဆေးမှု ရလဒ်နှင့် တွေ့ရှိသော ပလတ်စတစ် အသေးစိတ်"
        p_type_lbl = "ပလတ်စတစ် အမျိုးအစား"
        code_lbl = "ကုဒ်နံပါတ်"
        conf_lbl = "ယုံကြည်စိတ်ချရမှု"
        status_lbl = "အခြေအနေ"
        desc_lbl = "ဖော်ပြချက်"
        card2_title = "အဓိက ဂုဏ်သတ္တိများနှင့် အသုံးများသည့် ပစ္စည်းများ"
        uses_lbl = "အသုံးများသည့် ပစ္စည်းများ"
        card3_title = "ပြန်လည်အသုံးပြုမှု လမ်းညွှန်ချက်များ"
    else:
        recyclable_text = "Recyclable" if info["recyclable"] else "Non-recyclable"
        doc_title = "♻️ EcoSort - Plastic Recycling Report"
        date_lbl = "Date"
        card1_title = "Analysis Results & Identified Plastic Details"
        p_type_lbl = "Plastic Type"
        code_lbl = "Resin Code"
        conf_lbl = "Confidence"
        status_lbl = "Status"
        desc_lbl = "Description"
        card2_title = "Key Properties & Common Uses"
        uses_lbl = "Common Uses"
        card3_title = "Recycling Guidance"

    properties_list = info.get("properties", [])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Myanmar:wght@400;500;600;700&family=Padauk:wght@400;700&display=swap');
        @import url('https://mmwebfonts.com/css/pyidaungsu.css');
        @page {{ size: A4; margin: 10mm; background-color: #fdfbf7; }}
        * {{ font-family: 'Pyidaungsu', 'Noto Sans Myanmar', 'Padauk', 'Myanmar3', sans-serif !important; }}
        body {{ font-family: 'Pyidaungsu', 'Noto Sans Myanmar', 'Padauk', 'Myanmar3', sans-serif !important; color: #333; font-size: 13px; line-height: 2.2; }}
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
            <div class="title">{doc_title}</div>
            <p style="font-size: 9px; color: #666;">{date_lbl}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="img-container">
            <img src="data:image/png;base64,{img_str}" alt="Scanned Plastic">
        </div>

        <div class="card">
            <h3>{card1_title}</h3>
            <p><strong>{p_type_lbl}:</strong> {plastic_type} ({info['name_en']}) </br><strong>{code_lbl}:</strong> #{info['code']} </br><strong>{conf_lbl}:</strong> {confidence:.1f}% </br><strong>{status_lbl}:</strong> {recyclable_text}</p>
            <p><strong>{desc_lbl}:</strong> {info['description']}</p>
        </div>

        <div class="card">
            <h3>{card2_title}</h3>
            <ul>
                {"".join([f"<li>{prop}</li>" for prop in properties_list])}
            </ul>
            <p style="margin-top: 4px;"><strong>{uses_lbl}:</strong> {info['examples']}.</p>
        </div>

        <div class="info-box">
            <h3>{card3_title}</h3>
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
    return YOLO("ecosort_det_best.pt")

model = load_model()

# ==========================================
# PAGE VIEWS: WASTE CHART & ABOUT PAGE
# ==========================================
def render_waste_chart(lang="en"):
    th = st.session_state["_theme"]
    is_mm = (lang == "mm")
    
    title_text = "ကမ္ဘာ့နှင့် မြန်မာနိုင်ငံ၏ ပလတ်စတစ် ပြန်လည်အသုံးပြုနိုင်မှု နှုန်းထား" if is_mm else "Global vs. Myanmar Plastic Recycling"
    st.markdown(f'<div class="section-title">{title_text}</div>', unsafe_allow_html=True)

    years = [2000, 2005, 2010, 2015, 2019, 2022, 2023, 2024, 2025]
    global_rate = [5, 7, 9, 11, 13, 9.5, 9.8, 10.2, 10.5]
    myanmar_rate = [3, 3.5, 4, 5, 6, 7, 7.5, 8, 8.5]

    color_global = "#118AB2"
    color_myanmar = "#EF476F"

    name_g = "ကမ္ဘာ့နှုန်းထား" if is_mm else "Global"
    name_m = "မြန်မာနိုင်ငံ (ဒေသတွင်း ခန့်မှန်းချက်)" if is_mm else "Myanmar (regional estimate)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=global_rate, mode="lines+markers", name=name_g,
        line=dict(color=color_global, width=4, shape="spline"),
        marker=dict(size=9, color=color_global),
    ))
    fig.add_trace(go.Scatter(
        x=years, y=myanmar_rate, mode="lines+markers", name=name_m,
        line=dict(color=color_myanmar, width=4, dash="dash", shape="spline"),
        marker=dict(size=9, color=color_myanmar),
    ))
    
    y_title = "ပြန်လည်အသုံးပြုမှု နှုန်းထား (%)" if is_mm else "Recycling rate (%)"

    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Pyidaungsu, Nunito, sans-serif", color=th["text"], size=13),
        margin=dict(l=10, r=10, t=10, b=10),
        height=340,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            font=dict(color=th["text"], size=13),
        ),
        xaxis=dict(title=None, gridcolor=th["border"], zeroline=False, tickfont=dict(color=th["text"])),
        yaxis=dict(
            title=y_title, gridcolor=th["border"], zeroline=False, ticksuffix="%",
            tickfont=dict(color=th["text"]), title_font=dict(color=th["text"]),
        ),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if is_mm:
        caption_html = """
        <div class="chart-caption">
            အချက်အလက် အရင်းအမြစ်များ: OECD / Our World in Data (ကမ္ဘာ့ ပလတ်စတစ် ပြန်လည်အသုံးပြုမှု နှုန်းထား ၂၀၀၀-၂၀၁၉); 
            ၂၀၂၂ တွင် ကမ္ဘာ့ ပြန်လည်အသုံးပြုနိုင်မှု အချိုးအစား ~၉.၅% (Tsinghua University, 2025)။
            ၂၀၂၃-၂၀၂၅ တန်ဖိုးများသည် လက်ရှိ ဖြစ်ပေါ်တိုးတက်မှုများပေါ် အခြေခံထားသော ခန့်မှန်းချက်များ ဖြစ်သည်။
            မြန်မာနိုင်ငံ လိုင်းသည် ဝင်ငွေနည်း/အလယ်အလတ်ရှိသော အာဆီယံနိုင်ငံများအတွက် OECD ဒေသတွင်း ခန့်မှန်းချက်ကို ထိန်းသိမ်းထားခြင်း ဖြစ်သည်
            (OECD <i>Regional Plastics Outlook for Southeast and East Asia</i>, 2023)။
        </div>
        """
    else:
        caption_html = """
        <div class="chart-caption">
            Sources: OECD / Our World in Data (global waste-recycling-rate trend, 2000–2019); 
            global recycled-content share ~9.5% in 2022 (Tsinghua University, 2025).
            2023–2025 values are projections based on current trends.
            Myanmar line reflects OECD regional estimate for lower/middle-income ASEAN countries
            (OECD <i>Regional Plastics Outlook for Southeast and East Asia</i>, 2023).
        </div>
        """
    st.markdown(caption_html, unsafe_allow_html=True)

def render_about_page(lang="en"):
    th = st.session_state["_theme"]
    is_mm = (lang == "mm")
    
    if is_mm:
        st.markdown("""
        <div class="eco-header">
            <div class="eco-title">♻ EcoSort အကြောင်း</div>
            <div class="eco-subtitle">အေအိုင် · ပလတ်စတစ် ခွဲခြားစနစ် · ပြန်လည်အသုံးပြုမှု လမ်းညွှန်</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="result-card result-card-flex">
            <div class="about-p">
                <b>EcoSort</b> သည် ဘွဲ့ကြို ပရောဂျက်တစ်ခုအဖြစ် ဖန်တီးထားသော အေအိုင်သုံး ပလတ်စတစ် အမျိုးအစား ခွဲခြားမှုနှင့် ပြန်လည်အသုံးပြုမှု လမ်းညွှန်စနစ် ဖြစ်ပါသည်။ ဓာတ်ပုံမှတစ်ဆင့် ပလတ်စတစ် အမျိုးအစားများ (PET, HDPE, LDPE, PP, PS သို့မဟုတ် Others) ကို ခွဲခြားရန် YOLOv8 Deep Learning မော်ဒယ်ကို အသုံးပြုထားပြီး ပြန်လည်အသုံးပြုနိုင်ခြင်း ရှိမရှိနှင့် စနစ်တကျ စွန့်ပစ်နည်း လမ်းညွှန်ချက်များကို ဖော်ပြပေးပါသည်။
            </div>
            <div class="about-p">
                <b>အရေးပါမှု:</b> ကမ္ဘာပေါ်တွင် စွန့်ပစ် ပလတ်စတစ်၏ ၁၀% အောက်သာ ပြန်လည်အသုံးပြုနိုင်သေးပြီး ပလတ်စတစ် အမျိုးအစားအလိုက် ခွဲခြားခြင်းသည် ပြန်လည်အသုံးပြုရေး လုပ်ငန်းစဉ်၏ အဓိက အခက်အခဲ ဖြစ်ပါသည်။ EcoSort သည် ကွန်ပျူတာ အမြင်ခွဲခြားခြင်း နည်းပညာဖြင့် ပြည်သူများ လွယ်ကူစွာ သေချာစွာ ခွဲခြားနိုင်စေရန် ရည်ရွယ်ပါသည်။
            </div>
            <div class="about-p">
                <b>အသုံးပြုထားသော နည်းပညာများ:</b> ခွဲခြားစစ်ဆေးရန် YOLOv8 (Ultralytics)၊ အသုံးပြုသူ အင်တာဖေ့စ်အတွက် Streamlit နှင့် လွယ်ကူသော လမ်းညွှန်ချက်များ ထုတ်ပေးနိုင်ရန် develop လုပ်ထားပါသည်။
            </div>
            <div class="about-p">
                <b>ရေးသားသူ:</b> ဇင်ဝတ်ရည်ဇော်၊ ပြည်ကွန်ပျူတာတက္ကသိုလ် (UCSPyay)၊ ကွန်ပျူတာသိပ္ပံ ကျောင်းသူ။<br>
                <b>ဆက်သွယ်ရန်:</b> wyee659@gmail.com
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
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
                and disposal guidance.
            </div>
            <div class="about-p">
                <b>Author:</b> Zin Wut Yee Zaw, UCSPyay, Computer Science Student.<br>
                <b>Contact:</b> wyee659@gmail.com.
            </div>
        </div>
        """, unsafe_allow_html=True)

    render_waste_chart(lang)

# ==========================================
# PAGE VIEW: DASHBOARD
# ==========================================
def render_dashboard_page(lang="en"):
    th = st.session_state["_theme"]
    is_mm = (lang == "mm")
    
    title_text = "ဒက်ရှ်ဘုတ် (Dashboard)" if is_mm else "Dashboard"
    sub_text = "စကင်ဖတ်မှု မှတ်တမ်းနှင့် ကိန်းဂဏန်းများ" if is_mm else "Global Scan History & Stats"
    
    st.markdown(f"""
    <div class="eco-header">
        <div class="eco-title">{title_text}</div>
        <div class="eco-subtitle">{sub_text}</div>
    </div>
    """, unsafe_allow_html=True)

    # Always fetch latest stats directly from disk to ensure persistence across restarts
    st.session_state.global_stats = load_global_stats()
    stats = st.session_state.global_stats
    history = stats.get("history", [])
    total = stats.get("total_scans", 0)
    type_counts = stats.get("plastic_types", {})

    if total == 0:
        no_scan_title = "စကင်ဖတ်ထားမှုများ မရှိသေးပါ" if is_mm else "No scans yet"
        no_scan_sub = "ကိန်းဂဏန်းများကို ကြည့်ရှုရန် 'ခွဲခြားစစ်ဆေးရန်' စာမျက်နှာတွင် ပလတ်စတစ်ပုံ ပို့ပါ။" if is_mm else "Classify a plastic item on the Classifier page to see stats here."
        st.markdown(f"""
        <div class="empty-state">
            <div style="font-size:4rem; margin-bottom:1rem">📊</div>
            <div style="font-size:1.1rem; font-weight:500; margin-bottom:0.5rem">{no_scan_title}</div>
            <div style="font-size:0.85rem; opacity:0.7">{no_scan_sub}</div>
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
    metric_labels = [
        (m1, total, "စုစုပေါင်း စကင်ဖတ်မှု" if is_mm else "Total Scans"),
        (m2, f"{recyclable_pct}%", "ပြန်လည်အသုံးပြုနိုင်မှု" if is_mm else "Recyclable"),
        (m3, most_common, "အများဆုံး အမျိုးအစား" if is_mm else "Most Common"),
        (m4, f"{avg_conf}%", "ပျမ်းမျှ ယုံကြည်စိတ်ချရမှု" if is_mm else "Avg. Confidence"),
    ]
    for col, value, label in metric_labels:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    sec_title1 = "ပလတ်စတစ် အမျိုးအစားအလိုက် စကင်ဖတ်မှု" if is_mm else "Scans by Plastic Type"
    st.markdown(f'<div class="section-title">{sec_title1}</div>', unsafe_allow_html=True)
    
    bar_fig = go.Figure(go.Bar(
        x=list(type_counts.keys()),
        y=list(type_counts.values()),
        marker_color=[COLORS.get(k, th["accent"]) for k in type_counts.keys()],
        text=list(type_counts.values()),
        textposition="outside",
    ))
    y_axis_lbl = "အရေအတွက်" if is_mm else "Count"
    bar_fig.update_layout(
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Pyidaungsu, Nunito, sans-serif", color=th["text"], size=13),
        margin=dict(l=10, r=10, t=20, b=10),
        height=300,
        xaxis=dict(title=None, gridcolor=th["border"], tickfont=dict(color=th["text"])),
        yaxis=dict(title=y_axis_lbl, gridcolor=th["border"], tickfont=dict(color=th["text"]),
                    title_font=dict(color=th["text"])),
        showlegend=False,
    )
    st.plotly_chart(bar_fig, use_container_width=True, config={"displayModeBar": False})

    col_a, col_b = st.columns([1, 1.4], gap="large")
    with col_a:
        sec_title2 = "♻️ ပြန်လည်အသုံးပြုနိုင်မှု အချိုးအစား" if is_mm else "♻️ Recyclable Split"
        st.markdown(f'<div class="section-title">{sec_title2}</div>', unsafe_allow_html=True)
        
        pie_labels = ["ပြန်လည်အသုံးပြုနိုင်သည်", "ပြန်လည်အသုံးပြု၍မရပါ"] if is_mm else ["Recyclable", "Non-recyclable"]
        pie_fig = go.Figure(go.Pie(
            labels=pie_labels,
            values=[recyclable_count, max(0, total - recyclable_count)],
            hole=0.55,
            marker=dict(colors=["#06D6A0", "#EF476F"]),
            textfont=dict(color="#FFFFFF", size=13),
        ))
        pie_fig.update_layout(
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Pyidaungsu, Nunito, sans-serif", color=th["text"], size=13),
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
            legend=dict(font=dict(color=th["text"])),
        )
        st.plotly_chart(pie_fig, use_container_width=True, config={"displayModeBar": False})

    with col_b:
        sec_title3 = "လတ်တလော စကင်ဖတ်မှုများ" if is_mm else "Recent Scans"
        st.markdown(f'<div class="section-title">{sec_title3}</div>', unsafe_allow_html=True)
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

    clear_btn_text = "🗑️ မှတ်တမ်းများကို ရှင်းလင်းမည်" if is_mm else "🗑️ Clear global stats"
    if st.button(clear_btn_text):
        st.session_state.global_stats = {"total_scans": 0, "plastic_types": {}, "history": []}
        save_global_stats(st.session_state.global_stats)
        st.session_state.last_file_key = None
        st.rerun()

# ==========================================
# PAGE VIEW: LEARN SECTION
# ==========================================
def render_learn_page(lang="en"):
    th = st.session_state["_theme"]
    is_mm = (lang == "mm")
    
    title_text = "လေ့လာရန် (Learn)" if is_mm else "Learn"
    sub_text = "ပလတ်စတစ် အမျိုးအစားများနှင့် ပြန်လည်အသုံးပြုခြင်း အခြေခံများ" if is_mm else "Plastic Types & Recycling Basics"
    st.markdown(f"""
    <div class="eco-header">
        <div class="eco-title">{title_text}</div>
        <div class="eco-subtitle">{sub_text}</div>
    </div>
    """, unsafe_allow_html=True)

    vid_title = "ပြန်လည်အသုံးပြုခြင်းစနစ်သရုပ်ပြ ဗီဒီယို" if is_mm else "Recycling Process Video"
    st.markdown(f'<div class="section-title">{vid_title}</div>', unsafe_allow_html=True)
    st.video("https://youtu.be/MwL8kgyOzFA?si=13bvQnmQG3AunDIh")

    proc_title = "♻️ ပလတ်စတစ် ပြန်လည်အသုံးပြုပုံ အဆင့်ဆင့်" if is_mm else "♻️ How Plastic Recycling Works (Step by Step)"
    st.markdown(f'<div class="section-title">{proc_title}</div>', unsafe_allow_html=True)

    step_images = {
        "step1": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/img/ds2pe_image_239.jpg",
        "step2": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/img/plastic-recycling-sorting-image.jpg",
        "step3": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/img/close-hands.jpg",
        "step4": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/img/T8200219.jpg",
        "step5": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/img/plastic-pellet.jpg",
        "step6": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/img/AdobeStock_759704272-1.jpeg",
        "step7": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/img/ppm.jpg",

    }

    steps_data = [
        {
            "img": step_images["step1"],
            "title": "အဆင့် ၁ - စုဆောင်းခြင်း (Collection)" if is_mm else "Step 1: Collection",
            "desc": "ပလတ်စတစ် စွန့်ပစ်ပစ္စည်းများကို နေအိမ်များ၊ လုပ်ငန်းများနှင့် ပြန်လည်အသုံးပြုမှု စွန့်ပစ်စခန်းများမှ စုဆောင်းပါသည်။ ဤသည်မှာ ပထမဆုံးနှင့် အရေးအကြီးဆုံး အဆင့်ဖြစ်ပြီး စနစ်တကျ စုဆောင်းမှု မရှိပါက ပြန်လည်အသုံးပြုခြင်း ပြုလုပ်နိုင်မည် မဟုတ်ပါ။" if is_mm else "Plastic waste is collected from households, businesses, and recycling drop-off points. This is the first and most important step — without proper collection, recycling can't happen.",
            "tip": "<b>အကြံပြုချက်:</b> အမှိုက်ပုံးထဲ မထည့်မီ သင့်ပလတ်စတစ်များကို အမျိုးအစားအလိုက် (ဗူးများ၊ ပုံးများ၊ အိတ်များ) သီးခြား ခွဲခြားထားပါ။" if is_mm else "<b>Tip:</b> Separate your plastics by type (bottles, containers, bags) before putting them in the recycling bin."
        },
        {
            "img": step_images["step2"],
            "title": "အဆင့် ၂ - ခွဲခြားခြင်း (Sorting)" if is_mm else "Step 2: Sorting",
            "desc": "ပလတ်စတစ်များကို ၎င်းတို့၏ ရာဇင်အမျိုးအစားအလိုက် (PET, HDPE, PP စသည်ဖြင့်) အဆင့်မြင့် အလင်းစကင်ဖတ်စက်များ သို့မဟုတ် လူကိုယ်တိုင် ခွဲခြားကြပါသည်။ အမျိုးအစား မတူသော ပလတ်စတစ်များကို အတူတကွ ပြန်လည်အသုံးပြု၍ မရနိုင်ပါ။" if is_mm else "Plastics are sorted by resin type (PET, HDPE, PP, etc.) using advanced optical sorters and manual labor. Different types can't be recycled together.",
            "tip": "<b>အကြံပြုချက်:</b> သင့် ပလတ်စတစ် ပစ္စည်းများ၏ အောက်ခြေတွင် ပါရှိသော ရာဇင်ကုဒ် (♳-♹) သင်္ကေတကို စစ်ဆေးပါ — ဤသင်္ကေတအတိုင်း ခွဲခြားရခြင်း ဖြစ်သည်။" if is_mm else "<b>Tip:</b> Check the resin code (♳-♹) on the bottom of your plastic items — this is how they're sorted!"
        },
        {
            "img": step_images["step3"],
            "title": "အဆင့် ၃ - သန့်စင်ခြင်း (Cleaning)" if is_mm else "Step 3: Cleaning",
            "desc": "ပလတ်စတစ်များကို တံဆိပ်ကပ်များ၊ ကော်များ၊ အစားအသောက် အကြွင်းအကျန်များနှင့် ဖုန်မှုန့်များ ကင်းစင်စေရန် ဆေးကြောကြပါသည်။ ပေကျံနေသော ပလတ်စတစ်များသည် အသုတ်တစ်ခုလုံးကို ပျက်စီးစေနိုင်သဖြင့် ဤအဆင့်မှာ အလွန်အရေးပါသည်။" if is_mm else "Plastics are washed to remove labels, glue, food residue, and dirt. This is critical — contaminated plastics can ruin an entire batch.",
            "tip": "<b>အကြံပြုချက်:</b> စွန့်ပစ် မပြောင်းမီ သင့် ပလတ်စတစ် ပစ္စည်းများကို ရေဆေးလိုက်ပါ! အနည်းငယ် ဆေးကြောလိုက်ခြင်းသည် သန့်စင်ရေး စက်ရုံအတွက် အလွန် ကူညီရာရောက်ပါသည်။" if is_mm else "<b>Tip:</b> Rinse your plastic items before recycling! A quick rinse makes a huge difference at the cleaning facility."
        },
        {
            "img": step_images["step4"],
            "title": "အဆင့် ၄ - ကြိတ်စေ့ပြုလုပ်ခြင်း (Shredding)" if is_mm else "Step 4: Shredding",
            "desc": "သန့်စင်ပြီးသော ပလတ်စတစ်များကို သေးငယ်သော အစုတ်စုတ်အမြွှာမြွှာ ကြိတ်စေ့များအဖြစ် ကြိတ်ခွဲလိုက်ပါသည်။ ၎င်းသည် မျက်နှာပြင် အကျယ်အဝန်းကို တိုးတက်စေပြီး အရည်ကြိုရန်နှင့် ပုံသွင်းရန် လွယ်ကူစေပါသည်။" if is_mm else "Clean plastic is shredded into small flakes or pellets. This increases the surface area and makes it easier to melt and reform.",
            "tip": "<b>အကြံပြုချက်:</b> ပလတ်စတစ် ကြိတ်စေ့များသည် ဗူးများမှသည် အဝတ်အထည်များအထိ ပလတ်စတစ်သစ် ပစ္စည်းများ ပြုလုပ်ရန် ကုန်ကြမ်းဖြစ်ပါသည်။" if is_mm else "<b>Tip:</b> Shredded plastic flakes are the raw material for making new plastic products — from bottles to clothing!"
        },
        {
            "img": step_images["step5"],
            "title": "အဆင့် ၅ - ပလတ်စတစ်စေ့ ပြုလုပ်ခြင်း (Pelletizing)" if is_mm else "Step 5: Pelletizing",
            "desc": "ကြိတ်ခွဲထားသော ပလတ်စတစ်များကို အရည်ကြိုပြီး သေးငယ်သော ပလတ်စတစ်စေ့များအဖြစ် ပုံသွင်းပါသည်။ ဤစေ့များကို စက်ရုံများသို့ ပြန်လည်ရောင်းချပြီး ပလတ်စတစ် သစ်များ ထုတ်လုပ်ကာ ပြန်လည်အသုံးပြုမှု သံသရာကို ပြည့်စုံစေပါသည်။" if is_mm else "Shredded plastic is melted and formed into small pellets (nurdles). These pellets are then sold to manufacturers to make new plastic products — closing the recycling loop!",
            "tip": "<b>အကြံပြုချက်:</b> ပတ်ဝန်းကျင် ထိန်းသိမ်းရေးကို အထောက်အကူပြုရန် ပြန်လည်အသုံးပြုထားသည့် ပလတ်စတစ် (\"Post-Consumer Recycled\" သို့မဟုတ် \"PCR\") ဖြင့် ပြုလုပ်ထားသော ပစ္စည်းများကို အသုံးပြုပါ။" if is_mm else "<b>Tip:</b> Look for products made from recycled plastic (often labeled \"Post-Consumer Recycled\" or \"PCR\") to support the circular economy."
        },
        {
            "img": step_images["step6"],
            "title": "အဆင့် ၆ - ပလတ်စတစ်ထုတ်ကုန်သစ် တီထွင်ဖန်တီးခြင်း" if is_mm else "Step 6: Plastic new product development",
            "desc": "ထုတ်ကုန်တစ်ခုအဖြစ် ပြောင်းလဲပေးသည့် စနစ်တကျရှိသော အင်ဂျင်နီယာလုပ်ငန်းစဉ်တစ်ခု ဖြစ်ပါသည်။ ၎င်းလုပ်ငန်းစဉ်တွင် စိတ်ကူးပုံစံရေးဆွဲခြင်း၊ ကုန်ကြမ်းပစ္စည်း ရွေးချယ်ခြင်း၊ ဒစ်ဂျစ်တယ်နည်းဖြင့် စမ်းသပ်ပုံဖော်ခြင်း (digital simulation)၊ လျင်မြန်စွာ ပုံစံငယ်ထုတ်လုပ်ခြင်း (rapid prototyping) နှင့် Injection Molding ကဲ့သို့သော တိကျသေချာသည့် ပုံစံခွက်ပြုလုပ်ခြင်း (precision tooling) စသည့် အဆင့်များအကြား ညှိနှိုင်းဆောင်ရွက်မှုများ လိုအပ်ပါသည်။" if is_mm else "Plastic new product development is a structured engineering process that transforms an initial concept into a mass-manufactured polymer item. It requires coordinated steps across concept design, material selection, digital simulation, rapid prototyping, and precision tooling like injection molding",
            "tip": "<b>အကြံပြုချက်:</b> ပလတ်စတစ်များ ပတ်ဝန်းကျင်တွင် ပြန့်ကျဲကာ အသုံးမဝင်သည့် အမှိုက်များ အဖြစ်ရှိနေမည့်အစား အသုံးဝင်ပြီး အကျိုးပြုနိုင်စေမည့် အရာတစ်ခုအဖြစ် ပြန်လည်ထုတ်လုပ် အသုံးပြုကြပါစို့။" if is_mm else "<b>Tip:</b> Look for products made from recycled plastic (often labeled \"Post-Consumer Recycled\" or \"PCR\") to support the circular economy."
        },
        {
            "img": step_images["step7"],
            "title": "ပလတ်စတစ် အမှုန်ပြုလုပ်စက်" if is_mm else "Plastic Pelletizer",
            "desc": "ကုန်ကြမ်းပလတ်စတစ် သို့မဟုတ် စွန့်ပစ်ပလတ်စတစ်အစအနများကို အရည်ပျော်စေပြီး အရွယ်အစားညီညာကာ ကိုင်တွယ်အသုံးပြုရလွယ်ကူသော အစေ့အဆန်ငယ်လေးများ (pellets) အဖြစ် ဖြတ်တောက်ထုတ်လုပ်ပေးသည့် စက်မှုလုပ်ငန်းသုံးစက်တစ်မျိုး ဖြစ်ပါသည်။" if is_mm else "An industrial machine that melts raw plastic or waste plastic scraps and cuts them into small, uniform, and manageable pellets.",
            "tip": "<b></b>" if is_mm else ""
        },
    ]

    for idx, st_data in enumerate(steps_data):
        col1, col2 = st.columns([1, 2], gap="medium")
        with col1:
            st.markdown(f"""
            <div style="border:3px solid {th['border']}; border-radius:20px; overflow:hidden; background:{th['card_bg']};">
                <img src="{st_data['img']}" 
                     style="width:100%; height:auto; display:block; object-fit:cover;">
                <div style="text-align:center; padding:0.5rem; color:{th['muted']}; font-size:0.8rem; background:{th['card_bg']};">
                    {st_data['title']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background:{th['card_bg']}; border:3px solid {th['accent']}; border-radius:20px; padding:1.5rem; height:100%; display:flex; flex-direction:column; justify-content:center;">
                <div style="font-size:1.2rem; font-weight:700; color:{th['accent']};">{st_data['title']}</div>
                <div style="margin-top:0.8rem; line-height:1.8;">{st_data['desc']}</div>
                <div style="margin-top:1rem; background:{th['bg']}; padding:0.8rem 1.2rem; border-radius:14px; border-left:4px solid {th['accent']};">{st_data['tip']}</div>
            </div>
            """, unsafe_allow_html=True)

        if idx < len(steps_data) - 1:
            st.markdown(f'<hr style="border-color:{th["border"]}; margin:1.5rem 0;">', unsafe_allow_html=True)

    st.markdown(f'<hr style="border-color:{th["border"]}; margin:2rem 0;">', unsafe_allow_html=True)

    # ---------- RESIN TYPES SECTION ----------
    resin_sec_title = "ပလတ်စတစ် အမျိုးအစားများ" if is_mm else "The Resin Types"
    st.markdown(f'<div class="section-title">{resin_sec_title}</div>', unsafe_allow_html=True)

    for cls, info in RECYCLABILITY.items():
        sym = RESIN_SYMBOLS.get(cls, "♹")
        color = COLORS.get(cls, "#5C8374")
        if is_mm:
            badge = '<span class="badge-recyclable">✓ ပြန်လည်အသုံးပြုနိုင်သည်</span>' if info["recyclable"] else '<span class="badge-non">✗ ပြန်လည်အသုံးပြု၍မရပါ</span>'
            common_hdr = "အသုံးများသည့် ပစ္စည်းများ:"
        else:
            badge = '<span class="badge-recyclable">✓ Recyclable</span>' if info["recyclable"] else '<span class="badge-non">✗ Non-recyclable</span>'
            common_hdr = "Common items:"

        with st.expander(f"{sym}  #{info['code']} · {cls} — {info['name_en']}"):
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.8rem; flex-wrap:wrap;">
                <div style="font-size:2.5rem; color:{color}">{sym}</div>
                {badge}
            </div>
            <div class="examples-text" style="margin-bottom:0.6rem;"><b>{common_hdr}</b> {info['examples']}</div>
            <div class="guidance-box">{LEARN_TIPS.get(cls, "")}</div>
            """, unsafe_allow_html=True)

    st.markdown(f'<hr style="border-color:{th["border"]}; margin:2rem 0;">', unsafe_allow_html=True)

    # ==========================================
    # ---------- PLASTIC RECYCLING QUIZ ----------
    # ==========================================
    quiz_title = "♻️ ပလတ်စတစ် ပြန်လည်အသုံးပြုရေး ဗဟုသုတ စစ်ဆေးခြင်း" if is_mm else "♻️ Plastic Recycling Quiz"
    quiz_sub   = "သင်၏ ပလတ်စတစ် ပြန်လည်အသုံးပြုရေး ဗဟုသုတကို စစ်ဆေးပါ!" if is_mm else "Test your plastic recycling knowledge!"
    st.markdown(f'<div class="section-title">{quiz_title}</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:{th["muted"]}; font-size:0.9rem; margin-bottom:1.2rem;">{quiz_sub}</p>', unsafe_allow_html=True)

    # --- Quiz Data (bilingual) ---
    QUIZ_EN = [
        {
            "q": "Which resin code is assigned to PET plastic?",
            "options": ["#1", "#2", "#4", "#5"],
            "answer": 0,
            "explain": "PET (Polyethylene Terephthalate) is identified by Resin Identification Code #1. It is the most common plastic used in drink bottles."
        },
        {
            "q": "Which of the following plastics is generally NOT recyclable through standard curbside programs?",
            "options": ["PET", "HDPE", "Polystyrene (PS)", "Polypropylene (PP)"],
            "answer": 2,
            "explain": "PS (Polystyrene / Styrofoam) is rarely accepted in standard curbside recycling because it is low-density and prone to contamination."
        },
        {
            "q": "What should you do before placing a plastic bottle in the recycling bin?",
            "options": ["Crush and leave it dirty", "Rinse it clean and keep the cap on", "Remove all labels and break it apart", "Freeze it first"],
            "answer": 1,
            "explain": "Rinsing removes food/liquid residue that can contaminate an entire recycling batch. Keeping the cap on is now recommended by most facilities."
        },
        {
            "q": "LDPE (Low-Density Polyethylene) carries which resin code?",
            "options": ["#2", "#3", "#4", "#6"],
            "answer": 2,
            "explain": "LDPE is assigned Resin Identification Code #4. It is commonly used for plastic bags, cling wrap, and bread bags."
        },
        {
            "q": "Which plastic type is widely used for milk jugs and detergent bottles?",
            "options": ["PET", "HDPE", "PS", "Others (#7)"],
            "answer": 1,
            "explain": "HDPE (High-Density Polyethylene, #2) is rigid and chemical-resistant, making it ideal for milk jugs, shampoo bottles, and detergent containers."
        },
        {
            "q": "Plastic bags and cling wrap are typically made from which material?",
            "options": ["PP", "HDPE", "LDPE", "PET"],
            "answer": 2,
            "explain": "LDPE (#4) is flexible and lightweight, making it the primary material for plastic bags, cling wrap, and squeeze bottles."
        },
        {
            "q": "What does 'wishcycling' mean?",
            "options": [
                "Recycling plastic efficiently at home",
                "Tossing non-recyclables into the recycling bin hoping they will be sorted",
                "Donating old plastics to charity",
                "Choosing recycled products at the shop"
            ],
            "answer": 1,
            "explain": "'Wishcycling' is the habit of putting items into recycling bins without knowing if they are actually recyclable, which can contaminate and ruin recyclable batches."
        },
        {
            "q": "Which plastic is microwave-safe and used for yogurt tubs and food containers?",
            "options": ["PET (#1)", "PS (#6)", "PP (#5)", "Others (#7)"],
            "answer": 2,
            "explain": "PP (Polypropylene, #5) has high heat tolerance, making it safe for microwave use and suitable for yogurt tubs, food storage containers, and bottle caps."
        },
        {
            "q": "Resin code #7 ('Others') refers to what?",
            "options": [
                "PVC plastics only",
                "Mixed or multi-layer plastics that don't fit codes #1-#6",
                "Biodegradable plastics only",
                "Glass and metal composites"
            ],
            "answer": 1,
            "explain": "Resin code #7 covers all plastics not classified under codes #1-#6, including multi-layer packaging and some bioplastics. These are generally not recyclable through standard programs."
        },
        {
            "q": "Which step in the recycling process involves melting shredded plastic into small uniform beads?",
            "options": ["Sorting", "Shredding", "Pelletizing", "Collection"],
            "answer": 2,
            "explain": "Pelletizing is the process of melting shredded plastic and forming it into small uniform pellets (nurdles), which manufacturers then use to make new plastic products."
        },
        {
            "q": "What percentage of global plastic waste is effectively recycled?",
            "options": ["Less than 10%", "About 25%", "About 50%", "More than 70%"],
            "answer": 0,
            "explain": "Globally, less than 10% of all plastic waste produced is effectively recycled. The rest ends up in landfills, incinerators, or the natural environment."
        },
        {
            "q": "Which resin code is used for Polypropylene (PP)?",
            "options": ["#3", "#4", "#5", "#6"],
            "answer": 2,
            "explain": "Polypropylene (PP) is assigned Resin Identification Code #5. It is one of the most versatile plastics, used in food containers, bottle caps, and straws."
        },
        {
            "q": "What is the first step in the plastic recycling process?",
            "options": ["Shredding", "Sorting", "Collection", "Pelletizing"],
            "answer": 2,
            "explain": "Collection is the very first step: plastic waste must be gathered from homes, businesses, and drop-off points before any sorting or processing can begin."
        },
        {
            "q": "Which property makes HDPE suitable for detergent and chemical bottles?",
            "options": ["It is transparent", "It is chemical-resistant", "It is flexible", "It is biodegradable"],
            "answer": 1,
            "explain": "HDPE is highly resistant to many solvents and chemicals, making it the ideal choice for household cleaning products, detergents, and industrial containers."
        },
        {
            "q": "Foam cups and packing peanuts are made from which plastic?",
            "options": ["LDPE", "PP", "Polystyrene (PS)", "PET"],
            "answer": 2,
            "explain": "Expanded Polystyrene (EPS), commonly called Styrofoam, is used for foam cups, takeout containers, and protective packing peanuts because of its lightweight insulating properties."
        },
        {
            "q": "Which step of recycling removes food residue and labels from plastics?",
            "options": ["Collection", "Sorting", "Cleaning", "Pelletizing"],
            "answer": 2,
            "explain": "The Cleaning step washes plastics to remove food residue, labels, glue, and dirt. Contaminated plastics can ruin an entire recycling batch if not cleaned properly."
        },
        {
            "q": "Bottle caps are typically made from which plastic?",
            "options": ["PET", "LDPE", "PP", "PS"],
            "answer": 2,
            "explain": "Most bottle caps are made from PP (Polypropylene, #5) because it is rigid, heat-resistant, and provides a good seal. Many recycling facilities now accept caps on bottles."
        },
        {
            "q": "What does 'PCR' stand for in sustainable packaging?",
            "options": ["Plastic Carbon Reduction", "Post-Consumer Recycled", "Primary Chemical Resin", "Processed Composite Resin"],
            "answer": 1,
            "explain": "'PCR' stands for Post-Consumer Recycled, meaning the plastic content was previously used by consumers and then collected, processed, and turned into new products."
        },
        {
            "q": "Which plastic is known for its high clarity and is often used in food jars and soda bottles?",
            "options": ["HDPE", "PET", "PP", "LDPE"],
            "answer": 1,
            "explain": "PET (#1) has excellent optical clarity and strong barrier properties against oxygen and CO2, making it perfect for soda bottles and food jars."
        },
        {
            "q": "What happens to plastic during the Shredding step of recycling?",
            "options": [
                "It is melted into pellets",
                "It is cleaned with water",
                "It is cut into small flakes",
                "It is sorted by color"
            ],
            "answer": 2,
            "explain": "During Shredding, clean plastics are mechanically cut or ground into small flakes or chips. This increases surface area and makes the next step (melting and pelletizing) much easier."
        },
        {
            "q": "Chip bags and multi-layer food pouches belong to which resin category?",
            "options": ["LDPE (#4)", "PP (#5)", "PS (#6)", "Others (#7)"],
            "answer": 3,
            "explain": "Chip bags and multi-layer pouches are classified as #7 (Others) because they are made from multiple bonded plastic layers that cannot be separated and recycled through standard programs."
        },
        {
            "q": "Which of these plastics is the MOST widely recycled globally?",
            "options": ["PS", "PET", "LDPE", "Others (#7)"],
            "answer": 1,
            "explain": "PET (#1) has the highest recycling rate of any plastic globally. It is accepted by nearly all curbside programs and is in high demand by manufacturers for making new bottles and fibers."
        },
        {
            "q": "Squeeze bottles, such as those for honey or ketchup, are usually made from which plastic?",
            "options": ["PET", "PS", "LDPE", "PP"],
            "answer": 2,
            "explain": "LDPE (#4) is flexible and soft, making it ideal for squeeze bottles for honey, ketchup, and condiments where the user needs to squeeze the container."
        },
        {
            "q": "What is the main environmental problem caused by Polystyrene (PS) waste?",
            "options": [
                "It produces toxic gas when recycled",
                "It breaks into tiny microplastics that persist in the environment",
                "It absorbs water and becomes heavier",
                "It reacts with soil and creates acid rain"
            ],
            "answer": 1,
            "explain": "PS easily breaks apart into tiny microplastic particles that are extremely difficult to clean up and persist in oceans, soil, and food chains for hundreds of years."
        },
        {
            "q": "The Resin Identification Code (RIC) system was originally created by which organization?",
            "options": [
                "United Nations Environment Programme (UNEP)",
                "Society of the Plastics Industry (SPI)",
                "World Health Organization (WHO)",
                "International Recycling Bureau (IRB)"
            ],
            "answer": 1,
            "explain": "The Resin Identification Code (RIC) system was originally established by the Society of the Plastics Industry (SPI) in 1988."
        },
        {
            "q": "Which plastic item is least likely to be accepted in a standard curbside recycling bin?",
            "options": ["PET water bottle", "HDPE milk jug", "Polystyrene foam cup", "PP food container"],
            "answer": 2,
            "explain": "Polystyrene foam cups are almost universally rejected by curbside recycling programs due to their low density, high contamination risk, and difficulty of cleaning food residue from their porous surface."
        },
        {
            "q": "What is the 'circular economy' concept in the context of plastics?",
            "options": [
                "Burning plastics to generate electricity",
                "Designing plastics to be reused, recycled, or composted, never wasted",
                "Using circular-shaped recycling bins",
                "Exporting plastic waste to other countries for processing"
            ],
            "answer": 1,
            "explain": "The circular economy aims to keep materials in use as long as possible through reuse, repair, and recycling, eliminating the concept of 'waste' by closing the production loop."
        },
        {
            "q": "What is the key benefit of sorting plastics by resin type before recycling?",
            "options": [
                "It makes plastics look cleaner",
                "Different plastics melt at different temperatures and cannot be mixed",
                "It reduces the weight of plastic waste",
                "It adds color to recycled plastics"
            ],
            "answer": 1,
            "explain": "Different plastic resins have different melting points and chemical structures. Mixing them produces weak, unusable material. Sorting by type ensures high-quality recycled output."
        },
        {
            "q": "Which plastic resin is commonly used to make PVC pipes?",
            "options": ["PET (#1)", "PVC (#3)", "LDPE (#4)", "PP (#5)"],
            "answer": 1,
            "explain": "PVC (Polyvinyl Chloride, #3) is rigid, durable, and resistant to water and chemicals, making it widely used for plumbing pipes, window frames, and flooring."
        },
        {
            "q": "What does 'upcycling' mean in the context of plastic waste?",
            "options": [
                "Sending plastics to a higher-tier landfill",
                "Converting waste plastics into products of higher value or quality",
                "Melting plastics at a higher temperature",
                "Recycling plastics more than twice"
            ],
            "answer": 1,
            "explain": "Upcycling converts discarded plastics into something of greater value or quality than the original, for example turning plastic bottles into clothing fabric or bags."
        },
    ]

    QUIZ_MM = [
        {
            "q": "PET ပလတ်စတစ်ရဲ့ Resin Code က ဘယ်နံပါတ်လဲ?",
            "options": ["#1", "#2", "#4", "#5"],
            "answer": 0,
            "explain": "PET (Polyethylene Terephthalate) ကို Resin Identification Code #1 ဖြင့် သတ်မှတ်ထားပါသည်။ ၎င်းသည် သောက်ရေဘူးများတွင် အများဆုံးအသုံးပြုသော ပလတ်စတစ်အမျိုးအစားဖြစ်သည်။"
        },
        {
            "q": "အောက်ပါ ပလတ်စတစ်တွေထဲမှာ ပုံမှန် Recycling Program နဲ့ ပြန်လည်အသုံးချလို့ မရတာ ဘယ်ဟာလဲ?",
            "options": ["PET", "HDPE", "ပေါ်လီစတိုရင်း (PS)", "ပေါ်လီပရိုပလင်း (PP)"],
            "answer": 2,
            "explain": "PS (Polystyrene / Styrofoam) ကို ပုံမှန် Recycling Program တွေမှာ လက်ခံတာရှားပါတယ်။ ဘာလို့လဲဆိုတော့ ပေါ့ပါးပြီး အညစ်အကြေးတွေ ကပ်ညှိ ညစ်ညမ်းလွယ်လို့ပါ။"
        },
        {
            "q": "ပလတ်စတစ်ဘူးကို အမှိုက်ပုံးထဲ မထည့်ခင် ဘာလုပ်သင့်လဲ?",
            "options": ["ဘူးကို ချိုးဖိပြီး ညစ်ပေနေသည့်အတိုင်းထားပါ", "ရေဆေးသန့်စင်ပြီး အဖုံးကို တပ်ထားပါ", "Label အားလုံးကို ဖယ်ပြီး အပိုင်းပိုင်း ခွဲပါ", "အရင်ဆုံး အေးခဲအောင်လုပ်ပါ"],
            "answer": 1,
            "explain": "ရေဆေးခြင်းဖြင့် ဘူးအတွင်းရှိ အစားအစာနှင့် အရည်အကြွင်းအကျန်များကို ဖယ်ရှားနိုင်ပြီး အမှိုက်ပုံး တစ်ခုလုံးကို ညစ်ညမ်းစေခြင်းမှ ကာကွယ်နိုင်ပါသည်။ အဖုံးကို ဖုံးကာသေချာစွန့်ပစ်ခြင်းကိုလည်း ယနေ့ခေတ်တွင် Recycling Facility အများစုက အကြံပြုထားပါသည်။"
        },
        {
            "q": "LDPE (Low-Density Polyethylene) သည် မည်သည့် Resin Code ကို သတ်မှတ်ထားသနည်း?",
            "options": ["#2", "#3", "#4", "#6"],
            "answer": 2,
            "explain": "LDPE ကို Resin Identification Code #4 ဖြင့် သတ်မှတ်ထားပါသည်။ ၎င်းကို ပလတ်စတစ်အိတ်များ၊ Cling Wrap (အစားအစာထုပ်ပိုးရန် ပလတ်စတစ်အလွှာ) နှင့် ပေါင်မုန့်အိတ်များတွင် အများဆုံးအသုံးပြုကြသည်။"
        },
        {
            "q": "နို့ဘူးများနှင့် ဆပ်ပြာရည်ဘူးများတွင် အများဆုံးအသုံးပြုသော ပလတ်စတစ်အမျိုးအစားမှာ မည်သည့်အမျိုးအစားဖြစ်သနည်း?",
            "options": ["PET", "HDPE", "PS", "Others (#7)"],
            "answer": 1,
            "explain": "HDPE (High-Density Polyethylene, #2) သည် ခိုင်ခံ့ပြီး ဓာတုပစ္စည်းများကို ခံနိုင်ရည်ရှိသောကြောင့် နို့ဘူးများ၊ Shampoo ဘူးများနှင့် ဆပ်ပြာရည်ဘူးများတွင် အသုံးပြုကြပါသည်။"
        },
        {
            "q": "ပလတ်စတစ်အိတ်များနှင့် Cling Wrap များကို ပုံမှန်အားဖြင့် မည်သည့်ပစ္စည်းဖြင့် ပြုလုပ်ထားသနည်း?",
            "options": ["PP", "HDPE", "LDPE", "PET"],
            "answer": 2,
            "explain": "“LDPE (#4) သည် ပျော့ပြောင်းပြီး ပေါ့ပါးသောကြောင့် ပလတ်စတစ်အိတ်များ၊ Cling Wrap များနှင့် ဖိညှစ်အသုံးပြုရသော ဘူးများတွင် အဓိကအသုံးပြုသော ပစ္စည်းဖြစ်သည်။"
        },
        {
            "q": "‘Wishcycling’ ဆိုတာ ဘာကိုဆိုလိုတာလဲ?",
            "options": ["အိမ်မှာ ပလတ်စတစ်များကို ထိရောက်စွာ ပြန်လည်အသုံးချခြင်း", "မပြန်လည်အသုံးချနိုင်သော ပစ္စည်းများကို ခွဲထုတ်ပေးလိမ့်မည်ဟု မျှော်လင့်ပြီး Recycling Bin ထဲသို့ ထည့်ခြင်း", "အသုံးမပြုတော့သော ပလတ်စတစ်များကို ပေးကမ်းပစ်ခြင်း", "ဆိုင်တွင် ပြန်လည်အသုံးပြုပြီးသော ပစ္စည်းများကို ရွေးချယ်ဝယ်ယူခြင်း"],
            "answer": 1,
            "explain": "“Wishcycling ဆိုတာ တကယ်တမ်း Recycle လုပ်လို့ရ၊ မရ မသေချာဘဲ ပစ္စည်းတွေကို Recycling Bin ထဲ ထည့်လိုက်တဲ့ အလေ့အထ ဖြစ်ပါတယ်။ ဒီလိုလုပ်ခြင်းကြောင့် Recycle လုပ်လို့ရတဲ့ ပစ္စည်းတွေကိုပါ ညစ်ညမ်းစေပြီး အမှိုက်ပုံး တစ်ခုလုံး ပျက်စီးသွားနိုင်ပါတယ်။”"
        },
        {
            "q": "ဒိန်ချဉ်ခွက်နဲ့ အစားအသောက်ထည့်တဲ့ ကွန်တိန်နာတွေမှာ အသုံးများပြီး မိုက်ခရိုဝေ့ဖ်အသုံးပြုရန် သင့်တော်တဲ့ ပလတ်စတစ်အမျိုးအစားက ဘာလဲ?",
            "options": ["PET (#1)", "PS (#6)", "PP (#5)", "Others (#7)"],
            "answer": 2,
            "explain": "PP (Polypropylene, #5) သည် အပူဒဏ်ခံနိုင်ရည်မြင့်မားသောကြောင့် မိုက်ခရိုဝေ့ဖ်တွင် အသုံးပြုရန် သင့်တော်ပြီး ဒိန်ချဉ်ခွက်များ၊ အစားအသောက်သိုလှောင်သည့် ကွန်တိန်နာများနှင့် ဗူးအဖုံးများတွင် အသုံးများပါသည်။"
        },
        {
            "q": "Resin Code #7 (‘Others’) ဆိုတာ ဘယ်လိုပလတ်စတစ်အမျိုးအစားတွေကို ရည်ညွှန်းတာလဲ?",
            "options": ["PVC ပလတ်စတစ်များသာ", "Code #1–#6 အတွင်း မပါဝင်သော ရောနှောထားသည့် သို့မဟုတ် အလွှာပေါင်းစုံပါဝင်သော ပလတ်စတစ်များ", "သဘာဝအလျောက် ပျက်စီးနိုင်သော ပလတ်စတစ်များသာ", "ဖန်နှင့် သတ္တုပေါင်းစပ်ပစ္စည်းများ"],
            "answer": 1,
            "explain": "Resin Code #7 သည် Code #1–#6 အတွင်း မပါဝင်သော ပလတ်စတစ်အမျိုးအစားများအားလုံး ကို ရည်ညွှန်းပြီး၊ အလွှာပေါင်းစုံပါဝင်သော ထုပ်ပိုးပစ္စည်းများနှင့် အချို့သော bioplastic များ လည်း ပါဝင်ပါသည်။ ယေဘုယျအားဖြင့် ထိုပစ္စည်းများကို ပုံမှန် recycling စနစ်များမှတစ်ဆင့် ပြန်လည်အသုံးပြုရန် ခက်ခဲပါသည်။"
        },
        {
            "q": "“ပြန်လည်အသုံးပြုခြင်းလုပ်ငန်းစဉ်မှာ ကြိတ်ချေထားတဲ့ ပလတ်စတစ်တွေကို အရည်ပျော်အောင်လုပ်ပြီး အရွယ်အစားတူညီတဲ့ ပလတ်စတစ်အစေ့လေးတွေ (beads/pellets) အဖြစ် ပြုလုပ်တဲ့အဆင့်က ဘာလဲ?”",
            "options": ["အမျိုးအစားခွဲခြားခြင်း(Sorting)", "အစိတ်စိတ်အမွှာမွှာ ကြိတ်ချေခြင်း(Shredding)", "ပလတ်စတစ်အစေ့များ ပြုလုပ်ခြင်း(Pelletizing)", "စုဆောင်းခြင်း(Collection)"],
            "answer": 2,
            "explain": "Pelletizing ဆိုသည်မှာ ကြိတ်ချေထားသော ပလတ်စတစ်များကို အရည်ပျော်အောင်ပြုလုပ်ပြီး အရွယ်အစားတူညီသော ပလတ်စတစ်အစေ့လေးများ (nurdles) အဖြစ် ပြုလုပ်သည့် လုပ်ငန်းစဉ်ဖြစ်ပြီး၊ ထိုပလတ်စတစ်အစေ့များကို ထုတ်လုပ်သူများက ပလတ်စတစ်ထုတ်ကုန်အသစ်များ ပြုလုပ်ရန် အသုံးပြုကြပါသည်။"
        },
        {
            "q": "ကမ္ဘာတစ်ဝန်းရှိ ပလတ်စတစ်အမှိုက်များထဲမှ ဘယ်လောက်ရာခိုင်နှုန်းကို ထိရောက်စွာ ပြန်လည်အသုံးပြုနိုင်သလဲ?",
            "options": ["10% ထက်နည်းသည်", "25% ခန့်", "50% ခန့်", "70% ကျော်"],
            "answer": 0,
            "explain": "ကမ္ဘာတစ်ဝန်းတွင် ထုတ်လုပ်သည့် ပလတ်စတစ်အမှိုက်အားလုံး၏ 10% အောက်သာ ထိရောက်စွာ ပြန်လည်အသုံးပြုနိုင်ပါသည်။ ကျန်ရှိသည့် ပလတ်စတစ်အမှိုက်များမှာ အမှိုက်ပုံများ၊ မီးရှို့စက်များ သို့မဟုတ် သဘာဝပတ်ဝန်းကျင်၊ ရေအောက်နှင့် မြေဆီလွှာ အတွင်းသို့ ရောက်ရှိသွားကြပါသည်။"
        },
        {
            "q": "Polypropylene (PP) အတွက် အသုံးပြုထားတဲ့ Resin Code က ဘယ်နံပါတ်လဲ",
            "options": ["#3", "#4", "#5", "#6"],
            "answer": 2,
            "explain": "Polypropylene (PP) ကို Resin Identification Code #5 ဖြင့် သတ်မှတ်ထားပါသည်။ ၎င်းသည် အမျိုးမျိုးသော အသုံးပြုမှုများရှိသည့် ပလတ်စတစ်အမျိုးအစားတစ်ခုဖြစ်ပြီး အစားအသောက်ထည့်သည့်ဗူးများ၊ ဗူးအဖုံးများနှင့် ပိုက်များ (straws) တွင် အသုံးများပါသည်။"
        },
        {
            "q": "ပလတ်စတစ်ကို ပြန်လည်ထုတ်လုပ်သည့်စက်ရုံများတွင် ပြန်လည်အသုံးပြုရန် လုပ်ဆောင်ခြင်းလုပ်ငန်းစဉ်ရဲ့ ပထမဆုံးအဆင့်က ဘာလဲ?",
            "options": ["ကြိတ်ခြင်း", "ခွဲခြမ်းခြင်း", "စုဆောင်းခြင်း", "ပလတ်စတစ်စေ့ ပြုလုပ်ခြင်း"],
            "answer": 2,
            "explain": "Collection သည် ပလတ်စတစ်ပြန်လည်အသုံးပြုခြင်းလုပ်ငန်းစဉ်၏ ပထမဆုံးအဆင့် ဖြစ်ပါသည်။ အမျိုးအစားခွဲခြားခြင်း သို့မဟုတ် ပြုပြင်ခြင်းမပြုမီ အိမ်များ၊ စီးပွားရေးလုပ်ငန်းများနှင့် စွန့်ပစ်ပစ္စည်းလက်ခံသည့်နေရာများမှ ပလတ်စတစ်အမှိုက်များကို စုဆောင်းရပါသည်။"
        },
        {
            "q": "HDPE ကို ဆပ်ပြာရည်နဲ့ ဓာတုပစ္စည်းထည့်တဲ့ ဗူးတွေမှာ အသုံးပြုရန် သင့်တော်စေတဲ့ ဂုဏ်သတ္တိက ဘာလဲ?",
            "options": ["ဖောက်ထွင်းမြင်ရသောကြောင့်", "ဓာတုပစ္စည်းများကို ခံနိုင်ရည်ရှိသောကြောင့်", "ပျော့ပျောင်းသောကြောင့်", "သဘာဝအလျောက် ပျက်စီးလွယ်သောကြောင့်"],
            "answer": 1,
            "explain": "HDPE သည် ဆေးရည်များနှင့် ဓာတုပစ္စည်းအများအပြားကို အလွန်ကောင်းမွန်စွာ ခံနိုင်ရည်ရှိသဖြင့် အိမ်သုံးသန့်စင်ဆေးရည်များ၊ ဆပ်ပြာရည်များနှင့် စက်မှုလုပ်ငန်းသုံး ကွန်တိန်နာများအတွက် အသင့်တော်ဆုံး ရွေးချယ်မှုတစ်ခု ဖြစ်သည်။"
        },
        {
            "q": "ဖောခွက်တွေ ထုပ်ပိုးရာမှာသုံးတဲ့ ဖော့စေ့လေးတွေကို ဘယ်လိုပလတ်စတစ်အမျိုးအစားနဲ့ ပြုလုပ်ထားသလဲ?",
            "options": ["LDPE", "PP", "PS", "PET"],
            "answer": 2,
            "explain": "Expanded Polystyrene (EPS) ကို အများအားဖြင့် Styrofoam လို့ခေါ်ကြပါတယ်။ ၎င်းကို ပေါ့ပါးပြီး အပူကာကွယ်နိုင်တဲ့ ဂုဏ်သတ္တိရှိတာကြောင့် ဖော့ခွက်တွေ၊ အစားအစာထည့်ယူသွားတဲ့ ဘူးတွေ၊ ပစ္စည်းတွေကို ထုပ်ပိုးကာကွယ်ရာမှာ အသုံးပြုတဲ့ ဖော့စေ့လေးတွေ ပြုလုပ်ရာမှာ အသုံးများပါတယ်။"
        },
        {
            "q": "ပလတ်စတစ်များမှ အစားအစာ အကြွင်းအကျန်နှင့် တံဆိပ်များကို ဖယ်ရှားသည့် ပြန်လည်အသုံးပြုခြင်း၏ အဆင့်မှာ အဘယ်အဆင့်နည်း?",
            "options": ["စုဆောင်းခြင်း", "ခွဲခြားခြင်း", "သန့်စင်ဆေးကြောခြင်း", "ပလတ်စတစ်စေ့ပြုလုပ်ခြင်း"],
            "answer": 2,
            "explain": "သန့်စင်ဆေးကြောခြင်းအဆင့်တွင် ပလတ်စတစ်များကို ရေဆေးခြင်းဖြင့် အစားအစာအကြွင်းအကျန်များ၊ တံဆိပ်ကပ်စက္ကူများ၊ ကော်များနှင့် အညစ်အကြေးများကို ဖယ်ရှားပေးသည်။ ညစ်ပတ်နေသော ပလတ်စတစ်များကို စနစ်တကျ မသန့်စင်ဆေးကြောပါက ပြန်လည်အသုံးပြုသည့် လုပ်ငန်းစဥ်တစ်ခုလုံးကိုပင် ပျက်စီးစေနိုင်သည်။"
        },
        {
            "q": "ပုလင်းအဖုံးများကို ပုံမှန်အားဖြင့် ဘယ်ပလတ်စတစ်အမျိုးအစားနဲ့ ပြုလုပ်ထားလဲ?",
            "options": ["PET", "LDPE", "PP", "PS"],
            "answer": 2,
            "explain": "ပုလင်းအဖုံးအများစုကို PP (Polypropylene, #5) ဖြင့် ပြုလုပ်ထားလေ့ရှိပြီး အကြောင်းမှာ ၎င်းပလတ်စတစ်သည် မာကျောခိုင်ခံ့ခြင်း၊ အပူဒဏ်ခံနိုင်ခြင်းနှင့် ကောင်းမွန်စွာ အလုံပိတ်နိုင်သော ဂုဏ်သတ္တိရှိသောကြောင့်ဖြစ်သည်။ ယနေ့အခါတွင် ပြန်လည်အသုံးပြုရေး စက်ရုံအများအပြားသည် ပုလင်းတွင် အဖုံးပါရှိသည့်အတိုင်း လက်ခံလျက်ရှိသည်။"
        },
        {
            "q": "ရေရှည်ခံပြီး သဘာဝပတ်ဝန်းကျင်နဲ့ လိုက်ဖက်တဲ့ ထုပ်ပိုးမှု 'PCR' ဆိုတာ ဘာကိုခေါ်တာလဲ?",
            "options": ["ပလတ်စတစ် ကာဗွန်လျှော့ချရေး", "စားသုံးပြီးနောက် ပြန်လည်အသုံးပြုထားသော ပစ္စည်း", "အခြေခံ ဓာတုဗေဒ ပလတ်စတစ်စေး", "ပြုပြင်ထားသော ပေါင်းစပ်ပလတ်စတစ်စေး"],
            "answer": 1,
            "explain": "'PCR' သည် Post-Consumer Recycled ကို ရည်ညွှန်းပြီး စားသုံးသူများ အသုံးပြုပြီးဖြစ်သော ပလတ်စတစ်ပါဝင်ပစ္စည်းများကို စုဆောင်း၍ ပြုပြင်ပြီးနောက် ထုတ်ကုန်အသစ်များအဖြစ် ပြန်လည်ထုတ်လုပ်ထားခြင်းကို ဆိုလိုသည်။"
        },
        {
            "q": "ကြည်လင်ရှင်းလင်းမှုမြင့်မားပြီး မုန့်ဗူးများနှင့် ဆိုဒါပုလင်းများတွင် မကြာခဏ အသုံးပြုသည့် ပလတ်စတစ်အမျိုးအစားက ဘာလဲ?",
            "options": ["HDPE", "PET", "PP", "LDPE"],
            "answer": 1,
            "explain": "PET (#1) သည် အလွန်ကောင်းမွန်သော အလင်းပေါက်ရှင်းလင်းမှု ဂုဏ်သတ္တိနှင့် အောက်ဆီဂျင်နှင့် ကာဗွန်ဒိုင်အောက်ဆိုဒ်(CO2) ကို ကောင်းစွာ အကာအကွယ်ပေးနိုင်သော စွမ်းရည်တို့ ရှိသည့်အတွက် ဆိုဒါပုလင်းများနှင့် အစားအစာဖန်ဗူးများအတွက် အလွန်သင့်တော်သည်။"
        },
        {
            "q": "ပလတ်စတစ်ကို ပြန်လည်အသုံးပြုခြင်း၏ ကြိတ်ခွဲခြင်းအဆင့် (Shredding step) တွင် မည်သို့ဖြစ်သွားသနည်း။",
            "options": ["အစေ့များအဖြစ် အရည်ကျိုသည်","ရေဖြင့် ဆေးကြောသည်","အစအနသေးသေးလေးများအဖြစ် ဖြတ်တောက်သည်","အရောင်အလိုက် ခွဲခြားသည်"],
            "answer": 2,
            "explain": "ကြိတ်ခွဲခြင်းအဆင့်တွင် သန့်စင်ထားသော ပလတ်စတစ်များကို စက်ဖြင့် ဖြတ်တောက်၍ သို့မဟုတ် ကြိတ်ခွဲ၍ အစအနသေးငယ်များ သို့မဟုတ် အပိုင်းအစများအဖြစ် ပြောင်းလဲသည်။"
        },
        {
            "q": "အာလူးကြော်အိတ်များနှင့် အလွှာပေါင်းစုံ ပါဝင်သော အစားအစာထုပ်ပိုးအိတ်များသည် မည်သည့် resin နံပါတ်အမျိုးအစားတွင် ပါဝင်သနည်း။",
            "options": ["LDPE (#4)", "PP (#5)", "PS (#6)", "Others (#7)"],
            "answer": 3,
            "explain": "အာလူးကြော်အိတ်များနှင့် အလွှာပေါင်းစုံ ပါဝင်သော ထုပ်ပိုးအိတ်များကို #7 (အခြား) အမျိုးအစားအဖြစ် သတ်မှတ်သည်။ အကြောင်းမှာ ၎င်းတို့သည် ခွဲထုတ်၍မရသော ပလတ်စတစ်အလွှာများစွာဖြင့် ပေါင်းစပ်ပြုလုပ်ထားသဖြင့် ပုံမှန် ပြန်လည်အသုံးပြုရေး လုပ်ငန်းစဉ်များဖြင့် ပြန်လည်အသုံးပြုနိုင်ခြင်း မရှိပေ။"
        },
        {
            "q": "ဤပလတ်စတစ်များအနက် မည်သည့်အမျိုးအစားသည် ကမ္ဘာတစ်ဝန်းတွင် အကျယ်ပြန့်ဆုံး ပြန်လည်အသုံးပြုခံရသနည်း။",
            "options": ["PS", "PET", "LDPE", "Others (#7)"],
            "answer": 1,
            "explain": "PET (#1) သည် ကမ္ဘာတစ်ဝန်းရှိ ပလတ်စတစ်အားလုံးတွင် ပြန်လည်အသုံးပြုနှုန်း အမြင့်မားဆုံးဖြစ်သည်။ ၎င်းကို အိမ်တွင်းမှ စွန့်ပစ်ပစ္စည်းစုဆောင်းရေး အစီအစဉ်အားလုံးနီးပါးတွင် လက်ခံကြပြီး ပုလင်းအသစ်များနှင့် အမျှင်များထုတ်လုပ်ရန်အတွက် ထုတ်လုပ်သူများ၏ ဝယ်လိုအား မြင့်မားလျက်ရှိသည်။"
        },
        {
            "q": "ပျားရည် သို့မဟုတ် ငရုပ်ချဥ်ကဲ့သို့သော ညှစ်ထုတ်ရသည့်ပုလင်းများကို များသောအားဖြင့် မည်သည့် ပလတ်စတစ်အမျိုးအစားဖြင့် ပြုလုပ်ထားသနည်း။",
            "options": ["PET", "PS", "LDPE", "PP"],
            "answer": 2,
            "explain": "LDPE (#4) သည် ပျော့ပျောင်းကာ ကွေးညွှတ်နိုင်သော ဂုဏ်သတ္တိရှိသဖြင့် အသုံးပြုသူမှ ပုလင်းအား ညှစ်ကိုင်ရသော ကော်ဗူး၊ ပျားရည်ပုလင်း၊ ငရုပ်ချဥ်ပုလင်း ကဲ့သို့သော ညှစ်ထုတ်ရသည့် ပုလင်းများတွင် အသုံးပြုရန် အကောင်းဆုံးဖြစ်သည်။"
        },
        {
            "q": "Polystyrene (PS) စွန့်ပစ်ပစ္စည်းကြောင့် ဖြစ်ပေါ်လာသော အဓိက သဘာဝပတ်ဝန်းကျင်ဆိုင်ရာ ပြဿနာမှာ အဘယ်နည်း?",
            "options": ["ပြန်လည်အသုံးပြုသည့်အခါ အဆိပ်ဓာတ်ငွေ့များ ထုတ်လွှတ်သည်","ပတ်ဝန်းကျင်တွင် ကြာရှည်တည်ရှိနေသော မိုက်ခရိုပလတ်စတစ် အမှုန်ငယ်များအဖြစ် ကွဲထွက်သွားသည်","ရေကိုစုပ်ယူပြီး ပိုမိုလေးလံလာသည်","မြေဆီလွှာနှင့် ဓာတ်ပြုကာ အက်ဆစ်မိုးရေကို ဖြစ်ပေါ်စေသည်"],
            "answer": 1,
            "explain": "PS သည် အလွယ်တကူ မိုက်ခရိုပလတ်စတစ်အမှုန်ငယ်များအဖြစ်သို့ ပြိုကွဲသွားပြီး ယင်းတို့ကို သန့်စင်ရှင်းလင်းရန် အလွန်ခက်ခဲကာ သမုဒ္ဒရာများ၊ မြေဆီလွှာနှင့် ဇီဝဗေဒဆိုင်ရာ အစာကွင်းဆက်များတွင် နှစ်ပေါင်းရာနှင့်ချီ၍ တည်ရှိနေသည်။"
        },
        {
            "q": "Resin Identification Code (RIC) စနစ်​ကို မူလ မည်သည့်​ အဖွဲ့အစည်းမှ သတ်မှတ်ခဲ့သနည်း?",
            "options": ["United Nations Environment Programme (UNEP)", "Society of the Plastics Industry (SPI)", "World Health Organization (WHO)", "International Recycling Bureau (IRB)"],
            "answer": 1,
            "explain": "Resin Identification Code (RIC) စနစ်​ကို ၁၉၈၈ ခုနှစ်တွင် Society of the Plastics Industry (SPI) မှ စတင်တီထွင်ခဲ့သည်။ ၂၀၀၈ ခုနှစ်တွင် ၎င်းစနစ်၏ စီမံခန့်ခွဲမှုကို ASTM နိုင်ငံတကာ စံချိန်စံညွှန်းအဖွဲ့ထံ လွှဲပြောင်းပေးအပ်ခဲ့ပြီး ယခုအခါ ASTM D7611 စံသတ်မှတ်ချက်အဖြစ် ဆက်လက်ထိန်းသိမ်းထားသည်။"
        },
        {
            "q": "ပြန်လည်အသုံးပြုရန် ခွဲခြားထားသည့်အမှိုက်ပုံးတွင် လက်ခံနိုင်ခြေ အနည်းဆုံး ပလတ်စတစ်ပစ္စည်းမှာ မည်သည့်အမျိုးအစားနည်း။",
            "options": ["PET ရေဘူး", "HDPE နို့ဘူး", " PS ဖော့ခွက်", "PP အစားအသောက်ဘူး"],
            "answer": 2,
            "explain": "Polystyrene ဖော့ခွက်များသည် သိပ်သည်းဆနည်းပါးခြင်း၊ ညစ်ညမ်းမှုအန္တရာယ် မြင့်မားခြင်းနှင့် ချွေးပေါက်များရှိသော မျက်နှာပြင်မှ အစားအစာအကြွင်းအကျန်များကို သန့်စင်ရန် ခက်ခဲခြင်းတို့ကြောင့် ပြန်လည်အသုံးပြုသည့် အမှိုက်ပုံးများတွင် လက်မခံပေ။"
        },
        {
            "q": "ပလတ်စတစ်အသုံးပြုခြင်းအောက်က ‘Circular Economy’ (စက်ဝိုင်းပုံစံ စီးပွားရေးစနစ်) ဆိုတာဘာကိုဆိုလိုတာလဲ?",
            "options": ["ပလတ်စတစ်များကို မီးရှို့၍ လျှပ်စစ်ဓာတ်အားထုတ်လုပ်ခြင်း","ပလတ်စတစ်များကို ပြန်လည်အသုံးပြုခြင်း သို့မဟုတ် မြေဆွေးပြုလုပ်နိုင်ရန် ဒီဇိုင်းထုတ်ခြင်း သို့မဟုတ် အလေအလွင့်အမှိုက်မရှိစေရန် စွန့်ပစ်အမှိုက်ကို ပြန်လည်ထုတ်လုပ်ရန်အသုံးပြုခြင်း","စက်ဝိုင်းပုံသဏ္ဍာန် ပြန်လည်အသုံးပြုရေးအမှိုက်ပုံးများကို အသုံးပြုခြင်း","ပလတ်စတစ်စွန့်ပစ်ပစ္စည်းများကို အခြားနိုင်ငံများသို့ ပြန်လည်အသုံးပြုရန်အတွက် တင်ပို့ခြင်း"],
            "answer": 1,
            "explain": "စက်ဝိုင်းပုံစံ စီးပွားရေးဆိုတာ ပစ္စည်းတွေကို ပြန်သုံးတာ၊ ပြင်တာ၊ ပြန်လည်အသုံးပြုတာတွေနဲ့ တတ်နိုင်သမျှ ကြာကြာသုံးနိုင်အောင် ရည်ရွယ်ထားတာပါ။ ထုတ်လုပ်မှုကွင်းဆက်ကို ပိတ်လိုက်ခြင်းအားဖြင့် 'အမှိုက်' ဆိုတာကိုယ်တိုင် မရှိတော့အောင် ဖန်တီးတာပဲဖြစ်ပါတယ်။"
        },
        {
            "q": "ပြန်လည်အသုံးပြုခြင်းမပြုမီ ပလတ်စတစ်များကို resin အမျိုးအစားအလိုက် ခွဲခြားခြင်းရဲ့ အဓိကအကျိုးကျေးဇူးကဘာလဲ?",
            "options": ["ပလတ်စတစ်များကို ပိုမိုသန့်ရှင်းစေသည်","မတူညီသော ပလတ်စတစ်များသည် မတူညီသော အပူချိန်တွင် အရည်ပျော်ကြပြီး ရောနှောခြင်းမဖြစ်တော့ပါ","ပလတ်စတစ်စွန့်ပစ်ပစ္စည်း၏ အလေးချိန်ကို လျှော့ချပေးသည်","ပြန်လည်အသုံးပြုထားသော ပလတ်စတစ်များသို့ အရောင်ထည့်ပေးသည်"],
            "answer": 1,
            "explain": "မတူညီသော ပလတ်စတစ်အမျိုးအစာများတွင် မတူညီသော အရည်ပျော်မှတ်များနှင့် ဓာတုဗေဒဆိုင်ရာ တည်ဆောက်ပုံများ ရှိကြသည်။ အမျိုးအစားအလိုက် ခွဲခြားခြင်းသည် အရည်အသွေးမြင့်မားသော ပြန်လည်အသုံးပြုထားသည့် ထုတ်ကုန်ကို ရရှိစေသည်။"
        },
        {
            "q": "စျေးဝယ်အိတ် အများစုကို ဘယ် ပလတ်စတစ်အမျိုးအစားနဲ့ ထုတ်လုပ်ထားတာလဲ?",
            "options": ["PET (#1)", "PVC (#3)", "LDPE (#4)", "PP (#5)"],
            "answer": 2,
            "explain": "LDPE (#4)"
        },
        {
            "q": "ပလတ်စတစ်စွန့်ပစ်ပစ္စည်းများနှင့် ပတ်သက်၍ 'upcycling' ဆိုသည်မှာ အဘယ်ကို ဆိုလိုသနည်း။",
            "options": ["ပလတ်စတစ်များကို အဆင့်မြင့် အမှိုက်ပုံသို့ ပို့ခြင်း","စွန့်ပစ်ပလတ်စတစ်များကို တန်ဖိုးပိုမိုမြင့်မားသော သို့မဟုတ် အရည်အသွေးပိုမိုကောင်းမွန်သော ထုတ်ကုန်များအဖြစ် ပြောင်းလဲခြင်း","ပလတ်စတစ်များကို အပူချိန်ပိုမိုမြင့်မားစွာ အရည်ကျိုခြင်း","ပလတ်စတစ်များကို နှစ်ကြိမ်ထက်ပို၍ ပြန်လည်အသုံးပြုခြင်း"],
            "answer": 1,
            "explain": "Upcycling ဆိုသည်မှာ စွန့်ပစ်ထားသော ပလတ်စတစ်များကို မူလပစ္စည်းထက် တန်ဖိုးပိုကြီးသော သို့မဟုတ် အရည်အသွေးပိုကောင်းသော ပစ္စည်းအဖြစ် ပြောင်းလဲခြင်းဖြစ်သည်။ ဥပမာ – ပလတ်စတစ်ပုလင်းများကို အထည်အမျှင် သို့မဟုတ် အိတ်များအဖြစ် ပြောင်းလဲခြင်းဖြစ်သည်။"
        },
    ]

    QUIZ_DATA = QUIZ_MM if is_mm else QUIZ_EN

    # --- Session State for Quiz ---
    if "quiz_index" not in st.session_state:
        st.session_state.quiz_index = 0
    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0
    if "quiz_answered" not in st.session_state:
        st.session_state.quiz_answered = False
    if "quiz_selected" not in st.session_state:
        st.session_state.quiz_selected = None
    if "quiz_done" not in st.session_state:
        st.session_state.quiz_done = False
    if "quiz_history" not in st.session_state:
        st.session_state.quiz_history = []  # list of (index, score, answered, selected)

    total_q = len(QUIZ_DATA)
    idx = st.session_state.quiz_index

    # --- Restart Quiz ---
    def restart_quiz():
        st.session_state.quiz_index = 0
        st.session_state.quiz_score = 0
        st.session_state.quiz_answered = False
        st.session_state.quiz_selected = None
        st.session_state.quiz_done = False
        st.session_state.quiz_history = []

    # --- Quiz Complete Screen ---
    if st.session_state.quiz_done:
        score = st.session_state.quiz_score
        pct = int(score / total_q * 100)

        if pct >= 80:
            grade_emoji = "🏆"
            grade_color = "#06D6A0"
            grade_msg_en = "Excellent! You're a Recycling Champion!"
            grade_msg_mm = "အလွန်ကောင်းသည်! သင်သည် ပြန်လည်အသုံးပြုရေး ချန်ပီယံဖြစ်သည်!"
        elif pct >= 50:
            grade_emoji = "🌱"
            grade_color = "#FFD166"
            grade_msg_en = "Good effort! Keep learning about recycling."
            grade_msg_mm = "ကောင်းသည်! ဆက်လက် လေ့လာပါ။"
        else:
            grade_emoji = "♻️"
            grade_color = "#EF476F"
            grade_msg_en = "Keep going! Review the Resin Types section above."
            grade_msg_mm = "ဆက်ကြိုးစားပါ! အပေါ်ရှိ ပလတ်စတစ် အမျိုးအစားများ ကဏ္ဍကို ပြန်လည် ဖတ်ရှုပါ။"

        grade_msg = grade_msg_mm if is_mm else grade_msg_en
        score_lbl = f"မေးခွန်း {total_q} ခုအနက် {score} ခု မှန်ကန်သည်" if is_mm else f"You scored {score} out of {total_q}"
        restart_lbl = "🔄 ထပ်မံကစားမည်" if is_mm else "🔄 Try Again"

        st.markdown(f"""
        <div style="background:{th['card_bg']}; border:3px solid {grade_color}; border-radius:24px;
                    padding:2.5rem; text-align:center; margin:1rem 0;
                    box-shadow: 0 8px 24px {grade_color}33;">
            <div style="font-size:4rem; margin-bottom:0.5rem;">{grade_emoji}</div>
            <div style="font-size:2rem; font-weight:800; color:{grade_color}; margin-bottom:0.3rem;">{pct}%</div>
            <div style="font-size:1rem; font-weight:600; color:{th['text']}; margin-bottom:0.5rem;">{score_lbl}</div>
            <div style="font-size:0.95rem; color:{th['muted']};">{grade_msg}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(restart_lbl, key="quiz_restart_btn", use_container_width=True):
            restart_quiz()
            st.rerun()
        return

    # --- Progress Bar ---
    progress_pct = idx / total_q
    progress_label = f"မေးခွန်း {idx + 1} / {total_q}" if is_mm else f"Question {idx + 1} of {total_q}"
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
        <span style="font-size:0.85rem; color:{th['muted']}; font-weight:600;">{progress_label}</span>
        <span style="font-size:0.85rem; color:{th['accent']}; font-weight:700;">
            {'မှတ်နှုန်း' if is_mm else 'Score'}: {st.session_state.quiz_score}
        </span>
    </div>
    <div style="background:{th['border']}; border-radius:8px; height:8px; margin-bottom:1.5rem; overflow:hidden;">
        <div style="background:linear-gradient(90deg, {th['accent']}, {th['accent2']}); height:100%;
                    width:{int(progress_pct * 100)}%; border-radius:8px; transition:width 0.4s ease;"></div>
    </div>
    """, unsafe_allow_html=True)

    # --- Current Question ---
    q_data = QUIZ_DATA[idx]

    st.markdown(f"""
    <div style="background:{th['card_bg']}; border:2px solid {th['border']}; border-radius:20px;
                padding:1.8rem; margin-bottom:1rem;
                box-shadow:0 4px 16px rgba(6,214,160,0.08);">
        <div style="font-size:1.05rem; font-weight:700; color:{th['text']}; line-height:1.7;">
            {q_data['q']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Answer Options (2x2 card grid) ---
    answered  = st.session_state.quiz_answered
    selected  = st.session_state.quiz_selected
    correct_i = q_data["answer"]
    OPT_LABELS = ["A", "B", "C", "D"]

    col_top_l, col_top_r = st.columns(2, gap="small")
    col_bot_l, col_bot_r = st.columns(2, gap="small")
    opt_cols = [col_top_l, col_top_r, col_bot_l, col_bot_r]

    for opt_i, (opt_text, col) in enumerate(zip(q_data["options"], opt_cols)):
        label_letter = OPT_LABELS[opt_i]

        # Determine card colours based on state
        if answered:
            if opt_i == correct_i:
                border_c = "#06D6A0"
                bg_c     = "#06D6A020"
                lbl_bg   = "#06D6A0"
                lbl_fg   = "#FFFFFF"
                icon     = "✓"
            elif opt_i == selected:
                border_c = "#EF476F"
                bg_c     = "#EF476F18"
                lbl_bg   = "#EF476F"
                lbl_fg   = "#FFFFFF"
                icon     = "✗"
            else:
                border_c = th["border"]
                bg_c     = th["card_bg"]
                lbl_bg   = th["border"]
                lbl_fg   = th["muted"]
                icon     = label_letter
        else:
            border_c = th["border"]
            bg_c     = th["card_bg"]
            lbl_bg   = th["accent"] + "33"
            lbl_fg   = th["accent"]
            icon     = label_letter

        with col:
            # Render a styled card via HTML for visuals
            st.markdown(f"""
            <div style="background:{bg_c}; border:2px solid {border_c}; border-radius:16px;
                        padding:0.75rem 1rem; display:flex; align-items:flex-start; gap:0.7rem;
                        min-height:64px; margin-bottom:0.1rem;">
                <div style="min-width:28px; height:28px; border-radius:8px;
                            background:{lbl_bg}; color:{lbl_fg};
                            font-weight:800; font-size:0.85rem;
                            display:flex; align-items:center; justify-content:center;
                            flex-shrink:0;">{icon}</div>
                <div style="font-size:0.88rem; font-weight:600; color:{th['text'] if not answered or opt_i in [correct_i, selected] else th['muted']};
                            line-height:1.5; padding-top:0.15rem;">{opt_text}</div>
            </div>
            """, unsafe_allow_html=True)

            # Invisible click button overlaid — shown only when not answered
            if not answered:
                if st.button(f"{label_letter}", key=f"quiz_opt_{idx}_{opt_i}",
                             use_container_width=True):
                    st.session_state.quiz_answered = True
                    st.session_state.quiz_selected = opt_i
                    if opt_i == correct_i:
                        st.session_state.quiz_score += 1
                    st.rerun()

    # --- Explanation Box (shown after answering) ---
    if st.session_state.quiz_answered:
        sel_i       = st.session_state.quiz_selected
        correct_txt = q_data["options"][correct_i]

        if sel_i == correct_i:
            fb_emoji = ""
            fb_color = "#06D6A0"
            fb_lbl   = "မှန်ကန်သည်!" if is_mm else "Correct!"
        else:
            fb_emoji  = ""
            fb_color  = "#FFD166"
            c_prefix  = "မှန်ကန်သောအဖြေ —" if is_mm else "Correct answer:"
            fb_lbl    = f"မမှန်ကန်ပါ — {c_prefix} {correct_txt}" if is_mm else f"Incorrect — {c_prefix} {correct_txt}"

        st.markdown(f"""
        <div style="background:{fb_color}15; border-left:4px solid {fb_color}; border-radius:0 14px 14px 0;
                    padding:0.9rem 1.3rem; margin-top:1rem;">
            <div style="font-weight:700; color:{fb_color}; margin-bottom:0.35rem; font-size:0.95rem;">
                {fb_emoji} {fb_lbl}
            </div>
            <div style="font-size:0.88rem; color:{th['text']}; line-height:1.8;">{q_data['explain']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:0.8rem;'></div>", unsafe_allow_html=True)

        next_lbl   = "နောက်မေးခွန်း ➜" if is_mm else "Next Question ➜"
        finish_lbl = "ရလဒ်ကြည့်ရှုမည် 🏆" if is_mm else "See Results 🏆"
        prev_lbl   = "← ရှေ့မေးခွန်း" if is_mm else "← Previous"
        btn_text   = finish_lbl if idx >= total_q - 1 else next_lbl

        nav_col1, nav_col2 = st.columns([1, 2], gap="small")

        with nav_col1:
            has_history = len(st.session_state.quiz_history) > 0
            if st.button(prev_lbl, key=f"quiz_prev_{idx}",
                         use_container_width=True,
                         disabled=not has_history):
                # Restore previous state
                prev = st.session_state.quiz_history.pop()
                st.session_state.quiz_index    = prev["index"]
                st.session_state.quiz_score    = prev["score"]
                st.session_state.quiz_answered = prev["answered"]
                st.session_state.quiz_selected = prev["selected"]
                st.rerun()

        with nav_col2:
            if st.button(btn_text, key=f"quiz_next_{idx}",
                         use_container_width=True, type="primary"):
                # Save current state to history before moving forward
                st.session_state.quiz_history.append({
                    "index":    idx,
                    "score":    st.session_state.quiz_score
                              - (1 if st.session_state.quiz_selected == correct_i else 0),
                    "answered": True,
                    "selected": st.session_state.quiz_selected
                })
                if idx >= total_q - 1:
                    st.session_state.quiz_done = True
                else:
                    st.session_state.quiz_index += 1
                    st.session_state.quiz_answered = False
                    st.session_state.quiz_selected = None
                st.rerun()

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown('<div class="sidebar-logo">♻ EcoSort</div>', unsafe_allow_html=True)
    st.markdown("---")

    nav_classifier = "ခွဲခြားစစ်ဆေးရန်" if is_mm else "Classifier"
    nav_dashboard = "ဒက်ရှ်ဘုတ်" if is_mm else "Dashboard"
    nav_learn = "လေ့လာရန်" if is_mm else "Learn"
    nav_about = "အကြောင်းအရာ" if is_mm else "About Us"

    _pages = [
        ("Classifier", "", nav_classifier),
        ("Dashboard", "", nav_dashboard),
        ("Learn", "", nav_learn),
        ("About", "", nav_about),
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
    dark_label = "🌙 Dark mode" if is_mm else "🌙 Dark mode"
    dark = st.toggle(dark_label, value=st.session_state.dark_mode)
    if dark != st.session_state.dark_mode:
        st.session_state.dark_mode = dark
        st.rerun()

    # ===== LANGUAGE SWITCHER =====
    st.markdown("---")
    lang_header = "ဘာသာစကား" if is_mm else "Language"
    st.markdown(f"<div style='font-weight:600; font-size:0.85rem; margin-bottom:0.4rem;'>{lang_header}</div>", unsafe_allow_html=True)
    _col_l1, _col_l2 = st.columns(2)
    with _col_l1:
        if st.button("English", key="btn_lang_en", use_container_width=True, type="primary" if st.session_state.lang == "en" else "secondary"):
            st.session_state.lang = "en"
            st.rerun()
    with _col_l2:
        if st.button("မြန်မာ", key="btn_lang_mm", use_container_width=True, type="primary" if st.session_state.lang == "mm" else "secondary"):
            st.session_state.lang = "mm"
            st.rerun()
        
    # ===== Sidebar Footer =====
    st.markdown("---")
    if is_mm:
        st.markdown("""
        <div style="text-align: center; padding: 0.5rem 0; color: #8D99AE; font-size: 0.65rem; opacity: 0.7;">
            ♻️ EcoSort · AI-Powered Plastic Recycling Assistant<br>
            © 2026 Developed by Zin Wut Yee Zaw (UCSPyay)<br>
            Supervisor: Daw Khin Aye San
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 0.5rem 0; color: #8D99AE; font-size: 0.65rem; opacity: 0.7;">
            ♻️ EcoSort · AI-Powered Plastic Recycling Assistant<br>
            © 2026 Developed by Zin Wut Yee Zaw (UCSPyay)<br>
            Supervisor: Daw Khin Aye San
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PAGE ROUTING CONTROLLER
# ==========================================
if st.session_state.page == "About":
    render_about_page(st.session_state.lang)
    st.stop()

if st.session_state.page == "Dashboard":
    render_dashboard_page(st.session_state.lang)
    st.stop()

if st.session_state.page == "Learn":
    render_learn_page(st.session_state.lang)
    st.stop()

# ==========================================
# MAIN PAGE VIEW: CLASSIFIER
# ==========================================
main_title = "♻ EcoSort"
main_subtitle = "အေအိုင် · ပလတ်စတစ် ခွဲခြားစနစ် · ပြန်လည်အသုံးပြုမှု လမ်းညွှန်" if is_mm else "AI · Plastic Classifier · Recycling Guide"

st.markdown(f"""
<div class="eco-header">
    <div class="eco-title">{main_title}</div>
    <div class="eco-subtitle">{main_subtitle}</div>
</div>
""", unsafe_allow_html=True)

expander_hdr = "အသုံးပြုနိုင်သော အမျိုးအစားများနှင့် အသုံးပြုနည်း" if is_mm else "Supported Classes & How to Use"
with st.expander(expander_hdr, expanded=False):
    chip_html = "".join(
        f'<span class="class-chip">{RESIN_SYMBOLS.get(cls, "♹")} {cls}</span>'
        for cls in RECYCLABILITY.keys()
    )
    st.markdown(f'<div style="margin-bottom:0.8rem;">{chip_html}</div>', unsafe_allow_html=True)
    if is_mm:
        st.markdown("""
        <div class="sidebar-info" style="margin-top:0;">
            <b>အသုံးပြုနည်း:</b><br>
            ၁။ ပလတ်စတစ် ပစ္စည်း ဓာတ်ပုံ တင်သွင်းပါ<br>
            ၂။ YOLOv8 model နှင့် တွေ့ရှိသော plastic type ကို ချက်ချင်း ခွဲခြားပေးမည်ဖြစ်သည်<br>
            ၃။ ပြန်လည်အသုံးပြုမှု လမ်းညွှန်ချက်များကို လိုက်နာပါ<br><br>
            <b>အကောင်းဆုံး ရလဒ်အတွက် အကြံပြုချက်:</b><br>
            • ကြည်လင်ပြတ်သားပြီး အလင်းရောင်ကောင်းသော ဓာတ်ပုံများ<br>
            • ပလတ်စတစ်ပစ္စည်းကို ဓာတ်ပုံ၏ အလယ်ဗဟိုတွင် ထားပါ။ အနီးကပ် ရိုက်ပါ<br>
            • ပိုမိုမှန်ကန်သော ရလဒ်ရရှိနိုင်ရန် တစ်ပုံလျှင် ပစ္စည်းတစ်ခုသာ ရိုက်ပါ
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="sidebar-info" style="margin-top:0;">
            <b>How to use:</b><br>
            1. Upload a plastic item photo<br>
            2. Get instant AI classification<br>
            3. Follow recycling guidance<br><br>
            <b>Tips for best results:</b><br>
            • Clear, sharp, high-quality images with good brightness.<br>
            • Place the plastic object in the center of the photo. Take a close-up shot.<br>
            • Single item per photo.
        </div>
        """, unsafe_allow_html=True)

uploader_lbl = "ပလတ်စတစ် စွန့်ပစ်ပစ္စည်း ဓာတ်ပုံ တင်ပါ" if is_mm else "Upload a photo of plastic waste"
uploader_hlp = "ကြည်လင်ပြတ်သားသော ဓာတ်ပုံများ ပိုမိုကောင်းမွန်ပါသည်။ ပြန်လည်အသုံးပြုမှု သင်္ကေတ ပါဝင်ပါက ပေါ်လွင်အောင် ရိုက်ပါ။" if is_mm else "Clear photos work best. Try to capture the recycling symbol if visible."

uploaded_file = st.file_uploader(
    uploader_lbl,
    type=["jpg", "jpeg", "png"],
    help=uploader_hlp
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    spin_msg = "🔍 ဓာတ်ပုံအား စစ်ဆေးနေပါသည်..." if is_mm else "🔍 Analyzing..."
    with st.spinner(spin_msg):
        results = model(image)

    r = results[0]
    if len(r.boxes) > 0:
        annotated_img = Image.fromarray(r.plot()[..., ::-1])
        best_box = r.boxes[r.boxes.conf.argmax()]
        top1_idx = int(best_box.cls[0].item())
        top1_cls = model.names[top1_idx]
        top1_conf = float(best_box.conf[0].item())
    else:
        annotated_img = image
        top1_cls = "Others"
        top1_conf = 0.0

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        img_cap = "📷 တွေ့ရှိထားသော ပလတ်စတစ်" if is_mm else "📷 Detected Plastic"
        st.image(annotated_img, caption=img_cap, use_container_width=False)

    info = RECYCLABILITY.get(top1_cls, RECYCLABILITY["Others"])
    symbol = RESIN_SYMBOLS.get(top1_cls, "♹")
    color = COLORS.get(top1_cls, "#5C8374")
    conf_pct = int(top1_conf * 100)

    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.last_file_key != file_key:
        stats = load_global_stats()
        stats["total_scans"] = stats.get("total_scans", 0) + 1
        
        if "plastic_types" not in stats:
            stats["plastic_types"] = {}
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
        st.session_state.global_stats = stats
        st.session_state.last_file_key = file_key

    with col2:
        if is_mm:
            badge = '<span class="badge-recyclable">✓ ပြန်လည်အသုံးပြုနိုင်သည်</span>' if info["recyclable"] else '<span class="badge-non">✗ ပြန်လည်အသုံးပြု၍မရပါ</span>'
            conf_lbl = "ယုံကြည်စိတ်ချရမှု အဆင့် (Confidence)"
            common_txt = "အသုံးများသည့် ပစ္စည်းများ:"
        else:
            badge = '<span class="badge-recyclable">✓ Recyclable</span>' if info["recyclable"] else '<span class="badge-non">✗ Non-recyclable</span>'
            conf_lbl = "Confidence Level"
            common_txt = "Common items:"

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
            <div class="conf-label">{conf_lbl}</div>
            <div style="display:flex; align-items:center; gap:1rem;">
                <div class="conf-bar-bg" style="flex:1">
                    <div style="height:10px; width:{conf_pct}%; background:linear-gradient(90deg,{color},{color}99); border-radius:8px;"></div>
                </div>
                <div style="font-weight:800; color:{color}; min-width:48px; font-size:1rem">{conf_pct}%</div>
            </div>
            <div class="examples-text">{common_txt} {info['examples']}</div>
        </div>
        """, unsafe_allow_html=True)

    sec_title_dtl = "တွေ့ရှိသော ပလတ်စတစ် အသေးစိတ် အချက်အလက်များ" if is_mm else "Identified Plastic Details"
    st.markdown(f'<div class="section-title">{sec_title_dtl}</div>', unsafe_allow_html=True)
    
    props_md = "".join(f"- {prop}\n" for prop in info.get("properties", []))
    
    if is_mm:
        st.markdown(f"""
        <div style="margin: 1rem 0; line-height: 1.8;">
            <b>{top1_cls} ({info['name_en']})</b> — {info['description']}
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"**အဓိက ဂုဏ်သတ္တိများ**")
        st.markdown(props_md)
        st.markdown(f"**အသုံးများသည့် ပစ္စည်းများ**")
        st.markdown(f"<div class='examples-text' style='margin-bottom:1rem;'>{info['examples']}။</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="margin: 1rem 0; line-height: 1.8;">
            <b>{top1_cls} ({info['name_en']})</b> — {info['description']}
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"**Key Properties**")
        st.markdown(props_md)
        st.markdown(f"**Common Uses**")
        st.markdown(f"<div class='examples-text' style='margin-bottom:1rem;'>{info['examples']}.</div>", unsafe_allow_html=True)

    sec_title_gd = "♻️ ပြန်လည်အသုံးပြုမှု လမ်းညွှန်ချက်များ" if is_mm else "♻️ Recycling Guidance"
    st.markdown(f'<div class="section-title">{sec_title_gd}</div>', unsafe_allow_html=True)
    
    spin_gd = "လမ်းညွှန်ချက်များ ရယူနေပါသည်..." if is_mm else "Getting guidance..."
    with st.spinner(spin_gd):
        guidance_points = get_guidance(top1_cls, info["recyclable"], st.session_state.lang)
    guidance_html = "".join(f"<li>{point}</li>" for point in guidance_points)
    st.markdown(
        f'<div class="guidance-box"><ul class="guidance-list">{guidance_html}</ul></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    report_sub = "အစီရင်ခံစာ ထုတ်ယူရန်" if is_mm else "Export Report"
    st.subheader(report_sub)
    
    pdf_data = generate_pdf_report(image, top1_cls, float(top1_conf * 100), info, guidance_points, st.session_state.lang)
    
    if pdf_data:
        dl_lbl = "📄 PDF အစီရင်ခံစာ ရယူမည်" if is_mm else "📄 Download PDF Report"
        st.download_button(
            label=dl_lbl,
            data=pdf_data,
            file_name=f"EcoSort_Report_{top1_cls}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        err_pdf = "PDF ထုတ်ယူ၍ မရနိုင်ပါ။ WeasyPrint စနစ် ပြည့်စုံစွာ ထည့်သွင်းထားခြင်း ရှိမရှိ စစ်ဆေးပါ။" if is_mm else "Failed to generate PDF. WeasyPrint dependencies might be missing."
        st.error(err_pdf)

else:
    empty_t = "စတင်ရန် ပလတ်စတစ် ပစ္စည်း ဓာတ်ပုံ တင်ပါ" if is_mm else "Upload a plastic item photo to get started"
    empty_s = "JPG, JPEG, PNG ဖိုင်များကို လက်ခံပါသည် · AI နည်းပညာသုံး စစ်ဆေးမှု" if is_mm else "Supports JPG, JPEG, PNG · AI-powered classification"
    st.markdown(f"""
    <div class="empty-state">
        <div style="font-size:4rem; margin-bottom:1rem">📷</div>
        <div style="font-size:1.1rem; font-weight:500; margin-bottom:0.5rem">{empty_t}</div>
        <div style="font-size:0.85rem; opacity:0.7">{empty_s}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)
render_waste_chart(st.session_state.lang)

# ==========================================
# FOOTER 
# ==========================================
if is_mm:
    st.markdown("""
    <footer style="text-align: center; padding: 2rem 0; color: #8D99AE; font-size: 0.8rem;">
        ♻️ EcoSort · AI-Powered Plastic Recycling Assistant<br>
        © 2026 · Developed by Zin Wut Yee Zaw
    </footer>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <footer style="text-align: center; padding: 2rem 0; color: #8D99AE; font-size: 0.8rem;">
        ♻️ EcoSort · AI-Powered Plastic Recycling Assistant<br>
        © 2026 · Developed by Zin Wut Yee Zaw
    </footer>
    """, unsafe_allow_html=True)
