import streamlit as st
import os
import numpy as np
from PIL import Image, ImageDraw
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
import whisper
import streamlit.components.v1 as components

# إضافة الميتا تاجز للموقع
st.set_page_config(page_title="AI Shorts Batch Generator", page_icon="🎬", layout="centered")

meta_tags = """
    <meta name="description" content="AI-powered tool to transform long videos into viral, professional-quality Shorts with automatic captions and smart cropping.">
    <meta property="og:title" content="AI Shorts Batch Generator">
    <meta property="og:description" content="Convert your long videos into engaging TikTok/Reels content instantly!">
"""
components.html(f"<head>{meta_tags}</head>", height=0)

# 1. إعدادات التبويبة (الاسم والأيقونة كما في الصورة)
st.set_page_config(page_title="AI Shorts Generator", page_icon="🎬", layout="centered")

# 2. كود CSS لتصغير حجم عرض الفيديوهات في الموقع
st.markdown("""
    <style>
    video {
        max-width: 400px !important;
        margin: auto;
        display: block;
        border-radius: 10px;
    }
    .stVideo {
        display: flex;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

# 3. دالة رسم النصوص (خارج أي دالة أخرى لضمان الاستقرار)
def create_text_clip(text, duration, start_time, video_w, video_h, fontsize=30, color='white'):
    # إنشاء صورة شفافة للنص
    img = Image.new('RGBA', (int(video_w), 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # رسم النص في المنتصف (بناءً على عرض الفيديو)
    d.text((20, 40), text, fill=color)
    return ImageClip(np.array(img)).set_duration(duration).set_start(start_time).set_position(('center', 'center'))

# 4. واجهة المستخدم
st.title("🎬 AI Shorts Batch Generator")

# الوصف بالإنجليزية
st.markdown("""
### 🚀 About the Tool:
This professional AI tool helps you scale your content creation:
* **Batch Processing:** Automatically split long videos into 30-second viral Shorts.
* **Smart Transcription:** Generate and burn-in accurate subtitles automatically.
* **Auto-Cropping:** Intelligent 9:16 portrait conversion for TikTok, Reels, and YouTube Shorts.
* **Manual Control:** Flexible timing settings for precise cuts.
""")

uploaded_file = st.file_uploader("Upload your video:", type=["mp4", "mov"])
mode = st.radio("Processing Mode:", (" 🤖 Auto-Batch (All 30s clips)", "⏱️ Manual Single Cut"))

# إعدادات الوقت في حالة القص اليدوي
start_time_manual, end_time_manual = 0, 30
if mode == "⏱️ Manual Single Cut":
    col1, col2 = st.columns(2)
    start_time_manual = col1.number_input("Start (seconds):", value=0)
    end_time_manual = col2.number_input("End (seconds):", value=30)

if uploaded_file is not None:
    local_video_path = "temp_input_video.mp4"
    with open(local_video_path, "wb") as f:
        f.write(uploaded_file.read())
    
    # عرض الفيديو المرفوع (سيظهر صغيراً بسبب CSS)
    st.info("Uploaded Video Preview:")
    st.video(local_video_path)

    if st.button("🚀 Start AI Processing"):
        with st.spinner("AI is working... This may take a while depending on video length ⏳"):
            try:
                # تحميل الفيديو الأصلي
                full_video = VideoFileClip(local_video_path)
                
                # تطبيق القص الطولي (Auto-Crop 9:16) ليكون احترافياً
                w, h = full_video.size
                target_ratio = 9/16
                new_w = h * target_ratio
                x1 = (w - new_w) / 2
                full_video = full_video.crop(x1=x1, y1=0, x2=x1+new_w, y2=h)
                
                # تشغيل Whisper لاستخراج النصوص مرة واحدة فقط
                model = whisper.load_model("base")
                result = model.transcribe(local_video_path)
                segments = result["segments"]

                # تحديد المقاطع المطلوب إنتاجها
                ranges = []
                if mode == "🤖 Auto-Batch (All 30s clips)":
                    ranges = [(i, min(i + 30, full_video.duration)) for i in range(0, int(full_video.duration), 30)]
                else:
                    ranges = [(start_time_manual, min(end_time_manual, full_video.duration))]

                # معالجة كل مقطع
                for start, end in ranges:
                    clip_duration = end - start
                    if clip_duration <= 0: continue
                    
                    short_clip = full_video.subclip(start, end)
                    ui_clips = [short_clip]
                    
                    # إضافة النصوص (Subtitles) لهذا المقطع تحديداً
                    for seg in segments:
                        if seg["start"] >= start and seg["end"] <= end:
                            # حساب توقيت النص بالنسبة لبداية المقطع الصغير
                            rel_start = seg["start"] - start
                            rel_duration = min(seg["end"], end) - seg["start"]
                            
                            sub = create_text_clip(seg["text"], rel_duration, rel_start, short_clip.w, short_clip.h)
                            ui_clips.append(sub)
                    
                    # دمج المقطع وحفظه
                    final_video = CompositeVideoClip(ui_clips)
                    output_name = f"short_{int(start)}.mp4"
                    final_video.write_videofile(output_name, codec="libx264", audio_codec="aac", temp_audiofile='temp-audio.m4a', remove_temp=True)
                    
                    # عرض النتيجة (ستظهر صغيرة أيضاً)
                    st.success(f"✅ Generated Short starting at {start}s")
                    st.video(output_name)
                    with open(output_name, "rb") as f:
                        st.download_button(f"📥 Download {output_name}", f, file_name=output_name)

                full_video.close()
                os.remove(local_video_path)
                
            except Exception as e:
                st.error(f"❌ Error occurred: {e}")
