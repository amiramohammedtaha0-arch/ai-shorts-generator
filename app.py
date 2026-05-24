import streamlit as st
import os
import numpy as np
from PIL import Image, ImageDraw
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
import whisper

def create_text_clip(text, duration, start_time, video_w, video_h, fontsize=30, color='white'):
    img = Image.new('RGBA', (int(video_w), 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((20, 20), text, fill=color)
    return ImageClip(np.array(img)).set_duration(duration).set_start(start_time).set_position('center')

st.set_page_config(page_title="AI Shorts Generator", layout="centered")
st.title("🎬 AI Shorts Generator")

uploaded_file = st.file_uploader("Upload video:", type=["mp4", "mov"])
short_title = st.text_input("Hook Title:", "Wait for the end! 🔥")

# إضافة خيار التوقيت
mode = st.radio("Processing Mode:", ("🤖 Auto-Split (30s)", "⏱️ Manual Timing"))
start_time, end_time = 0, 30

if mode == "⏱️ Manual Timing":
    col1, col2 = st.columns(2)
    start_time = col1.number_input("Start Time (s):", value=0)
    end_time = col2.number_input("End Time (s):", value=30)

if uploaded_file is not None:
    local_video_path = "temp_input_video.mp4"
    with open(local_video_path, "wb") as f:
        f.write(uploaded_file.read())
    
    if st.button("🚀 Generate AI Short"):
        with st.spinner("Processing..."):
            try:
                video = VideoFileClip(local_video_path)
                
                # استخدام التوقيت المختار
                if mode == "🤖 Auto-Split (30s)":
                    end_time = min(30, video.duration)
                
                short_clip = video.subclip(start_time, end_time)
                
                model = whisper.load_model("base")
                result = model.transcribe(local_video_path)
                segments = result["segments"]
                
                ui_clips = [short_clip]
                ui_clips.append(create_text_clip(short_title, end_time - start_time, 0, video.w, video.h, 40, 'yellow'))
                
                for seg in segments:
                    if seg["start"] >= start_time and seg["end"] <= end_time:
                        seg_start_relative = seg["start"] - start_time
                        seg_end_relative = seg["end"] - start_time
                        sub_clip = create_text_clip(seg["text"], seg_end_relative - seg_start_relative, seg_start_relative, video.w, video.h)
                        ui_clips.append(sub_clip)
                
                final_video = CompositeVideoClip(ui_clips)
                final_video.write_videofile("final.mp4", codec="libx264", audio_codec="aac")
                st.video("final.mp4")
                video.close()
            except Exception as e:
                st.error(f"Error: {e}")
