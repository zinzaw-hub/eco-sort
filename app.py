# ==========================================
# PAGE VIEW: LEARN SECTION (UPDATED WITH GOOGLE DRIVE VIDEO & FIXED ALIGNMENT)
# ==========================================
def render_learn_page():
    th = st.session_state["_theme"]
    
    st.markdown("""
    <div class="eco-header">
        <div class="eco-title">Learn</div>
        <div class="eco-subtitle">Plastic Types &amp; Recycling Basics</div>
    </div>
    """, unsafe_allow_html=True)

    # ---------- VIDEO SECTION (Google Drive) ----------
    st.markdown('<div class="section-title">🎬 Recycling Example Video</div>', unsafe_allow_html=True)
    
    # ခင်ဗျားရဲ့ Google Drive Video Link
    video_url = "https://drive.google.com/uc?export=download&id=1lDlYJQ7ZwCcjRTyHn4-0V-7MnW_7pT7d"
    
    try:
        st.video(video_url)
    except Exception as e:
        st.warning(f"⚠️ Video ဖွင့်လို့မရပါ။ နောက်မှပြန်ကြည့်ပါ။ Error: {e}")
        # Fallback Video (YouTube)
        st.video("https://www.youtube.com/watch?v=6jQ7y_qQYUA")

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
                🗑️ Step 1: Collection
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
                🔄 Step 2: Sorting
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
                🧼 Step 3: Cleaning
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
