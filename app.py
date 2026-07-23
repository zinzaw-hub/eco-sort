import streamlit as st
from ultralytics import YOLO
from PIL import Image
import os
import plotly.graph_objects as go
from groq import Groq

st.set_page_config(page_title="EcoSort", page_icon="♻️", layout="wide")

# ---------------- Theme ----------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

def apply_theme():
    if st.session_state.dark_mode:
        bg, card, text, accent, accent2 = "#2b2b24", "#3a3a30", "#f0ead6", "#a9b18f", "#c9a66b"
    else:
        bg, card, text, accent, accent2 = "#f5f2e8", "#ffffff", "#3a3a30", "#8a9a5b", "#bfa76a"
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {bg}; color: {text}; }}
        div[data-testid="stMetric"], div[data-testid="stContainer"] {{
            background-color: {card}; border-radius: 12px; padding: 8px;
        }}
        .stButton>button {{
            background-color: {accent}; color: white; border-radius: 8px; border: none;
        }}
        .stProgress > div > div {{ background-color: {accent2}; }}
        </style>
    """, unsafe_allow_html=True)

apply_theme()

# ---------------- Resin Info ----------------
RESIN_SYMBOLS = {
    "PET": "♳", "HDPE": "♴", "LDPE": "♶",
    "PP": "♷", "PS": "♸", "Others": "♹",
}

RECYCLABILITY = {
    "PET":    {"recyclable": True,  "code": "1", "name_en": "Polyethylene Terephthalate"},
    "HDPE":   {"recyclable": True,  "code": "2", "name_en": "High-Density Polyethylene"},
    "LDPE":   {"recyclable": True,  "code": "4", "name_en": "Low-Density Polyethylene"},
    "PP":     {"recyclable": True,  "code": "5", "name_en": "Polypropylene"},
    "PS":     {"recyclable": False, "code": "6", "name_en": "Polystyrene"},
    "Others": {"recyclable": False, "code": "7", "name_en": "Other / Mixed Plastics"},
}

# ---------------- Groq LLM ----------------
@st.cache_data(show_spinner=False)
def get_guidance(plastic_type, recyclable):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Guidance unavailable: GROQ_API_KEY not configured."
    try:
        client = Groq(api_key=api_key)
        status = "recyclable" if recyclable else "non-recyclable"
        prompt = (
            f"In 2 short sentences, tell someone how to properly "
            f"{'recycle' if recyclable else 'dispose of'} {plastic_type} plastic "
            f"(a {status} material). Be practical and concise."
        )
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Guidance unavailable: {e}"

# ---------------- Model ----------------
@st.cache_resource
def load_model():
    return YOLO("best_model_yolov8.pt")

model = load_model()

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Settings")
    st.toggle("Dark mode", key="dark_mode", on_change=apply_theme)
    st.markdown("---")
    st.subheader("Global Plastic Waste by Type")
    labels = ["PET", "HDPE", "LDPE", "PP", "PS", "Others"]
    values = [12, 17, 15, 19, 8, 29]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.4,
        marker=dict(colors=["#8a9a5b","#bfa76a","#a9b18f","#c9a66b","#6b7a4f","#5c5c4d"])
    )])
    fig.update_layout(
        margin=dict(t=0,b=0,l=0,r=0), height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#3a3a30" if not st.session_state.dark_mode else "#f0ead6"
    )
    st.plotly_chart(fig)

# ---------------- Main ----------------
st.title("♻️ EcoSort - AI Plastic Classifier")
st.write("Upload a photo of plastic waste to identify its resin type and get recycling guidance.")

uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    col1, col2 = st.columns(2)
    with col1:
        st.image(image, caption="Uploaded Image")

    with st.spinner("Analyzing..."):
        results = model(image)

    r = results[0]
    probs = r.probs

    # Top prediction
    top1_idx = probs.top1
    top1_cls = model.names[top1_idx]
    top1_conf = float(probs.top1conf)

    info = RECYCLABILITY.get(top1_cls, RECYCLABILITY["Others"])
    symbol = RESIN_SYMBOLS.get(top1_cls, "♹")

    with col2:
        st.markdown(f"## {symbol} {top1_cls}")
        st.markdown(f"**{info['name_en']}** (Code {info['code']})")
        st.progress(top1_conf, text=f"Confidence: {top1_conf:.1%}")

        if info["recyclable"]:
            st.success("✅ Recyclable")
        else:
            st.error("❌ Non-recyclable")

    # Top 3 predictions
    st.subheader("📊 Top Predictions")
    top5_indices = probs.top5
    top5_confs = probs.top5conf.tolist()
    for idx, conf in zip(top5_indices[:3], top5_confs[:3]):
        cls_name = model.names[idx]
        st.progress(float(conf), text=f"{cls_name}: {conf:.1%}")

    # Guidance
    st.subheader("♻️ Recycling Guidance")
    with st.spinner("Getting guidance..."):
        guidance = get_guidance(top1_cls, info["recyclable"])
    st.info(guidance)
