import streamlit as st
import time
import random

# ==========================================
# 1. SETUP & LIBRARY
# ==========================================
st.set_page_config(
    page_title="Social Video Gen v2.0",
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
        if k.startswith("AIza") and len(k) > 20:
            cleaned.append(k)
    return list(set(cleaned))

def check_key_health(api_key):
    try:
        genai.configure(api_key=api_key, transport='rest')
        models = list(genai.list_models())
        found_model = None
        candidates = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
        # Prioritas Model (Flash -> Pro -> Default)
        for m in candidates:
            if 'flash' in m and '1.5' in m: found_model = m; break
        if not found_model:
            for m in candidates:
                if 'pro' in m and '1.5' in m: found_model = m; break
        if not found_model and candidates: found_model = candidates[0]
            
        if not found_model: return False, "No Model Found", None

        # Test Ping
        model = genai.GenerativeModel(found_model)
        model.generate_content("Hi", generation_config={'max_output_tokens': 1})
        return True, "Active", found_model
    except Exception as e:
        err = str(e)
        if "429" in err: return False, "Quota Limit", None
        if "400" in err: return False, "Invalid Key", None
        return False, f"Error: {err[:15]}...", None

# ==========================================
# 3. SIDEBAR: KEY MANAGER
# ==========================================
st.sidebar.title("🔑 AI Key Manager")

if 'active_keys_data' not in st.session_state:
    st.session_state.active_keys_data = []

raw_input = st.sidebar.text_area("Paste Gemini API Keys:", height=100, placeholder="AIzaSy...")

if st.sidebar.button("🔍 Validasi & Sync", type="primary"):
    candidates = clean_keys(raw_input)
    if not candidates:
        st.sidebar.error("❌ Key kosong.")
    else:
        valid_data = []
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        
        for i, key in enumerate(candidates):
            status_text.text(f"Cek Key {i+1}...")
            is_alive, msg, model_name = check_key_health(key)
            if is_alive:
                valid_data.append({'key': key, 'model': model_name})
            progress_bar.progress((i + 1) / len(candidates))
            
        st.session_state.active_keys_data = valid_data
        status_text.empty()
        
        if valid_data:
            st.sidebar.success(f"🎉 {len(valid_data)} Key Siap!")
        else:
            st.sidebar.error("💀 Semua Key Gagal.")

if st.session_state.active_keys_data:
    st.sidebar.info(f"🟢 {len(st.session_state.active_keys_data)} Key Aktif")

# ==========================================
# 4. LOGIKA VIDEO & NEGATIVE PROMPT
# ==========================================

SAFETY = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

MOVES_CINEMATIC = ["Slow Dolly In", "Truck Left/Right", "Low Angle Tracking", "Orbit / Arc Shot", "Rack Focus", "Static Tripod"]
MOVES_DYNAMIC = ["Handheld Shake (POV)", "Fast Zoom In", "Whip Pan", "Crash Zoom", "Drone FPV Fly-through", "GoPro Fish Eye"]
MOVES_PRODUCT = ["360 Rotation", "Slow Pan Up (Reveal)", "Macro Focus Shift", "Top Down Slider", "Lighting Change"]

# --- AUTO NEGATIVE PROMPTS ---
NEG_KLING = "nsfw, low quality, blurry, distorted, morphing, extra limbs, bad anatomy, text, watermark, static, frozen, slideshow, jpeg artifacts"
NEG_LUMA = "distortion, warping, morphing, melting, floating objects, unnatural physics, bad simulation, glitch, low resolution"
NEG_HAILUO = "text, watermark, logo, bad composition, blurry, low quality, cartoon, illustration, painting, drawing"
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
    else: return NEG_HAILUO

# ==========================================
# 5. UI GENERATOR
# ==========================================
st.title("🎬 Social Video Gen v2.0")
st.caption("AI Video Prompt Generator: Kling, Veo, Luma, Hailuo")

video_platform = st.radio(
    "🎥 Target Platform:", 
    ["Kling AI", "Google Veo (VideoFX)", "Luma Dream Machine", "Hailuo / MiniMax"], 
    horizontal=True
)

col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("💡 Ide Video", placeholder="Contoh: Samurai walking in neon rain")
    niche = st.selectbox("🎯 Niche Konten:", ["Cinematic / Travel", "Vlog / POV / Action", "Product / Food Showcase"])

with col2:
    if video_platform == "Kling AI":
        ar_display = st.selectbox("📐 Rasio", ["--ar 9:16 (Vertical)", "--ar 16:9 (Landscape)"])
        limit_msg = "Format: Subject + Action + Env + Camera"
    elif video_platform == "Google Veo (VideoFX)":
        ar_display = "Auto (Set in Web)"
        limit_msg = "Format: Cinematic Narrative & Technical Terms"
    elif video_platform == "Luma Dream Machine":
        ar_display = "Auto (Set in Web)"
        limit_msg = "Format: Physics-focused Description"
    else:
        ar_display = "Auto (Set in Web)"
        limit_msg = "Format: Artistic & Poetic"
        
    qty = st.slider("🔢 Jumlah Variasi", 1, 10, 5)
    
    use_neg = st.checkbox("Gunakan Negative Prompt Otomatis", value=True)
    st.caption(f"🛡️ {limit_msg}")

st.markdown("---")

# ==========================================
# 6. EKSEKUSI
# ==========================================
if st.button(f"🚀 Generate Prompts", type="primary"):
    
    keys_data = st.session_state.active_keys_data
    
    if not keys_data:
        st.error("⛔ Validasi Key dulu di Sidebar!")
    elif not topic:
        st.warning("⚠️ Masukkan Ide Video.")
    else:
        results = []
        st.sidebar.markdown("---")
        error_log = st.sidebar.expander("📜 Log Error", expanded=False)
        pbar = st.progress(0)
        
        movements = get_movements(niche, qty)
        neg_prompt_text = get_negative(video_platform) if use_neg else ""
        key_idx = 0
        
        for i in range(qty):
            movement = movements[i]
            success = False
            attempts = 0
            
            while not success and attempts < len(keys_data):
                current_data = keys_data[key_idx]
                try:
                    genai.configure(api_key=current_data['key'], transport='rest')
                    model = genai.GenerativeModel(current_data['model'])
                    
                    # --- SYSTEM PROMPT LOGIC ---
                    if video_platform == "Kling AI":
                        ar_val = ar_display.split(' ')[0]
                        sys_prompt = f"""
                        Role: Professional AI Video Director for Kling AI.
                        Task: Write a structured prompt.
                        Subject: {topic}.
                        Camera Movement: {movement}.
                        Atmosphere: Realistic, 8k.
                        
                        RULES:
                        1. Structure: [Subject Description] + [Specific Action] + [Environment] + [Camera Movement].
                        2. Make sure the action is LOOPABLE if possible.
                        3. NO intro/outro.
                        4. Add {ar_val} at the end.
                        """
                    elif video_platform == "Google Veo (VideoFX)":
                        sys_prompt = f"""
                        Role: Expert Cinematographer for Google Veo.
                        Task: Create a highly detailed cinematic prompt.
                        Subject: {topic}.
                        Camera Movement: {movement}.
                        
                        RULES:
                        1. Use natural, flowing sentences (No formatting like 'Subject: ...').
                        2. Include cinematic terminology (e.g., 'shot on 35mm', 'anamorphic lens', 'golden hour').
                        3. Explicitly describe the lighting, texture, and the feeling of the scene.
                        4. Start with the main action immediately.
                        5. Incorporate '{movement}' naturally into the sentence description.
                        """
                    elif video_platform == "Luma Dream Machine":
                        sys_prompt = f"""
                        Role: Luma Labs Expert.
                        Task: Write a prompt for Luma.
                        Subject: {topic}.
                        Movement: {movement}.
                        
                        RULES:
                        1. Start with the motion.
                        2. Describe physics (gravity, wind, collision).
                        3. Include '{movement}'.
                        4. Output: Raw prompt text only.
                        """
                    else: # Hailuo
                        sys_prompt = f"""
                        Role: Cinematographer.
                        Task: Detailed video description for Hailuo.
                        Subject: {topic}.
                        Movement: {movement}.
                        RULES: Focus on lighting and time flow. Raw text only.
                        """
                    
                    response = model.generate_content(sys_prompt, safety_settings=SAFETY)
                    
                    if response.text:
                        clean_p = response.text.strip().replace('"', '').replace("`", "").replace("Prompt:", "")
                        if video_platform == "Kling AI" and "--camera" not in clean_p:
                            clean_p += f" --camera_control {movement.lower().replace(' ', '_')}"
                            
                        results.append((movement, clean_p, neg_prompt_text))
                        success = True
                
                except Exception as e:
                    error_log.warning(f"Key #{key_idx+1}: {str(e)}")
                    pass
                
                key_idx = (key_idx + 1) % len(keys_data)
                if success: break
                else: attempts += 1
                time.sleep(0.5)
            
            pbar.progress((i+1)/qty)
        
        if results:
            st.success(f"✅ Selesai! {len(results)} Video Prompts.")
            
            # Text File Preparation
            txt_out = f"PLATFORM: {video_platform}\nTOPIK: {topic}\n\n"
            for idx, r in enumerate(results):
                txt_out += f"[{r[0]}]\nPOSITIVE: {r[1]}\n"
                if r[2]: txt_out += f"NEGATIVE: {r[2]}\n"
                txt_out += "\n" + "-"*20 + "\n\n"
            
            st.download_button("📥 Download .txt", txt_out, f"video_prompts_{topic}.txt")
            
            # Display Results
            for idx, (move, pos, neg) in enumerate(results):
                st.markdown(f"**#{idx+1} {move}**")
                
                st.markdown('<span class="pos-label">✅ Positive Prompt</span>', unsafe_allow_html=True)
                st.code(pos, language="text")
                
                if neg:
                    st.markdown('<span class="neg-label">🚫 Negative Prompt</span>', unsafe_allow_html=True)
                    st.code(neg, language="text")
                
                st.markdown(f"<div class='char-count'>Length: {len(pos)} chars</div>", unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.error("❌ Gagal. Cek Koneksi/Key.")