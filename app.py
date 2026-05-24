import streamlit as st
import os
import numpy as np
from PIL import Image, ImageDraw
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
import whisper

# 1. الدالة معرفة في بداية الملف (خارج أي دالة أخرى)
def create_text_clip(text, duration, start_time, video_w, video_h, fontsize=30, color='white'):
    img = Image.new('RGBA', (int(video_w), 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # استخدام الخط الافتراضي
    d.text((20, 20), text, fill=color)
    return ImageClip(np.array(img)).set_duration(duration).set_start(start_time).set_position('center')

# 2. إعدادات الصفحة
st.set_page_config(page_title="AI Shorts Generator", page_icon="🎬", layout="centered")

st.title("🎬 AI Shorts Generator")

uploaded_file = st.file_uploader("Upload video:", type=["mp4", "mov"])
short_title = st.text_input("Hook Title:", "Wait for the end! 🔥")

if uploaded_file is not None:
    local_video_path = "temp_input_video.mp4"
    with open(local_video_path, "wb") as f:
        f.write(uploaded_file.read())
    
    st.video(local_video_path)

    if st.button("🚀 Generate AI Short"):
        output_path = "final_ai_short.mp4"
        with st.spinner("AI is processing..."):
            try:
                video = VideoFileClip(local_video_path)
                duration = min(30, video.duration)
                short_clip = video.subclip(0, duration)
                
                model = whisper.load_model("base")
                result = model.transcribe(local_video_path)
                segments = result["segments"]
                
                ui_clips = [short_clip]
                
                # إضافة العنوان
                ui_clips.append(create_text_clip(short_title, duration, 0, video.w, video.h, 40, 'yellow'))
                
                # إضافة الكلام
                for seg in segments:
                    if seg["start"] < duration:
                        sub_clip = create_text_clip(seg["text"], min(seg["end"], duration) - seg["start"], seg["start"], video.w, video.h)
                        ui_clips.append(sub_clip)
                
                final_video = CompositeVideoClip(ui_clips)
                final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
                st.video(output_path)
                
                # تنظيف
                video.close()
                os.remove(local_video_path)
            except Exception as e:
                st.error(f"Error: {e}")
