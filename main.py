import streamlit as st
import requests
import urllib.parse
from PIL import Image
from io import BytesIO
import time
import tempfile
import numpy as np
import imageio
from gtts import gTTS

# --- FREE IMAGE GENERATION (No API Key) ---
def generate_free_image(prompt, seed=42):
    safe_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&model=flux&seed={seed}&nologo=true&enhance=true"
    try:
        r = requests.get(url, timeout=90)
        if r.status_code == 200:
            return Image.open(BytesIO(r.content))
    except Exception as e:
        st.error(f"Image Error: {e}")
    return None

# --- MOTION EFFECT (Ken Burns Zoom) ---
def create_motion_frames(pil_image, num_frames=45):
    frames = []
    pil_image = pil_image.resize((768, 768)).convert("RGB")
    w, h = pil_image.size
    for i in range(num_frames):
        zoom = 1.0 + (i / num_frames) * 0.3
        new_w, new_h = int(w / zoom), int(h / zoom)
        left = (w - new_w) // 2 + int((i - num_frames/2) * 0.5)
        top = (h - new_h) // 2
        cropped = pil_image.crop((max(0,left), max(0,top), min(w, left+new_w), min(h, top+new_h)))
        resized = cropped.resize((768, 768))
        frames.append(np.array(resized))
    return frames

def split_story(story):
    lines = [l.strip() for l in story.split('.') if l.strip()]
    return [l for l in lines if l][:15]

st.set_page_config(page_title="My Story - VIDEO PRO MAX", page_icon="🎬", layout="wide")
st.title("🎬 My Story - Video Pro MAX (FREE)")

with st.sidebar:
    st.header("Lock Your Character")
    char_name = st.text_input("Character Name", "Ali")
    char_look = st.text_area("Character Look (Prompt)", "10 year old Pakistani boy, full body, cute face, big eyes, pent shirt, shoes", height=120)
    style = st.selectbox("Graphic Style", ["3D Cartoon, Pixar style, ultra detailed", "Realistic Photo, 8k", "Anime style", "Disney style", "Cinematic"])
    
    st.divider()
    st.header("Upload Your Pictures for Video")
    st.caption("Unlimited Upload - Add as many as you want")
    uploaded_files = st.file_uploader("Upload Character Pictures", type=["jpg","png","jpeg","webp"], accept_multiple_files=True)
    if uploaded_files:
        st.success(f"{len(uploaded_files)} Images Uploaded!")

    st.divider()
    motion_on = st.checkbox("Enable Motion Effect (Zoom)", value=True)
    motion_speed = st.slider("Motion Speed", 1, 5, 2)

st.subheader("Write Your Story (Each sentence = 1 Scene)")
story_input = st.text_area("Story", "A boy named Ali lived in a village. He was very hardworking. He worked in his fields. Finally his hard work paid off. Everyone in the village started respecting him.", height=150, label_visibility="collapsed")

col1, col2 = st.columns([1,1])
with col1:
    gen_btn = st.button("🎨 Generate Images (FREE)", type="primary", use_container_width=True)
with col2:
    video_btn = st.button("🎬 Create Full Motion Video", use_container_width=True)

if 'images' not in st.session_state:
    st.session_state.images = []

if gen_btn:
    if uploaded_files:
        imgs = [Image.open(f).convert("RGB") for f in uploaded_files]
        st.session_state.images = imgs
        st.success(f"Using {len(imgs)} of your uploaded images for video!")
    else:
        scenes = split_story(story_input)
        st.session_state.images = []
        cols = st.columns(min(len(scenes), 5))
        for i, scene in enumerate(scenes):
            full_prompt = f"{style}, full body shot, {char_look}, character {char_name}, scene: {scene}, consistent face, same character, highly detailed, no crop"
            with st.spinner(f"Generating Scene {i+1}..."):
                img = generate_free_image(full_prompt, seed=100+i*7)
                if img:
                    st.session_state.images.append(img)
                    if i < 5:
                        cols[i % 5].image(img, caption=f"Scene {i+1}")
                time.sleep(1)
        st.success("All Images Ready!")

if st.session_state.images:
    st.divider()
    st.write(f"Total {len(st.session_state.images)} images ready")
    cols = st.columns(min(len(st.session_state.images), 6))
    for i, im in enumerate(st.session_state.images):
        cols[i % 6].image(im, caption=f"{i+1}")

if video_btn:
    if not st.session_state.images:
        st.warning("Please generate or upload images first!")
    else:
        with st.spinner("Creating Full Motion Video... Please wait 1 minute..."):
            try:
                tts = gTTS(text=story_input, lang='en', slow=False)
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
                tts.save(audio_path)

                video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                writer = imageio.get_writer(video_path, fps=15, macro_block_size=1, quality=8)
                total_frames = 45 // motion_speed if motion_on else 15

                for im in st.session_state.images:
                    if motion_on:
                        for frame in create_motion_frames(im, num_frames=total_frames):
                            writer.append_data(frame)
                    else:
                        frame = np.array(im.resize((768, 768)).convert("RGB"))
                        for _ in range(total_frames):
                            writer.append_data(frame)
                writer.close()
                
                st.balloons()
                st.success("Video is Ready!")
                st.video(video_path)
                
                with open(video_path, 'rb') as vf:
                    st.download_button("📥 Download Video (MP4)", vf, file_name="My_Story_Video.mp4", mime="video/mp4", use_container_width=True)
                st.audio(audio_path)

            except Exception as e:
                st.error(f"Error: {e}")

st.caption("FREE Version - Unlimited Upload + Motion Video - No API Key Needed!")
