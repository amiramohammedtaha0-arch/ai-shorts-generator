import streamlit as st
import os
import numpy as np
import gc # إضافة مكتبة لتنظيف الذاكرة
from PIL import Image, ImageDraw
import streamlit.components.v1 as components
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
import whisper

# إعدادات التبويبة
st.set_page_config(page_title="AI Shorts Generator", page_icon="🎬", layout="centered")

meta_tags = """
    <meta name="description" content="AI-powered tool to transform long videos into viral, professional-quality Shorts.">
    <meta property="og:title" content="AI Shorts Batch Generator">
"""
components.html(f"<head>{meta_tags}</head>", height=0)

st.markdown("""
    <style>
    video { max-width: 400px !important; margin: auto; display: block; border-radius: 10px; }
    .stVideo { display: flex; justify-content: center; }
    </style>
""", unsafe_allow_html=True)

def create_text_clip(text, duration, start_time, video_w, video_h):
    img = Image.new('RGBA', (int(video_w), 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((20, 40), text, fill='white')
    return ImageClip(np.array(img)).set_duration(duration).set_start(start_time).set_position(('center', 'center'))

st.title("🎬 AI Shorts Batch Generator")

st.markdown("""
### 🚀 About the Tool:
* **Batch Processing:** Split long videos into 30s clips.
* **Auto-Subtitles:** Burn-in captions using AI.
* **Auto-Cropping:** Perfect 9:16 portrait format.
* **Manual Control:** Precise timing for your cuts.
""")

uploaded_file = st.file_uploader("Upload video:", type=["mp4", "mov"])
mode = st.radio("Processing Mode:", ("🤖 Auto-Batch (All 30s clips)", "⏱️ Manual Single Cut"))

start_time_manual, end_time_manual = 0, 30
if mode == "⏱️ Manual Single Cut":
    col1, col2 = st.columns(2)
    start_time_manual = col1.number_input("Start (s):", value=0)
    end_time_manual = col2.number_input("End (s):", value=30)

if uploaded_file is not None:
    local_video_path = "temp_input_video.mp4"
    with open(local_video_path, "wb") as f:
        f.write(uploaded_file.read())
    
    st.info("Uploaded Video Preview:")
    st.video(local_video_path)

    if st.button("🚀 Start AI Processing"):
        with st.spinner("Processing... Using light-weight AI model to save resources ⏳"):
            try:
                full_video = VideoFileClip(local_video_path)
                w, h = full_video.size
                full_video = full_video.crop(x1=(w - h*9/16)/2, y1=0, x2=(w + h*9/16)/2, y2=h)
                
                # استخدام نموذج 'tiny' لتقليل استهلاك الـ RAM ومنع الخطأ 403
                model = whisper.load_model("tiny") 
                result = model.transcribe(local_video_path)
                segments = result["segments"]

                ranges = [(i, min(i + 30, full_video.duration)) for i in range(0, int(full_video.duration), 30)] if mode == "🤖 Auto-Batch (All 30s clips)" else [(start_time_manual, min(end_time_manual, full_video.duration))]

                for start, end in ranges:
                    clip_duration = end - start
                    if clip_duration <= 0: continue
                    
                    short_clip = full_video.subclip(start, end)
                    ui_clips = [short_clip]
                    
                    for seg in segments:
                        if seg["start"] >= start and seg["end"] <= end:
                            sub = create_text_clip(seg["text"], min(seg["end"], end) - seg["start"], seg["start"] - start, short_clip.w, short_clip.h)
                            ui_clips.append(sub)
                    
                    final_video = CompositeVideoClip(ui_clips)
                    output_name = f"short_{int(start)}.mp4"
                    final_video.write_videofile(output_name, codec="libx264", audio_codec="aac")
                    
                    st.success(f"✅ Generated: {output_name}")
                    st.video(output_name)
                    with open(output_name, "rb") as f:
                        st.download_button(f"📥 Download {output_name}", f, file_name=output_name)
                    
                    # تنظيف الذاكرة بعد كل مقطع
                    del final_video, short_clip, ui_clips
                    gc.collect()

                full_video.close()
                os.remove(local_video_path)
            except Exception as e:
                st.error(f"❌ Error: {e}")
