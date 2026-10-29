import streamlit as st
import requests
import urllib.parse
from PIL import Image
from io import BytesIO
import time
from gtts import gTTS
import tempfile
import os

# --- FREE IMAGE FUNCTION ---
def generate_free_image(prompt, seed=42):
    # Pollinations - No API Key needed
    safe_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&model=flux&seed={seed}&nologo=true"
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception as e:
        st.error(f"Image Error: {e}")
    return None

def split_story(story):
    lines = [l.strip() for l in story.split('.') if l.strip()]
    # 5 hisso me baant do
    scenes = []
    for i in range(5):
        if i < len(lines):
            scenes.append(lines[i])
        else:
            scenes.append(lines[-1] if lines else "jungle me khargosh")
    return scenes[:5]

st.set_page_config(page_title="Meri Kahani - VIDEO PRO", page_icon="🎬", layout="wide")
st.title("🎬 میری کہانی - Video Pro (FREE)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("ہمارا کریکٹر لاک کریں")
    char_name = st.text_input("کریکٹر کا نام", "علی")
    char_look = st.text_area("کریکٹر کی شکل", "10 year old Pakistani boy with pent shirt, cute face, big eyes", height=100)
    style = st.selectbox("گرافک اسٹائل", ["3D Cartoon, ultra detailed, Pixar style", "Realistic Photo, 8k", "Anime style", "Disney style"])
    
    st.divider()
    st.header("📤 اپنی تصویریں ڈال کر ویڈیو بنائیں")
    uploaded_files = st.file_uploader("Character ki 1-5 Pictures Upload karo", type=["jpg","png","jpeg"], accept_multiple_files=True)
    if uploaded_files:
        st.success(f"{len(uploaded_files)} Tasveerein Upload ho gayin!")

st.subheader("کہانی لکھیں")
story_input = st.text_area("5 scenes me kahani likhein (har jumla ek scene banega)", "ایک گاؤں میں علی نام کا ایک غریب لڑکا رہتا تھا۔ وہ محنت کا پھل ڈھونڈ رہا تھا۔ اس کے والد ایک کسان تھے اور بڑی مشکل سے گھر کا خرچ پورا کرتے تھے۔ علی بڑا ہو کر ایک کامیاب انسان بننا چاہتا تھا لیکن اس کے پاس کتابیں خریدنے کے لیے پیسے بھی نہیں تھے۔ علی نے ہمت نہیں ہاری۔", height=150)

col1, col2 = st.columns([1,1])
with col1:
    gen_btn = st.button("🎨 پہلے تصویریں بنائیں (FREE)", type="primary", use_container_width=True)
with col2:
    video_btn = st.button("🎬 اب ویڈیو بنائیں", use_container_width=True)

if 'images' not in st.session_state:
    st.session_state.images = []

# --- GENERATE IMAGES ---
if gen_btn:
    if uploaded_files:
        # Agar user ne apni tasveerein di hain to wohi use karo
        imgs = []
        for f in uploaded_files:
            imgs.append(Image.open(f))
        st.session_state.images = imgs
        st.success("Aap ki upload ki hui tasveeron se video banegi!")
    else:
        # Nahi to kahani se FREE tasveerein banao
        scenes = split_story(story_input)
        st.session_state.images = []
        cols = st.columns(5)
        for i, scene in enumerate(scenes):
            full_prompt = f"{style}, {char_look}, character name {char_name}, scene: {scene}, same face, consistent character, highly detailed"
            with st.spinner(f"Scene {i+1} ban raha hai..."):
                img = generate_free_image(full_prompt, seed=42+i)
                if img:
                    st.session_state.images.append(img)
                    cols[i].image(img, caption=f"Scene {i+1}: {scene[:30]}")
                    time.sleep(1)
        st.success("4K Images Ban Gayin! Ab Video ka button dabao")

# --- SHOW IMAGES IF EXIST ---
if st.session_state.images:
    st.divider()
    cols = st.columns(len(st.session_state.images))
    for i, im in enumerate(st.session_state.images):
        cols[i].image(im, caption=f"Scene {i+1}")

# --- MAKE VIDEO ---
if video_btn:
    if not st.session_state.images:
        st.warning("Pehle tasveerein banao ya upload karo bhas!")
    else:
        with st.spinner("Video ban rahi hai... 30 second lagega..."):
            try:
                # 1. Audio banao gTTS se
                tts = gTTS(text=story_input, lang='ur', slow=False)
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
                tts.save(audio_path)
                
                # 2. Video banao imageio se (Streamlit Cloud me moviepy se behtar)
                import imageio.v2 as imageio
                video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                
                writer = imageio.get_writer(video_path, fps=1, macro_block_size=1) # 1 image = 1 sec, aap 0.5 bhi kar sakte ho
                for im in st.session_state.images:
                    # resize to 1024x1024
                    im_resized = im.resize((1024,1024))
                    # 3 second tak ek image dikhao (fps=1, so 3 frames)
                    for _ in range(3):
                        writer.append_data(imageio.core.util.Array(im_resized))
                writer.close()
                
                st.success("Video Ready hai bhas!")
                st.video(video_path)
                
                with open(video_path, 'rb') as f:
                    st.download_button("📥 ویڈیو ڈاؤن لوڈ کریں", f, file_name="meri_kahani_video.mp4", mime="video/mp4")
                
                st.audio(audio_path)
                with open(audio_path, 'rb') as f:
                    st.download_button("🔊 آڈیو ڈاؤن لوڈ کریں", f, file_name="kahani.mp3")

            except Exception as e:
                st.error(f"Video Error: {e}")
                st.info("Agar moviepy ka error aye to requirements.txt me ye 3 line add karo: \n gtts \n imageio \n imageio-ffmpeg")

st.markdown("---")
st.caption("Made with ❤️ - FREE Version - Ab koi API Key nahi chahiye!")
