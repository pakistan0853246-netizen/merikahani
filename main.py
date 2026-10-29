import streamlit as st
import requests, io, base64
from PIL import Image
from gtts import gTTS
from fpdf import FPDF
import re

# --- PAGE DESIGN ---
st.set_page_config(page_title="Meri Kahani - Pro", page_icon="📚", layout="wide")
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #FFF8E7 0%, #FFECD2 100%); }
.main-title { text-align:center; font-size: 45px; font-weight: bold; color: #4A2C0A; }
.card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">📚 میری کہانی - PRO</p>', unsafe_allow_html=True)

# --- SIDEBAR - CHARACTER LOCK ---
with st.sidebar:
    st.header("👤 ہمارا کریکٹر لاک کریں")
    char_name = st.text_input("کریکٹر کا نام", "علی")
    char_look = st.text_area("کریکٹر کی شکل", "10 سال کا پاکستانی بچہ، سفید شلوار قمیض، بڑی آنکھیں، پیارا مسکراتا چہرہ")
    char_style = st.selectbox("گرافک سٹائل", ["Pixar 3D Cartoon, ultra detailed", "Disney Style, vibrant", "Anime Style, high quality", "Realistic Photo, 8k"])
    api_key = st.text_input("Stability API Key", type="password", help="stability.ai سے فری Key لے لیں")
    st.info("کریکٹر ایک ہی رہے گا، یہی تو مزہ ہے باس!")

# --- MAIN AREA ---
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    story_input = st.text_area("اپنی پوری کہانی لکھیں باس (4-5 جملے)", "علی صبح سویرے جنگل میں گیا۔ وہاں اسے ایک جادوئی شیر ملا۔ شیر اور علی دوست بن گئے۔ دونوں نے مل کر خزانہ ڈھونڈا۔", height=150)
    generate_btn = st.button("✨ جادوئی کتاب بنائیں", use_container_width=True, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

# --- FUNCTIONS ---
def split_scenes(story):
    scenes = re.split(r'[۔.!?\n]', story)
    return [s.strip() for s in scenes if len(s.strip()) > 10][:5]

def generate_image(prompt, key):
    if not key: return None
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    # Character Lock Prompt
    full_prompt = f"{char_look}, character named {char_name}, {prompt}, {char_style}, consistent character, same face, highly detailed, beautiful background"
    payload = {"text_prompts": [{"text": full_prompt}], "cfg_scale": 8, "width": 1024, "height": 1024, "steps": 30}
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            img_data = base64.b64decode(res.json()["artifacts"][0]["base64"])
            return Image.open(io.BytesIO(img_data))
        else:
            st.error(f"API Error: {res.text}")
            return None
    except Exception as e:
        st.error(str(e))
        return None

def make_pdf(images, story_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.multi_cell(0, 10, story_text.encode('latin-1', 'ignore').decode('latin-1'))
    for img in images:
        if img:
            temp_path = "/tmp/temp_img.png"
            img.save(temp_path)
            pdf.add_page()
            pdf.image(temp_path, x=10, y=10, w=180)
    return bytes(pdf.output())

# --- GENERATION LOGIC ---
if generate_btn:
    if not story_input:
        st.warning("پہلے کہانی تو لکھیں باس!")
    else:
        scenes = split_scenes(story_input)
        st.success(f"باس، آپ کی کہانی کے {len(scenes)} سین بن گئے، اب تصویریں بن رہی ہیں...")
        
        images = []
        cols = st.columns(len(scenes))
        for i, scene in enumerate(scenes):
            with cols[i]:
                st.write(f"**سین {i+1}:** {scene}")
                with st.spinner("بن رہی ہے..."):
                    img = generate_image(scene, api_key)
                    if img:
                        st.image(img, use_container_width=True)
                        images.append(img)
                    else:
                        st.warning("API Key ڈالیں تو تصویر آئے گی، ابھی Demo دکھا رہا ہوں")
                        # Demo placeholder
                        st.image("https://via.placeholder.com/400x400.png?text="+scene[:20], use_container_width=True)
        
        # --- VOICE FEATURE ---
        st.divider()
        st.subheader("🔊 کہانی سنیں")
        try:
            tts = gTTS(text=story_input, lang='ur', slow=False)
            tts.save("/tmp/story.mp3")
            st.audio("/tmp/story.mp3")
        except:
            tts = gTTS(text=story_input, lang='en')
            tts.save("/tmp/story.mp3")
            st.audio("/tmp/story.mp3")

        # --- PDF DOWNLOAD ---
        if images:
            st.divider()
            pdf_bytes = make_pdf(images, story_input)
            st.download_button("📕 پوری کتاب PDF میں ڈاؤن لوڈ کریں", data=pdf_bytes, file_name=f"{char_name}_ki_kahani.pdf", mime="application/pdf", use_container_width=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("✨ نئے فیچرز")
    st.write("✅ **کریکٹر لاک:** ہر تصویر میں آپ کا علی ایک جیسا رہے گا")
    st.write("✅ **HD گرافک:** Pixar 3D والا گرافک")
    st.write("✅ **آٹو سین:** ایک کہانی سے 5 تصویریں خود بن جائیں گی")
    st.write("✅ **آواز:** کہانی کو سنا بھی جا سکتا ہے")
    st.write("✅ **PDF بک:** پوری کتاب ڈاؤن لوڈ")
    st.markdown('</div>', unsafe_allow_html=True)
