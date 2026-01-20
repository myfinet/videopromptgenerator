import streamlit as st
import time
import random

# ==========================================
# 1. SETUP & LIBRARY
# ==========================================
st.set_page_config(
    page_title="Social Video Gen v2.3",
    page_icon="🎬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stCodeBlock {margin-bottom: 5px;}
    div[data-testid="stExpander"] {border: 1px solid #e0e0e0; border-radius: 8px;}
    .neg-label {font-size: 12px; color: #d32f2f; font-weight: bold; margin-top: 5px;}
    .pos-label {font-size: 12px; color: #2e7d32; font-weight: bold;}
    .i2v-badge {background-color: #e3f2fd; padding: 5px; border-radius: 4px; font-weight: bold; color: #1565c0; font-size: 12px; margin-bottom: 10px; display: inline-block;}
    .affiliate-badge {background-color: #fff9c4; padding: 5px; border-radius: 4px; font-weight: bold; color: #fbc02d; font-size: 12px;}
    .char-count {font-size: 11px; color: #666; font-family: monospace; margin-bottom: 15px;}
</style>
""", unsafe_allow_html=True)

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    st.error("❌ Library Error. Requirements: google-generativeai>=0.8.3")
    st.stop()

# ==========================================
# 2. FUNGSI UTILITIES
# ==========================================
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
# 3. SIDEBAR & DATA
# ==========================================
st.sidebar.title("🔑 AI Key Manager")
if 'active_keys_data' not in st.session_state: st.session_state.active_keys_data = []
raw_input = st.sidebar.text_area("Paste Gemini API Keys:", height=100, placeholder="AIzaSy...")
if st.sidebar.button("🔍 Validasi & Sync", type="primary"):
    candidates = clean_keys(raw_input)
    if not candidates: st.sidebar.error("❌ Key kosong.")
    else:
        valid_data = []
        progress_bar = st.sidebar.progress(0)
        for i, key in enumerate(candidates):
            is_alive, msg, model_name = check_key_health(key)
            if is_alive: valid_data.append({'key': key, 'model': model_name})
            progress_bar.progress((i + 1) / len(candidates))
        st.session_state.active_keys_data = valid_data
        if valid_data: st.sidebar.success(f"🎉 {len(valid_data)} Key Siap!")
        else: st.sidebar.error("💀 Semua Key Gagal.")
if st.session_state.active_keys_data: st.sidebar.info(f"🟢 {len(st.session_state.active_keys_data)} Key Aktif")

SAFETY = {HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE}
MOVES_CINEMATIC = ["Slow Dolly In", "Truck Left/Right", "Low Angle Tracking", "Orbit / Arc Shot", "Rack Focus", "Static Tripod"]
MOVES_DYNAMIC = ["Handheld Shake (POV)", "Fast Zoom In", "Whip Pan", "Crash Zoom", "Drone FPV Fly-through"]
MOVES_PRODUCT = ["360 Rotation", "Slow Pan Up (Reveal)", "Macro Focus Shift", "Top Down Slider", "Lighting Change"]
HOOKS_AFFILIATE = ["Problem -> Solution", "ASMR Unboxing", "User Testimonial", "Before vs After"]
NEG_KLING = "nsfw, low quality, blurry, distorted, morphing, extra limbs, bad anatomy, text, watermark, static, frozen, slideshow, jpeg artifacts, ugly hands, extra fingers"
NEG_LUMA = "distortion, warping, morphing, melting, floating objects, unnatural physics, bad simulation, glitch, low resolution"
NEG_VEO = "distorted, blurry, low resolution, visual artifacts, unstable motion, morphing, grainy, oversaturated"

def get_movements(niche, qty):
    if niche == "Cinematic / Travel": base = MOVES_CINEMATIC
    elif niche == "Vlog / POV / Action": base = MOVES_DYNAMIC
    else: base = MOVES_PRODUCT
    if qty > len(base): return random.sample(base * 2, qty)
    return random.sample(base, qty)

def get_negative(platform):
    if "Kling" in platform: return NEG_KLING
    elif "Luma" in platform: return NEG_LUMA
    elif "Veo" in platform: return NEG_VEO
    else: return NEG_KLING

# ==========================================
# 5. UI GENERATOR (UPDATED POSITION)
# ==========================================
st.title("🎬 Social Video Gen v2.3")
st.caption("Support: Text-to-Video & Image-to-Video (I2V)")

# 1. Image Uploader (POSISI PALING ATAS & MENCOLOK)
with st.container():
    st.info("🖼️ **Image Reference (Opsional)**: Upload gambar di bawah ini jika ingin mode Image-to-Video.")
    uploaded_file = st.file_uploader("Klik 'Browse files' untuk upload gambar referensi:", type=["jpg", "png", "jpeg", "webp"])
    if uploaded_file:
        st.success("✅ Gambar Terdeteksi! Prompt akan disesuaikan untuk Gerakan (Motion).")

st.markdown("---")

# 2. Platform Selector
video_platform = st.radio("🎥 Target Platform:", ["Kling AI", "Google Veo (VideoFX)", "Luma Dream Machine"], horizontal=True)

# 3. Tabs
tab1, tab2 = st.tabs(["🎬 Creative / Cinematic", "🛒 Affiliate / Produk"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        topic_c = st.text_input("💡 Ide Video (Creative)", placeholder="Contoh: Electric car charging port close up")
        niche_c = st.selectbox("🎯 Niche:", ["Product / Food Showcase", "Cinematic / Travel", "Vlog / POV / Action"])
    with col2:
        qty_c = st.slider("🔢 Jumlah (Creative)", 1, 10, 5, key="qty_c")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input("📦 Nama Produk", placeholder="Contoh: TWS F9")
        product_desc = st.text_area("📝 Fitur/Deskripsi", placeholder="Paste deskripsi produk...", height=100)
    with col2:
        marketing_angle = st.selectbox("🎣 Strategi Marketing", HOOKS_AFFILIATE)
        qty_a = st.slider("🔢 Jumlah (Affiliate)", 1, 10, 5, key="qty_a")

st.markdown("---")
c1, c2 = st.columns(2)
with c1:
    if video_platform == "Kling AI":
        ar_display = st.selectbox("📐 Rasio", ["--ar 9:16 (Vertical)", "--ar 16:9 (Landscape)"])
    else: ar_display = "Auto"
with c2:
    use_neg = st.checkbox("Gunakan Negative Prompt Otomatis", value=True)

# ==========================================
# 6. EKSEKUSI
# ==========================================
if st.button(f"🚀 Generate Prompts", type="primary"):
    keys_data = st.session_state.active_keys_data
    active_tab = "creative" if topic_c else "affiliate" if product_name else None
    is_i2v = uploaded_file is not None
    
    if not keys_data: st.error("⛔ Validasi Key dulu!")
    elif not active_tab: st.warning("⚠️ Masukkan Topik/Produk.")
    else:
        results = []
        pbar = st.progress(0)
        
        if active_tab == "creative":
            qty = qty_c
            base_inputs = get_movements(niche_c, qty)
            main_topic = topic_c
        else:
            qty = qty_a
            base_inputs = [marketing_angle] * qty 
            main_topic = f"{product_name} - {product_desc}"

        neg_prompt_text = get_negative(video_platform) if use_neg else ""
        key_idx = 0
        
        for i in range(qty):
            input_var = base_inputs[i]
            success = False; attempts = 0
            while not success and attempts < len(keys_data):
                current_data = keys_data[key_idx]
                try:
                    genai.configure(api_key=current_data['key'], transport='rest')
                    model = genai.GenerativeModel(current_data['model'])
                    
                    # --- I2V INSTRUCTION LOGIC ---
                    i2v_instruction = ""
                    if is_i2v:
                        i2v_instruction = "CRITICAL: The user is providing an REFERENCE IMAGE. The prompt must focus ONLY on the ACTION, MOVEMENT, and ATMOSPHERE applied to that specific image. Do NOT describe the static scene from scratch. Keep it concise."
                    else:
                        i2v_instruction = "Describe the entire scene visually from scratch."

                    # --- PROMPT CONSTRUCTION ---
                    if active_tab == "creative":
                        if video_platform == "Kling AI":
                            ar_val = ar_display.split(' ')[0]
                            sys_prompt = f"""
                            Role: AI Video Director for Kling AI. Mode: {'Image-to-Video' if is_i2v else 'Text-to-Video'}.
                            Subject: {main_topic}. Movement: {input_var}.
                            {i2v_instruction}
                            Rules: Structure [Subject Action] + [Env Details] + [Camera]. Add {ar_val}.
                            """
                        elif video_platform == "Luma Dream Machine":
                            sys_prompt = f"""
                            Role: Luma Expert. Mode: {'Image-to-Video' if is_i2v else 'Text-to-Video'}.
                            Subject: {main_topic}. Movement: {input_var}.
                            {i2v_instruction}
                            Rules: Start with motion verb. Focus on physics.
                            """
                        else: # Veo
                             sys_prompt = f"Role: Cinematographer. Subject: {main_topic}. Move: {input_var}. {i2v_instruction} Rules: Cinematic terms."
                    else: # Affiliate
                        sys_prompt = f"""
                        Role: TikTok Shop Video Creator. Mode: {'Image-to-Video' if is_i2v else 'Text-to-Video'}.
                        Product: {main_topic}. Angle: {input_var}.
                        {i2v_instruction}
                        Rules: Focus on selling visuals, no text overlays. Under 800 chars.
                        """

                    response = model.generate_content(sys_prompt, safety_settings=SAFETY)
                    if response.text:
                        clean_p = response.text.strip().replace('"', '').replace("`", "").replace("Prompt:", "")
                        if video_platform == "Kling AI" and active_tab == "creative" and "--camera" not in clean_p and not is_i2v:
                            clean_p += f" --camera_control {input_var.lower().replace(' ', '_')}"
                        results.append((input_var, clean_p, neg_prompt_text))
                        success = True
                except Exception: pass
                key_idx = (key_idx + 1) % len(keys_data)
                if success: break
                else: attempts += 1
                time.sleep(0.5)
            pbar.progress((i+1)/qty)
        
        if results:
            st.success(f"✅ Selesai! {len(results)} Prompts.")
            txt_out = f"PLATFORM: {video_platform}\nMODE: {'I2V (Pakai Gambar)' if is_i2v else 'T2V (Teks Saja)'}\nTOPIK: {main_topic}\n\n"
            for idx, r in enumerate(results):
                txt_out += f"[{r[0]}]\nPOSITIVE: {r[1]}\n"
                if r[2]: txt_out += f"NEGATIVE: {r[2]}\n"
                txt_out += "\n" + "-"*20 + "\n\n"
            st.download_button("📥 Download .txt", txt_out, f"prompts.txt")
            
            for idx, (move, pos, neg) in enumerate(results):
                st.markdown(f"**#{idx+1} Strategy: {move}**")
                if is_i2v: st.markdown('<span class="i2v-badge">🖼️ Gunakan dengan Gambar Referensi</span>', unsafe_allow_html=True)
                st.markdown('<span class="pos-label">✅ Positive Prompt</span>', unsafe_allow_html=True)
                st.code(pos, language="text")
                if neg:
                    st.markdown('<span class="neg-label">🚫 Negative Prompt</span>', unsafe_allow_html=True)
                    st.code(neg, language="text")
                st.markdown("---")
        else: st.error("❌ Gagal.")
