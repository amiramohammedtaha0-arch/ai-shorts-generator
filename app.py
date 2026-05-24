import streamlit as st
import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import whisper

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
                
                # إضافة العنوان الجذاب
                title_clip = (TextClip(short_title, fontsize=30, color='yellow', font='Arial-Bold', bg_color='black')
                              .set_position(('center', 40))
                              .set_duration(duration))
                ui_clips.append(title_clip)
                
                # إضافة الكلام (Subtitles)
                for seg in segments:
                    if seg["start"] < duration:
                        sub_clip = (TextClip(seg["text"], fontsize=24, color='white', font='Arial',
                                            method='caption', size=(video.w * 0.8, None))
                                    .set_position(('center', 'center'))
                                    .set_start(seg["start"])
                                    .set_end(min(seg["end"], duration)))
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