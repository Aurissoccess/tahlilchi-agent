import streamlit as st
import google.generativeai as genai
import os
import time
from dotenv import load_dotenv
from PIL import Image

# .env faylini yuklash
load_dotenv()

# Sahifa sozlamalari
st.set_page_config(
    page_title="Tahlilchi AI Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Dizayn (CSS)
st.markdown("""
<style>
    /* Asosiy fon va matn */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #ffffff;
    }
    
    /* Sidebar dizayni */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 215, 0, 0.2);
    }
    
    /* Tugmalar */
    .stButton>button {
        background: linear-gradient(45deg, #ffd700, #ff8c00);
        color: #000000;
        font-weight: bold;
        border: none;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
    }
    
    /* Chat xabarlari */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Sarlavha */
    h1 {
        color: #ffd700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        font-family: 'Outfit', sans-serif;
    }
    
    /* Glassmorphism card */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# API sozlamalari
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    with st.sidebar:
        st.warning("API Key topilmadi. Iltimos, kiriting:")
        GEMINI_API_KEY = st.text_input("Gemini API Key", type="password")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# System Instruction (AI Studio'dan olingan)
SYSTEM_INSTRUCTION = """
Sen foydalanuvchining shaxsiy 'Bilimlar Bazasi' (Knowledge Base) bo'yicha ekspert-tahlilchi va professional yordamchisan. Sening asosiy vazifang – foydalanuvchi taqdim etgan bilimlar bazasidagi (audio fayllar, transkripsiya qilingan matnlar yoki hujjatlar) ma'lumotlarni tahlil qilish va shu ma'lumotlar asosida savollarga aniq, lisoniy va mantiqiy javob berishdir.

Sening asosiy qoidalaring:
1. FAQAT berilgan materiallar (audio/matn) asosida javob ber. Agar ma'lumot yetarli bo'lmasa, buni ochiq ayting.
2. Professional, tahliliy va hurmatli tonda bo'l.
3. Javoblaringni Markdown formatida (sarlavhalar, ro'yxatlar, qalin matn) chiroyli tuzing.
4. Foydalanuvchiga bilimlar bazasidagi eng muhim nuqtalarni topishga yordam ber.
"""

# Modelni yaratish
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# Sidebar - Fayl yuklash
with st.sidebar:
    st.title("📂 Bilimlar Bazasi")
    uploaded_file = st.file_uploader("Audio fayl yuklang (MP3, WAV, M4A)", type=["mp3", "wav", "m4a", "ogg"])
    
    if uploaded_file:
        if uploaded_file.name not in [f.name for f in st.session_state.uploaded_files]:
            with st.spinner("Fayl tahlil qilinmoqda..."):
                # Faylni vaqtincha saqlash
                os.makedirs("temp_uploads", exist_ok=True)
                file_path = os.path.join("temp_uploads", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Gemini'ga yuklash
                gemini_file = genai.upload_file(path=file_path)
                
                # Fayl tayyor bo'lishini kutish
                while gemini_file.state.name == "PROCESSING":
                    time.sleep(2)
                    gemini_file = genai.get_file(gemini_file.name)
                
                st.session_state.uploaded_files.append({
                    "name": uploaded_file.name,
                    "gemini_file": gemini_file
                })
                st.success(f"Yuklandi: {uploaded_file.name}")
    
    st.divider()
    if st.button("Chatni tozalash"):
        st.session_state.messages = []
        st.rerun()

# Asosiy interfeys
st.title("🧠 Tahlilchi AI Agent")
st.markdown(f'<div class="glass-card">Hozirda <b>{len(st.session_state.uploaded_files)}</b> ta fayl asosida tahlil olib borilmoqda.</div>', unsafe_allow_html=True)

# Chat tarixini ko'rsatish
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Savolingizni bu yerga yozing..."):
    # Foydalanuvchi xabari
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AI javobi
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Fayllarni yuborish uchun tayyorlash
            input_content = [prompt]
            for f in st.session_state.uploaded_files:
                input_content.insert(0, f["gemini_file"])
            
            # Gemini javobi
            response = model.generate_content(input_content, stream=True)
            
            for chunk in response:
                full_response += chunk.text
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Xato yuz berdi: {e}")

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 50px; opacity: 0.5;">
    Tahlilchi AI Agent v1.0 | Google Gemini AI bilan ishlaydi
</div>
""", unsafe_allow_html=True)
