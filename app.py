import streamlit as st
import time
import random
import json
import os
from datetime import datetime

# ==========================================
# 1. SETUP & LIBRARY
# ==========================================
st.set_page_config(
    page_title="Social Video Gen v2.5",
    page_icon="🎬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stCodeBlock {margin-bottom: 5px;}
    div[data-testid="stExpander"] {border: 1px solid #e0e0e0; border-radius: 8px;}
    .last-key-box {
        background-color: #e8f5e9; 
        padding: 10px; 
        border-radius: 8px; 
        border-left: 4px solid #4CAF50;
        margin-top: 10px;
    }
    .timestamp {font-size: 11px; color: #555; font-family: monospace;}
    .key-text {font-weight: bold; font-family: monospace; color: #2e7d32;}
    .img-box {border: 2px dashed #ccc; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 15px;}
</style>
""", unsafe_allow_html=True)

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    st.error("❌ Library Error. Requirements: google-generativeai>=0.8.3")
    st.stop()

# ==========================================
# 2. UTILITIES (HISTORY & KEY)
# ==========================================
LAST_KEY_FILE = 'last_key.json'

def save_last_key(api_key, model_name):
    data = {
        'key': api_key,
        'model': model_name,
        'time': datetime.now().strftime("%d/%m %H:%M")
    }
    with open(LAST_KEY_FILE, 'w') as f:
        json.dump(data, f)

def load_last_key():
    if os.path.exists(LAST_KEY_FILE):
        try:
            with open(LAST_KEY_FILE, 'r') as f: return json.load(f)
        except: return None
    return None

def clean_keys(raw_text):
    if not raw_text: return []
    candidates = raw_text.replace('\n', ',').split(',')
    cleaned = []
    for c in candidates:
        k = c.strip().replace('"', '').replace("'", "")
        if k.startswith("AIza") and len(k) > 20: cleaned.append(k)
    return list(set(cleaned))

def check_key_health(api_key):
    try:
        genai.configure(api_key=api_key, transport='rest')
        models = list(genai.list_models())
        found_model = None
        candidates = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        for m in candidates:
            if 'flash' in m and '1.5' in m: found_model = m; break
        if not found_model:
            for m in candidates:
                if 'pro' in m and '1.5' in m: found_model = m; break
        if not found_model and candidates: found_model = candidates[0]
        if not found_model: return False, "No Model Found", None
        
        model = genai.GenerativeModel(found_model)
        model.generate_content("Hi", generation_config={'max_output_tokens': 1})
        return True, "Active", found_model
    except Exception as e: return False, str(e), None

# ==========================================
# 3. SIDEBAR: KEY MANAGER (SIMPLIFIED)
# ==========================================
st.sidebar.title("⚙️ Setup")

# Init Session
if 'active_keys_data' not in st.session_state: 
    st.session_state.active_keys_data = []

# --- A. INPUT KEY BARU ---
with st.sidebar.expander("🔑 API Key Input", expanded=True):
    raw_input = st.text_area("Paste Key:", height=70, placeholder="AIzaSy...")
    if st.button("Validasi Key Baru"):
        candidates = clean_keys(raw_input)
        if not candidates: st.error("Key kosong.")
        else:
            valid_data = []
            status = st.empty()
            for key in candidates:
                status.text("Checking...")
                is_alive, msg, model = check_key_health(key)
                if is_alive: 
                    valid_data.append({'key': key, 'model': model})
                    # Auto save key pertama ke last history
                    save_last_key(key, model)
            
            st.session_state.active_keys_data = valid_data
            status.empty()
            if valid_data: st.success(f"{len(valid_data)} Key Aktif!")
            else: st.error("Key Gagal.")

# --- B. LAST USED KEY (SIMPLE BLOCK) ---
last_k = load_last_key()
if last_k:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div class='last-key-box'>
        <div class='key-text'>🔑 ...{last_k['key'][-6:]}</div>
        <div class='timestamp'>🕒 {last_k['time']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🔄 Pakai Key Ini"):
        # Cek apakah key sudah aktif di sesi ini
        is_exist = any(d['key'] == last_k['key'] for d in st.session_state.active_keys_data)
        if not is_exist:
            # Re-validasi cepat (opsional, tapi aman)
            st.session_state.active_keys_data.append({'key': last_k['key'], 'model': last_k['model']})
            st.sidebar.success("Key dimuat!")
        else:
            st.sidebar.info("Key sudah siap.")

# Indikator Status
if st.session_state.active_keys_data:
    st.sidebar.success(f"🟢 Siap Generate")
else:
    st.sidebar.warning("🔴 Masukkan Key")

# ==========================================
# 4. MAIN LAYOUT
# ==========================================
st.title("🎬 Social Video Gen v2.5")
st.caption("AI Video Prompt Generator • Text-to-Video & Image-to-Video")

video_platform = st.radio("🎥 Target Platform:", ["Kling AI", "Google Veo (VideoFX)", "Luma Dream Machine"], horizontal=True)

# --- IMAGE UPLOADER (LAYAR UTAMA) ---
st.markdown("### 🖼️ Referensi Gambar (I2V)")
with st.container(border=True):
    col_img1, col_img2 = st.columns([1, 3])
    with col_img1:
        uploaded_file = st.file_uploader("Upload JPG/PNG", type=["jpg", "png", "jpeg", "webp"], label_visibility="collapsed")
    with col_img2:
        if uploaded_file:
            st.image(uploaded_file, width=150, caption="Gambar Terupload")
            st.caption("✅ Mode Image-to-Video Aktif. Prompt akan fokus pada gerakan.")
        else:
            st.info("ℹ️ Upload gambar jika ingin mode Image-to-Video. Jika kosong, mode Text-to-Video.")

# --- TABS ---
tab1, tab2 = st.tabs(["🎬 Creative / Cinematic", "🛒 Affiliate / Produk"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        topic_c = st.text_input("💡 Ide Video (Creative)", placeholder="Contoh: Cyberpunk street in rain")
        niche_c = st.selectbox("🎯 Niche:", ["Product / Food Showcase", "Cinematic / Travel", "Vlog / POV / Action"])
    with col2:
        qty_c = st.slider("🔢 Jumlah Variasi", 1, 10, 5, key="qty_c")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input("📦 Nama Produk", placeholder="Contoh: TWS F9")
        product_desc = st.text_area("📝 Fitur/Deskripsi", placeholder="Paste deskripsi produk...", height=100)
    with col2:
        marketing_angle = st.selectbox("🎣 Hook Marketing", ["Problem -> Solution", "ASMR Unboxing", "User Testimonial", "Before vs After"])
        qty_a = st.slider("🔢 Jumlah Variasi", 1, 10, 5, key="qty_a")

st.markdown("---")
c1, c2 = st.columns(2)
with c1:
    ar_display = st.selectbox("📐 Rasio (Kling Only)", ["--ar 9:16 (Vertical)", "--ar 16:9 (Landscape)"]) if video_platform == "Kling AI" else "Auto"
with c2:
    use_neg = st.checkbox("Auto Negative Prompt", value=True)

# ==========================================
# 5. LOGIKA GENERATE
# ==========================================
# Data Constants
SAFETY = {HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE}
MOVES = {
    "Cinematic / Travel": ["Slow Dolly In", "Truck Left/Right", "Orbit Shot", "Rack Focus", "Static Tripod"],
    "Vlog / POV / Action": ["Handheld Shake (POV)", "Fast Zoom In", "Whip Pan", "Crash Zoom", "Drone FPV"],
    "Product / Food Showcase": ["360 Rotation", "Slow Pan Up (Reveal)", "Macro Focus Shift", "Top Down Slider"]
}
NEGATIVES = {
    "Kling": "nsfw, low quality, blurry, distorted, morphing, extra limbs, bad anatomy, text, watermark, static, frozen, slideshow, jpeg artifacts, ugly hands",
    "Luma": "distortion, warping, morphing, melting, floating objects, unnatural physics, glitch, low resolution",
    "Veo": "distorted, blurry, low resolution, visual artifacts, unstable motion, morphing"
}

if st.button(f"🚀 Generate Prompts", type="primary"):
    keys_data = st.session_state.active_keys_data
    active_tab = "creative" if topic_c else "affiliate" if product_name else None
    is_i2v = uploaded_file is not None
    
    if not keys_data: st.error("⛔ Validasi Key dulu di Sidebar!")
    elif not active_tab: st.warning("⚠️ Masukkan Topik/Produk.")
    else:
        results = []
        pbar = st.progress(0)
        
        if active_tab == "creative":
            qty = qty_c
            base_inputs = random.sample(MOVES[niche_c] * 2, qty)
            main_topic = topic_c
        else:
            qty = qty_a
            base_inputs = [marketing_angle] * qty 
            main_topic = f"{product_name} - {product_desc}"

        neg_text = NEGATIVES["Kling"] if "Kling" in video_platform else NEGATIVES["Luma"] if "Luma" in video_platform else NEGATIVES["Veo"]
        key_idx = 0
        
        for i in range(qty):
            input_var = base_inputs[i]
            success = False; attempts = 0
            while not success and attempts < len(keys_data):
                current = keys_data[key_idx]
                try:
                    genai.configure(api_key=current['key'], transport='rest')
                    model = genai.GenerativeModel(current['model'])
                    
                    i2v_instr = "CRITICAL: User provided REF IMAGE. Prompt must focus ONLY on ACTION/MOTION applied to the image." if is_i2v else "Describe visually from scratch."
                    
                    if active_tab == "creative":
                        if video_platform == "Kling AI":
                            ar = ar_display.split(' ')[0]
                            sys = f"Role: AI Director Kling. Mode: {'I2V' if is_i2v else 'T2V'}. Subject: {main_topic}. Move: {input_var}. {i2v_instr}. Rules: Structure [Action] + [Env] + [Camera]. Add {ar}."
                        elif video_platform == "Luma Dream Machine":
                            sys = f"Role: Luma Expert. Mode: {'I2V' if is_i2v else 'T2V'}. Subject: {main_topic}. Move: {input_var}. {i2v_instr}. Rules: Physics focus. Start with verb."
                        else: # Veo
                             sys = f"Role: Cinematographer. Subject: {main_topic}. Move: {input_var}. {i2v_instr}. Rules: Cinematic."
                    else: # Affiliate
                        sys = f"Role: TikTok Shop Creator. Mode: {'I2V' if is_i2v else 'T2V'}. Product: {main_topic}. Angle: {input_var}. {i2v_instr}. Rules: Selling visuals, no text."

                    resp = model.generate_content(sys, safety_settings=SAFETY)
                    if resp.text:
                        clean_p = resp.text.strip().replace('"', '').replace("`", "").replace("Prompt:", "")
                        if video_platform == "Kling AI" and active_tab == "creative" and "--camera" not in clean_p and not is_i2v:
                            clean_p += f" --camera_control {input_var.lower().replace(' ', '_')}"
                        
                        results.append((input_var, clean_p))
                        save_last_key(current['key'], current['model']) # Auto Update Last Key
                        success = True
                except Exception: pass
                key_idx = (key_idx + 1) % len(keys_data)
                if success: break
                else: attempts += 1
                time.sleep(0.5)
            pbar.progress((i+1)/qty)
        
        if results:
            st.success(f"✅ Selesai! {len(results)} Prompts.")
            for idx, (move, pos) in enumerate(results):
                st.markdown(f"**#{idx+1} {move}**")
                st.code(pos, language="text")
                if use_neg: 
                    with st.expander("Lihat Negative Prompt"):
                        st.code(neg_text, language="text")
        else: st.error("❌ Gagal.")
