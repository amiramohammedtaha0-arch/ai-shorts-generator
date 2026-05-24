import streamlit as st
import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import whisper
import numpy as np
from PIL import Image, ImageDraw

# 1. إعدادات الصفحة الاحترافية
st.set_page_config(page_title="AI Shorts Generator", page_icon="🎬", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0f1116; color: #ffffff; }
    h1 { color: #ff4b4b; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("🎬 AI Shorts Generator")
st.write("Upload your video and let AI create your Short with automated captions!")

# 2. منطقة رفع الملف
uploaded_file = st.file_uploader("Upload your video file (MP4/MOV):", type=["mp4", "mov"])
short_title = st.text_input("Hook Title (Appears at top):", "Wait for the end! 🔥")

if uploaded_file is not None:
    # حفظ الملف مؤقتاً للمعالجة
    local_video_path = "temp_input_video.mp4"
    with open(local_video_path, "wb") as f:
        f.write(uploaded_file.read())
    
    st.video(local_video_path)

    # زر التشغيل
    if st.button("🚀 Generate AI Short"):
        output_path = "final_ai_short.mp4"
        
        with st.spinner("AI is processing... This may take a moment ⏳"):
            try:
                # تحميل الفيديو
                video = VideoFileClip(local_video_path)
                duration = min(30, video.duration) # قص لـ 30 ثانية
                short_clip = video.subclip(0, duration)
                
                # استخدام Whisper لتحويل الصوت لنص (Transcription)
                model = whisper.load_model("base")
                result = model.transcribe(local_video_path)
                segments = result["segments"]
                
                # إعداد طبقات الفيديو
                ui_clips = [short_clip]

                
                #ده اللي عدلتته

                def create_text_clip(text, duration, start_time, video_w, video_h, fontsize=30, color='white'):
                    img = Image.new('RGBA', (int(video_w), 100), (0, 0, 0, 0))
                    d = ImageDraw.Draw(img)
                    d.text((video_w*0.1, 40), text, fill=color)
                    return ImageClip(np.array(img)).set_duration(duration).set_start(start_time).set_position('center')

# 1. إضافة العنوان الجذاب (بدل الجزء الممسوح)
               ui_clips.append(create_text_clip(short_title, duration, 0, video.w, video.h, fontsize=40, color='yellow'))
               for seg in segments:
                   if seg["start"] < duration:
                       sub_clip = create_text_clip(seg["text"], min(seg["end"], duration) - seg["start"], seg["start"], video.w, video.h)
                       ui_clips.append(sub_clip)
                
                
                
                # دمج كل شيء في فيديو واحد
                final_video = CompositeVideoClip(ui_clips)
                final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
                
                st.success("🎉 Your AI Short is ready!")
                st.video(output_path)
                
                # زر التحميل
                with open(output_path, "rb") as file:
                    st.download_button("📥 Download Video", file, "ai_short.mp4", "video/mp4")
                
                # تنظيف المساحة
                video.close()
                os.remove(local_video_path)
                
            except Exception as e:
                st.error(f"Error: {e}")
