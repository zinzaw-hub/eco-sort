
import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np
import os
import plotly.graph_objects as go
from groq import Groq

st.set_page_config(page_title="EcoSort", page_icon="\u267b\ufe0f", layout="wide")

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

# ---------------- Resin code symbols (Unicode recycling symbols) ----------------
RESIN_SYMBOLS = {
    "PET": "\u2673", "HDPE": "\u2674", "PVC": "\u2675",
    "LDPE": "\u2676", "PP": "\u2677", "PS": "\u2678", "Other": "\u2679",
}

RECYCLABILITY = {
    "PET":   {"recyclable": True,  "code": "1", "name_en": "Polyethylene Terephthalate"},
    "HDPE":  {"recyclable": True,  "code": "2", "name_en": "High-Density Polyethylene"},
    "PVC":   {"recyclable": False, "code": "3", "name_en": "Polyvinyl Chloride"},
    "LDPE":  {"recyclable": True,  "code": "4", "name_en": "Low-Density Polyethylene"},
    "PP":    {"recyclable": True,  "code": "5", "name_en": "Polypropylene"},
    "PS":    {"recyclable": False, "code": "6", "name_en": "Polystyrene"},
    "Other": {"recyclable": False, "code": "7", "name_en": "Other / Mixed Plastics"},
}

# ---------------- Groq LLM guidance ----------------
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
    return YOLO("plastic_yolov8_v2.pt")

model = load_model()

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Settings")
    st.toggle("Dark mode", key="dark_mode", on_change=apply_theme)
    st.markdown("---")
    st.subheader("Global Plastic Waste by Type")
    labels = ["PET", "HDPE", "PVC", "LDPE", "PP", "PS", "Other"]
    values = [12, 17, 10, 15, 19, 8, 19]  # approximate share, illustrative
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4,
                                   marker=dict(colors=["#8a9a5b","#bfa76a","#a9b18f","#c9a66b",
                                                        "#6b7a4f","#d9c48f","#5c5c4d"]))])
    fig.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=280,
                       paper_bgcolor="rgba(0,0,0,0)", font_color="#3a3a30" if not st.session_state.dark_mode else "#f0ead6")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- Main ----------------
st.title("\u267b\ufe0f EcoSort - AI Plastic Classifier")
st.write("Upload a photo of plastic waste to identify its resin type and get recycling guidance.")

uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    col1, col2 = st.columns(2)

    with col1:
        st.image(image, caption="Uploaded Image", use_container_width=True)

    with st.spinner("Analyzing..."):
        results = model(image)

    with col2:
        r = results[0]
        annotated = r.plot()
        annotated_rgb = annotated[:, :, ::-1]
        st.image(annotated_rgb, caption="Detection Result", use_container_width=True)

    if len(r.boxes) == 0:
        st.warning("No plastic items detected. Try a clearer photo.")
    else:
        st.subheader("Detected Items")
        seen_types = set()
        for i, box in enumerate(r.boxes):
            cls_name = model.names[int(box.cls)]
            conf = float(box.conf)
            info = RECYCLABILITY.get(cls_name, RECYCLABILITY["Other"])
            symbol = RESIN_SYMBOLS.get(cls_name, "\u2679")

            with st.container():
                c1, c2, c3 = st.columns([1, 2, 2])
                with c1:
                    st.markdown(f"### {symbol} {cls_name} ({info['code']})")
                with c2:
                    st.progress(conf, text=f"Confidence: {conf:.1%}")
                with c3:
                    if info["recyclable"]:
                        st.success("\u2705 Recyclable")
                    else:
                        st.error("\u274c Non-recyclable")

                if cls_name not in seen_types:
                    seen_types.add(cls_name)
                    with st.expander(f"Recycling guidance for {cls_name}"):
                        guidance = get_guidance(cls_name, info["recyclable"])
                        st.write(guidance)
                st.markdown("---")
