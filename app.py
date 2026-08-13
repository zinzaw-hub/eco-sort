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
    page_title="EcoSort - ပလတ်စတစ် ခွဲခြားစစ်ဆေးစနစ်" if is_mm else "EcoSort - Plastic Recycling Assistant",
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

RECYCLABILITY_MM = {
    "PET": {
        "recyclable": True, "code": "1", "name_en": "Polyethylene Terephthalate (ပေါလီအက်သလင်း တာရက်သလိတ်)", 
        "examples": "ရေသန့်ဗူး၊ အအေးဗူး၊ အစားအသောက်ထည့် ဘူးများ",
        "description": "PET (Polyethylene Terephthalate) သည် ကြည်လင်၊ ခိုင်မာပြီး ပေါ့ပါးသော ပလတ်စတစ်ဖြစ်ပြီး အောက်ဆီဂျင်ကြောင့် အစားအသောက်များ ပျက်စီးခြင်းမှ ကာကွယ်ပေးသဖြင့် အစားအသောက်နှင့် သောက်ရေသန့် ထုပ်ပိုးရာတွင် အများဆုံး အသုံးပြုကြသည်။",
        "properties": [
            "ကြည်လင်ပြတ်သားခြင်း — အလင်းပေါက်မှု မြင့်မားခြင်း",
            "ခိုင်ခံ့ပြီး ရိုက်ခတ်ဒဏ် ခံနိုင်ခြင်း — ရိုက်ခတ်မှုများကို ကောင်းစွာ တောင့်ခံနိုင်ခြင်း",
            "လေနှင့် စိုထိုင်းဆကို ကောင်းစွာ ကာကွယ်ပေးနိုင်ခြင်း — လတ်ဆတ်မှုကို ထိန်းသိမ်းပေးခြင်း",
            "၁၀၀% ပြန်လည်အသုံးပြုနိုင်ခြင်း — ပြန်လည်အသုံးပြုရေး စက်ရုံများမှ အလိုရှိဆုံး ပလတ်စတစ်ဖြစ်ခြင်း"
        ]
    },
    "HDPE": {
        "recyclable": True, "code": "2", "name_en": "High-Density Polyethylene (သိပ်သည်းဆမြင့် ပေါလီအက်သလင်း)", 
        "examples": "နို့ဗူး၊ ဆပ်ပြာဆီဗူး၊ ခေါင်းလျှော်ရည်ဗူးများ",
        "description": "HDPE (High-Density Polyethylene) သည် မာကျောခိုင်မာပြီး ပျော်ရည်အမျိုးမျိုးကို ခံနိုင်ရည်ရှိသော ပလတ်စတစ်ဖြစ်သဖြင့် ခိုင်ခံ့သော ဗူးများနှင့် ကွန်တိန်းနားများ ပြုလုပ်ရာတွင် သင့်တော်သည်။",
        "properties": [
            "မာကျောခိုင်ခံ့ခြင်း — လေးလံသော ပစ္စည်းများ ဆင့်စီရာတွင် ခံနိုင်ရည်ရှိခြင်း",
            "ဓာတုဗေဒဆေးဝါးများ ခံနိုင်ခြင်း — အိမ်သုံးသန့်ရှင်းရေး ဆေးဝါးများကို ဘေးကင်းစွာ ထည့်သွင်းနိုင်ခြင်း",
            "ရာသီဥတုဒဏ် ခံနိုင်ခြင်း — ပတ်ဝန်းကျင်ဒဏ်ကို တောင့်ခံနိုင်ခြင်း",
            "ကျယ်ပြန့်စွာ ပြန်လည်အသုံးပြုနိုင်ခြင်း — ပြန်လည်သိမ်းဆည်းရေး အစီအစဉ်တော်တော်များများတွင် လက်ခံခြင်း"
        ]
    },
    "LDPE": {
        "recyclable": True, "code": "4", "name_en": "Low-Density Polyethylene (သိပ်သည်းဆနည်း ပေါလီအက်သလင်း)", 
        "examples": "ပေါင်မုန့်အိတ်၊ ညှစ်ထုတ်ရသော ဗူးများ၊ ပလတ်စတစ် အုပ်အိတ်များ",
        "description": "LDPE (Low-Density Polyethylene) သည် ပျော့ပျောင်း ကွေးညွှတ်နိုင်ပြီး ဓာတုဗေဒဒဏ် ခံနိုင်သော ပလတ်စတစ်ဖြစ်သည်။ HDPE ထက် မာကျောမှုနည်းပါးပြီး အိတ်များနှင့် ပျော့ပျောင်းသော ထုပ်ပိုးမှုများတွင် အသုံးပြုသည်။",
        "properties": [
            "ပျော့ပျောင်းကွေးညွှတ်နိုင်ခြင်း — မကျိုးပဲ့ဘဲ ကွေးညွှတ်နိုင်ခြင်း",
            "ပေါ့ပါးခြင်း — ထုပ်ပိုးမှု အလေးချိန်ကို နည်းပါးစေခြင်း",
            "စိုထိုင်းဆ ခံနိုင်ခြင်း — အတွင်းပစ္စည်းများကို ခြောက်သွေ့စေခြင်း",
            "အစိတ်အပိုင်းလိုက် ပြန်လည်အသုံးပြုနိုင်ခြင်း — အချို့သော ပြန်လည်သိမ်းဆည်းရေး စခန်းများတွင် လက်ခံခြင်း"
        ]
    },
    "PP": {
        "recyclable": True, "code": "5", "name_en": "Polypropylene (ပေါလီပရိုပလင်း)", 
        "examples": "ဒိန်ချဉ်ခွက်၊ ဗူးအဖုံးများ၊ အဆာပြေ အစားအသောက်ထည့် ဗူးများ",
        "description": "PP (Polypropylene) သည် အပူဒဏ်ခံနိုင်ပြီး ခိုင်မာသော ပလတ်စတစ်ဖြစ်ကာ စိုထိုင်းဆ၊ ဆီနှင့် ဓာတုဗေဒပစ္စည်းများကို တားဆီးပေးနိုင်သဖြင့် အပူဖြည့် သောက်စရာများနှင့် အစားအသောက် သိုလှောင်ရန် သင့်တော်သည်။",
        "properties": [
            "အပူဒဏ်ခံနိုင်မှု မြင့်မားခြင်း — မိုက်ခရိုဝေ့ဖ်နှင့် အပူချိန်မြင့် အရည်များအတွက် ဘေးကင်းခြင်း",
            "ခိုင်ခံ့ပြီး ကွေးညွှတ်ဒဏ် ခံနိုင်ခြင်း — ထပ်ခါထပ်ခါ မကြာခဏ အသုံးပြုနိုင်ခြင်း",
            "စိုထိုင်းဆနှင့် ဆီဒဏ် ကာကွယ်ပေးခြင်း — အစားအသောက် ထုပ်ပိုးမှုအတွက် အထူးကောင်းမွန်ခြင်း",
            "ပြန်လည်အသုံးပြုနိုင်ခြင်း — ဒေသတွင်း အစီအစဉ်များတွင် တိုးမြှင့်လက်ခံလာခြင်း"
        ]
    },
    "PS": {
        "recyclable": False, "code": "6", "name_en": "Polystyrene (ပေါလီစတိုရင်း)", 
        "examples": "ဖော့ခွက်များ၊ အစားအသောက်ထည့် ဖော့ဗူးများ၊ ပစ္စည်းအလွှာသုံး ဖော့စေ့များ",
        "description": "PS (Polystyrene) ကို မာကျောသော ပုံစံ သို့မဟုတ် ဖော့ပုံစံ (Styrofoam) ဖြင့် တွေ့ရသည်။ ပေါ့ပါးပြီး အပူချိန် ထိန်းသိမ်းမှု ကောင်းသော်လည်း ကျိုးပဲ့လွယ်ပြီး စီးပွားရေးအရ ပြန်လည်အသုံးပြုရန် ခက်ခဲသည်။",
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
        "description": "Others (အမျိုးအစား ၇) တွင် အမျိုးအစား ၁ မှ ၆ အတွင်း မပါဝင်သော ပလတ်စတစ်များ ပါဝင်ပြီး အလွှာပေါင်းစုံ ရောနှောထားသော သို့မဟုတ် ပေါလီကာဗိုနိတ် ပလတ်စတစ်များ ဖြစ်လေ့ရှိသည်။",
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
# AI GUIDANCE & REPORT GENERATION FUNCTIONS
# ==========================================
@st.cache_data(show_spinner=False)
def get_guidance(plastic_type, recyclable, lang="en"):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return ["လမ်းညွှန်ချက် မရနိုင်ပါ: GROQ_API_KEY ထည့်သွင်းထားခြင်း မရှိပါ။"] if lang == "mm" else ["Guidance unavailable: GROQ_API_KEY not configured."]
    try:
        client = Groq(api_key=api_key)
        if lang == "mm":
            prompt = (
                f"Give exactly 5 short, practical bullet points in Myanmar (Burmese) language on how to properly "
                f"{'recycle' if recyclable else 'dispose of'} {plastic_type} plastic. "
                f"Each bullet must be a single short actionable sentence in Myanmar language. "
                f"Reply with ONLY the bullet points in Myanmar, one per line, each starting with '- '. "
                f"No intro, no summary, no extra text."
            )
        else:
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
            max_tokens=350,
        )
        raw = resp.choices[0].message.content.strip()
        points = [
            line.lstrip("-•* ").strip()
            for line in raw.splitlines()
            if line.strip()
        ]
        return points if points else [raw]
    except Exception as e:
        return [f"လမ်းညွှန်ချက် မရနိုင်ပါ: {e}"] if lang == "mm" else [f"Guidance unavailable: {e}"]

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
        @page {{ size: A4; margin: 10mm; background-color: #fdfbf7; }}
        body {{ font-family: 'Pyidaungsu', 'Arial', sans-serif; color: #333; font-size: 13px; line-height: 2.2; }}
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
    return YOLO("best_model_yolov8_ft2.pt")

model = load_model()

# ==========================================
# PAGE VIEWS: WASTE CHART & ABOUT PAGE
# ==========================================
def render_waste_chart(lang="en"):
    th = st.session_state["_theme"]
    title_text = "ကမ္ဘာ့နှင့် မြန်မာနိုင်ငံ၏ ပလတ်စတစ် ပြန်လည်အသုံးပြုနိုင်မှု နှုန်းထား" if lang == "mm" else "Global vs. Myanmar Plastic Recycling"
    st.markdown(f'<div class="section-title">{title_text}</div>', unsafe_allow_html=True)

    years = [2000, 2005, 2010, 2015, 2019, 2022, 2023, 2024, 2025]
    global_rate = [5, 7, 9, 11, 13, 9.5, 9.8, 10.2, 10.5]
    myanmar_rate = [3, 3.5, 4, 5, 6, 7, 7.5, 8, 8.5]

    color_global = "#118AB2"
    color_myanmar = "#EF476F"

    name_g = "ကမ္ဘာ့နှုန်းထား" if lang == "mm" else "Global"
    name_m = "မြန်မာနိုင်ငံ (ဒေသတွင်း ခန့်မှန်းချက်)" if lang == "mm" else "Myanmar (regional estimate)"

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
    
    y_title = "ပြန်လည်အသုံးပြုမှု နှုန်းထား (%)" if lang == "mm" else "Recycling rate (%)"

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

    if lang == "mm":
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
    if lang == "mm":
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
                <b>အရေးပါမှု:</b> ကမ္ဘာပေါ်တွင် စွန့်ပစ် ပလတ်စတစ်၏ ၁၀% အောက်သာ ပြန်လည်အသုံးပြုနိုင်သေးပြီး ပလတ်စတစ် အမျိုးအစားအလိုက် ခွဲခြားခြင်းသည် ပြန်လည်အသုံးပြုရေး လုပ်ငန်းစဉ်၏ အဓိက အခက်အခဲ ဖြစ်ပါသည်။ EcoSort သည် ကွန်ပျူတာ ဗီဇရှင် နည်းပညာဖြင့် ပြည်သူများ လွယ်ကူစွာ သေချာစွာ ခွဲခြားနိုင်စေရန် ရည်ရွယ်ပါသည်။
            </div>
            <div class="about-p">
                <b>အသုံးပြုထားသော နည်းပညာများ:</b> ခွဲခြားစစ်ဆေးရန် YOLOv8 (Ultralytics)၊ အသုံးပြုသူ အင်တာဖေ့စ်အတွက် Streamlit နှင့် လွယ်ကူသော လမ်းညွှန်ချက်များ ထုတ်ပေးရန် Groq LLM API ကို အသုံးပြုထားပါသည်။
            </div>
            <div class="about-p">
                <b>ရေးသားသူ:</b> ဇင်ဝတ်ရည်ဇော်၊ ပြည်ကွန်ပျူတာတက္ကသိုလ် (UCSPyay)၊ ကွန်ပျူတာသိပ္ပံ ကျောင်းသူ။<br>
                <b>ဆက်သွယ်ရန်:</b> wyee659@gmail.com။
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
                and an LLM (via Groq) for generating plain-language disposal guidance.
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
    title_text = "ဒက်ရှ်ဘုတ် (Dashboard)" if lang == "mm" else "Dashboard"
    sub_text = "စကင်ဖတ်မှု မှတ်တမ်းနှင့် ကိန်းဂဏန်းများ" if lang == "mm" else "Global Scan History & Stats"
    
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
        no_scan_title = "စကင်ဖတ်ထားမှုများ မရှိသေးပါ" if lang == "mm" else "No scans yet"
        no_scan_sub = "ကိန်းဂဏန်းများကို ကြည့်ရှုရန် 'ခွဲခြားစစ်ဆေးရန်' စာမျက်နှာတွင် ပလတ်စတစ်ပုံ ပို့ပါ။" if lang == "mm" else "Classify a plastic item on the Classifier page to see stats here."
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
        (m1, total, "စုစုပေါင်း စကင်ဖတ်မှု" if lang == "mm" else "Total Scans"),
        (m2, f"{recyclable_pct}%", "ပြန်လည်အသုံးပြုနိုင်မှု" if lang == "mm" else "Recyclable"),
        (m3, most_common, "အများဆုံး အမျိုးအစား" if lang == "mm" else "Most Common"),
        (m4, f"{avg_conf}%", "ပျမ်းမျှ ယုံကြည်စိတ်ချရမှု" if lang == "mm" else "Avg. Confidence"),
    ]
    for col, value, label in metric_labels:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    sec_title1 = "ပလတ်စတစ် အမျိုးအစားအလိုက် စကင်ဖတ်မှု" if lang == "mm" else "Scans by Plastic Type"
    st.markdown(f'<div class="section-title">{sec_title1}</div>', unsafe_allow_html=True)
    
    bar_fig = go.Figure(go.Bar(
        x=list(type_counts.keys()),
        y=list(type_counts.values()),
        marker_color=[COLORS.get(k, th["accent"]) for k in type_counts.keys()],
        text=list(type_counts.values()),
        textposition="outside",
    ))
    y_axis_lbl = "အရေအတွက်" if lang == "mm" else "Count"
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
        sec_title2 = "♻️ ပြန်လည်အသုံးပြုနိုင်မှု အချိုးအစား" if lang == "mm" else "♻️ Recyclable Split"
        st.markdown(f'<div class="section-title">{sec_title2}</div>', unsafe_allow_html=True)
        
        pie_labels = ["ပြန်လည်အသုံးပြုနိုင်သည်", "ပြန်လည်အသုံးပြု၍မရပါ"] if lang == "mm" else ["Recyclable", "Non-recyclable"]
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
        sec_title3 = "လတ်တလော စကင်ဖတ်မှုများ" if lang == "mm" else "Recent Scans"
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

    clear_btn_text = "🗑️ မှတ်တမ်းများကို ရှင်းလင်းမည်" if lang == "mm" else "🗑️ Clear global stats"
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
    
    title_text = "လေ့လာရန် (Learn)" if lang == "mm" else "Learn"
    sub_text = "ပလတ်စတစ် အမျိုးအစားများနှင့် ပြန်လည်အသုံးပြုခြင်း အခြေခံများ" if lang == "mm" else "Plastic Types & Recycling Basics"
    st.markdown(f"""
    <div class="eco-header">
        <div class="eco-title">{title_text}</div>
        <div class="eco-subtitle">{sub_text}</div>
    </div>
    """, unsafe_allow_html=True)

    vid_title = "ပြန်လည်အသုံးပြုခြင်း နမူနာ ဗီဒီယို" if lang == "mm" else "Recycling Example Video"
    st.markdown(f'<div class="section-title">{vid_title}</div>', unsafe_allow_html=True)
    st.video("https://youtu.be/MwL8kgyOzFA?si=13bvQnmQG3AunDIh")

    proc_title = "♻️ ပလတ်စတစ် ပြန်လည်အသုံးပြုပုံ အဆင့်ဆင့်" if lang == "mm" else "♻️ How Plastic Recycling Works (Step by Step)"
    st.markdown(f'<div class="section-title">{proc_title}</div>', unsafe_allow_html=True)

    step_images = {
        "step1": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/ds2pe_image_239.jpg",
        "step2": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/plastic-recycling-sorting-image.jpg",
        "step3": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/close-hands.jpg",
        "step4": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/T8200219.jpg",
        "step5": "https://raw.githubusercontent.com/zinzaw-hub/eco-sort/main/AdobeStock_759704272-1.jpeg",
    }

    steps_data = [
        {
            "img": step_images["step1"],
            "title": "အဆင့် ၁ - စုဆောင်းခြင်း (Collection)" if lang == "mm" else "Step 1: Collection",
            "desc": "ပလတ်စတစ် စွန့်ပစ်ပစ္စည်းများကို နေအိမ်များ၊ လုပ်ငန်းများနှင့် ပြန်လည်အသုံးပြုမှု စွန့်ပစ်စခန်းများမှ စုဆောင်းပါသည်။ ဤသည်မှာ ပထမဆုံးနှင့် အရေးအကြီးဆုံး အဆင့်ဖြစ်ပြီး စနစ်တကျ စုဆောင်းမှု မရှိပါက ပြန်လည်အသုံးပြုခြင်း ပြုလုပ်နိုင်မည် မဟုတ်ပါ။" if lang == "mm" else "Plastic waste is collected from households, businesses, and recycling drop-off points. This is the first and most important step — without proper collection, recycling can't happen.",
            "tip": "<b>အကြံပြုချက်:</b> အမှိုက်ပုံးထဲ မထည့်မီ သင့်ပလတ်စတစ်များကို အမျိုးအစားအလိုက် (ဗူးများ၊ ပုံးများ၊ အိတ်များ) သီးခြား ခွဲခြားထားပါ။" if lang == "mm" else "<b>Tip:</b> Separate your plastics by type (bottles, containers, bags) before putting them in the recycling bin."
        },
        {
            "img": step_images["step2"],
            "title": "အဆင့် ၂ - ခွဲခြားခြင်း (Sorting)" if lang == "mm" else "Step 2: Sorting",
            "desc": "ပလတ်စတစ်များကို ၎င်းတို့၏ ရာဇင်အမျိုးအစားအလိုက် (PET, HDPE, PP စသည်ဖြင့်) အဆင့်မြင့် အလင်းစကင်ဖတ်စက်များ သို့မဟုတ် လူကိုယ်တိုင် ခွဲခြားကြပါသည်။ အမျိုးအစား မတူသော ပလတ်စတစ်များကို အတူတကွ ပြန်လည်အသုံးပြု၍ မရနိုင်ပါ။" if lang == "mm" else "Plastics are sorted by resin type (PET, HDPE, PP, etc.) using advanced optical sorters and manual labor. Different types can't be recycled together.",
            "tip": "<b>အကြံပြုချက်:</b> သင့် ပလတ်စတစ် ပစ္စည်းများ၏ အောက်ခြေတွင် ပါရှိသော ရာဇင်ကုဒ် (♳-♹) သင်္ကေတကို စစ်ဆေးပါ — ဤသင်္ကေတအတိုင်း ခွဲခြားရခြင်း ဖြစ်သည်။" if lang == "mm" else "<b>Tip:</b> Check the resin code (♳-♹) on the bottom of your plastic items — this is how they're sorted!"
        },
        {
            "img": step_images["step3"],
            "title": "အဆင့် ၃ - သန့်စင်ခြင်း (Cleaning)" if lang == "mm" else "Step 3: Cleaning",
            "desc": "ပလတ်စတစ်များကို တံဆိပ်ကပ်များ၊ ကော်များ၊ အစားအသောက် အကြွင်းအကျန်များနှင့် ဖုန်မှုန့်များ ကင်းစင်စေရန် ဆေးကြောကြပါသည်။ ပေကျံနေသော ပလတ်စတစ်များသည် အသုတ်တစ်ခုလုံးကို ပျက်စီးစေနိုင်သဖြင့် ဤအဆင့်မှာ အလွန်အရေးပါသည်။" if lang == "mm" else "Plastics are washed to remove labels, glue, food residue, and dirt. This is critical — contaminated plastics can ruin an entire batch.",
            "tip": "<b>အကြံပြုချက်:</b> စွန့်ပစ် မပြောင်းမီ သင့် ပလတ်စတစ် ပစ္စည်းများကို ရေဆေးလိုက်ပါ! အနည်းငယ် ဆေးကြောလိုက်ခြင်းသည် သန့်စင်ရေး စက်ရုံအတွက် အလွန် ကူညီရာရောက်ပါသည်။" if lang == "mm" else "<b>Tip:</b> Rinse your plastic items before recycling! A quick rinse makes a huge difference at the cleaning facility."
        },
        {
            "img": step_images["step4"],
            "title": "အဆင့် ၄ - ကြိတ်စေ့ပြုလုပ်ခြင်း (Shredding)" if lang == "mm" else "Step 4: Shredding",
            "desc": "သန့်စင်ပြီးသော ပလတ်စတစ်များကို သေးငယ်သော အစုတ်စုတ်အမြွှာမြွှာ ကြိတ်စေ့များအဖြစ် ကြိတ်ခွဲလိုက်ပါသည်။ ၎င်းသည် မျက်နှာပြင် အကျယ်အဝန်းကို တိုးတက်စေပြီး အရည်ကြိုရန်နှင့် ပုံသွင်းရန် လွယ်ကူစေပါသည်။" if lang == "mm" else "Clean plastic is shredded into small flakes or pellets. This increases the surface area and makes it easier to melt and reform.",
            "tip": "<b>အကြံပြုချက်:</b> ပလတ်စတစ် ကြိတ်စေ့များသည် ဗူးများမှသည် အဝတ်အထည်များအထိ ပလတ်စတစ်သစ် ပစ္စည်းများ ပြုလုပ်ရန် ကုန်ကြမ်းဖြစ်ပါသည်။" if lang == "mm" else "<b>Tip:</b> Shredded plastic flakes are the raw material for making new plastic products — from bottles to clothing!"
        },
        {
            "img": step_images["step5"],
            "title": "အဆင့် ၅ - ပလတ်စတစ်စေ့ ပြုလုပ်ခြင်း (Pelletizing)" if lang == "mm" else "Step 5: Pelletizing",
            "desc": "ကြိတ်ခွဲထားသော ပလတ်စတစ်များကို အရည်ကြိုပြီး သေးငယ်သော ပလတ်စတစ်စေ့များအဖြစ် ပုံသွင်းပါသည်။ ဤစေ့များကို စက်ရုံများသို့ ပြန်လည်ရောင်းချပြီး ပလတ်စတစ် သစ်များ ထုတ်လုပ်ကာ ပြန်လည်အသုံးပြုမှု သံသရာကို ပြည့်စုံစေပါသည်။" if lang == "mm" else "Shredded plastic is melted and formed into small pellets (nurdles). These pellets are then sold to manufacturers to make new plastic products — closing the recycling loop!",
            "tip": "<b>အကြံပြုချက်:</b> ပတ်ဝန်းကျင် ထိန်းသိမ်းရေးကို အထောက်အကူပြုရန် ပြန်လည်အသုံးပြုထားသည့် ပလတ်စတစ် (\"Post-Consumer Recycled\" သို့မဟုတ် \"PCR\") ဖြင့် ပြုလုပ်ထားသော ပစ္စည်းများကို အသုံးပြုပါ။" if lang == "mm" else "<b>Tip:</b> Look for products made from recycled plastic (often labeled \"Post-Consumer Recycled\" or \"PCR\") to support the circular economy."
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
    resin_sec_title = "ပလတ်စတစ် အမျိုးအစားများ" if lang == "mm" else "The Resin Types"
    st.markdown(f'<div class="section-title">{resin_sec_title}</div>', unsafe_allow_html=True)

    for cls, info in RECYCLABILITY.items():
        sym = RESIN_SYMBOLS.get(cls, "♹")
        color = COLORS.get(cls, "#5C8374")
        if lang == "mm":
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

    # ---------- GENERAL TIPS ----------
    gen_tips_title = "🌱 အထွေထွေ အကြံပြုချက်များ" if lang == "mm" else "🌱 General Tips"
    st.markdown(f'<div class="section-title">{gen_tips_title}</div>', unsafe_allow_html=True)
    
    if lang == "mm":
        st.markdown("""
        <div class="result-card result-card-flex">
            <div class="about-p">
                <b>၁။ မသုံးဘဲ လျှော့ချပါ။</b> အထိရောက်ဆုံး ပလတ်စတစ် စွန့်ပစ်မှု လျှော့ချခြင်းမှာ မထုတ်လုပ်မီ ထိန်းချုပ်ခြင်း ဖြစ်သည် — ထပ်မံ အသုံးပြုနိုင်သော ရေသန့်ဗူးများ၊ အိတ်များ၊ ကွန်တိန်းနားများသည် ပြန်လည်အသုံးပြုခြင်းထက် ပိုမို ထိရောက်ပါသည်။
            </div>
            <div class="about-p">
                <b>၂။ မစွန့်ပစ်မီ ရေဆေးပါ။</b> အစားအသောက် သို့မဟုတ် အရည် ပေကျံနေခြင်းသည် ပြန်လည်အသုံးပြုရေး စက်ရုံများတွင် အခြား ပြန်လည်အသုံးပြုနိုင်သော ပစ္စည်းများကိုပါ ညစ်နွမ်းစေပြီး အမှိုက်ပုံသို့ ရောက်ရှိစေပါသည်။
            </div>
            <div class="about-p">
                <b>၃။ မသေချာဘဲ မစွန့်ပစ်ပါနှင့်။</b> ပြန်လည်အသုံးပြု၍ မရနိုင်သော ပစ္စည်းများကို စွန့်ပစ်ပုံးထဲ ထည့်ခြင်းသည် ပိုမို ပျက်စီးစေနိုင်သည် — မသေချာပါက ဒေသတွင်း သတ်မှတ်ချက်များကို စစ်ဆေးပါ။
            </div>
            <div class="about-p">
                <b>၄။ ဒေသတွင်း စည်းကမ်းများကို လိုက်နာပါ။</b> နေရာဒေသအလိုက် ပြန်လည်အသုံးပြုနိုင်မှု သတ်မှတ်ချက်များ ကွဲပြားနိုင်သည် — ဤဆော့ဖ်ဝဲကို အခြေခံအဖြစ် အသုံးပြုပြီး သင့်ဒေသရှိ အမှိုက်စွန့်ပစ်မှု စည်းကမ်းများနှင့် တိုက်ဆိုင်စစ်ဆေးပါ။
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
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
    dark_label = "🌙 အမှောင်မုဒ် (Dark mode)" if is_mm else "🌙 Dark mode"
    dark = st.toggle(dark_label, value=st.session_state.dark_mode)
    if dark != st.session_state.dark_mode:
        st.session_state.dark_mode = dark
        st.rerun()

    # ===== LANGUAGE SWITCHER =====
    st.markdown("---")
    lang_header = "🌐 ဘာသာစကား" if is_mm else "🌐 Language"
    st.markdown(f"<div style='font-weight:600; font-size:0.85rem; margin-bottom:0.4rem;'>{lang_header}</div>", unsafe_allow_html=True)
    _col_l1, _col_l2 = st.columns(2)
    with _col_l1:
        if st.button("GB English", key="btn_lang_en", use_container_width=True, type="primary" if st.session_state.lang == "en" else "secondary"):
            st.session_state.lang = "en"
            st.rerun()
    with _col_l2:
        if st.button("MM မြန်မာ", key="btn_lang_mm", use_container_width=True, type="primary" if st.session_state.lang == "mm" else "secondary"):
            st.session_state.lang = "mm"
            st.rerun()
        
    # ===== Sidebar Footer =====
    st.markdown("---")
    if is_mm:
        st.markdown("""
        <div style="text-align: center; padding: 0.5rem 0; color: #8D99AE; font-size: 0.65rem; opacity: 0.7;">
            ♻️ EcoSort · အေအိုင်သုံး ပလတ်စတစ် ပြန်လည်အသုံးပြုမှု ကူညီရေးစနစ်<br>
            © 2026 ရေးသားသူ ဇင်ဝတ်ရည်ဇော် (UCSPyay)<br>
            ကြီးကြပ်သူ: ဒေါ်ခင်အေးဆန်း
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
            ၂။ AI မှ ချက်ချင်း ခွဲခြားပေးမည်ဖြစ်သည်<br>
            ၃။ ပြန်လည်အသုံးပြုမှု လမ်းညွှန်ချက်များကို လိုက်နာပါ<br><br>
            <b>အကောင်းဆုံး ရလဒ်အတွက် အကြံပြုချက်:</b><br>
            • ကြည်လင်ပြတ်သားပြီး အလင်းရောင်ကောင်းသော ဓာတ်ပုံများ<br>
            • ပြန်လည်အသုံးပြုမှု သင်္ကေတ ပါဝင်ပါက ပေါ်လွင်အောင် ရိုက်ပါ<br>
            • တစ်ပုံလျှင် ပစ္စည်းတစ်ခုသာ ရိုက်ပါ
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
            • Clear, well-lit photos<br>
            • Show the recycling symbol if visible<br>
            • Single item per photo
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
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        img_cap = "📷 တင်သွင်းထားသော ဓာတ်ပုံ" if is_mm else "📷 Uploaded Image"
        st.image(image, caption=img_cap, use_container_width=False)

    spin_msg = "🔍 ဓာတ်ပုံအား စစ်ဆေးနေပါသည်..." if is_mm else "🔍 Analyzing..."
    with st.spinner(spin_msg):
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
            common_txt = "📦 အသုံးများသည့် ပစ္စည်းများ:"
        else:
            badge = '<span class="badge-recyclable">✓ Recyclable</span>' if info["recyclable"] else '<span class="badge-non">✗ Non-recyclable</span>'
            conf_lbl = "Confidence Level"
            common_txt = "📦 Common items:"

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
            <b>{top1_cls} ({info['name_en']})</b> — {info['description']} ရာဇင် သင်္ကေတ နံပါတ် #{info['code']} ဖြင့် သတ်မှတ်ထားပါသည်။
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"**အဓိက ဂုဏ်သတ္တိများ**")
        st.markdown(props_md)
        st.markdown(f"**📦 အသုံးများသည့် ပစ္စည်းများ**")
        st.markdown(f"<div class='examples-text' style='margin-bottom:1rem;'>{info['examples']}။</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="margin: 1rem 0; line-height: 1.8;">
            <b>{top1_cls} ({info['name_en']})</b> — {info['description']} Identified by recycling number #{info['code']}.
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"**Key Properties**")
        st.markdown(props_md)
        st.markdown(f"**📦 Common Uses**")
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
        ♻️ EcoSort · အေအိုင်သုံး ပလတ်စတစ် ပြန်လည်အသုံးပြုမှု ကူညီရေးစနစ်<br>
        © 2026 · ရေးသားသူ ဇင်ဝတ်ရည်ဇော်
    </footer>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <footer style="text-align: center; padding: 2rem 0; color: #8D99AE; font-size: 0.8rem;">
        ♻️ EcoSort · AI-Powered Plastic Recycling Assistant<br>
        © 2026 · Developed by Zin Wut Yee Zaw
    </footer>
    """, unsafe_allow_html=True)
