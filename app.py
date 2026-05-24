import streamlit as st
import os
import numpy as np
from PIL import Image, ImageDraw
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
import whisper

# الدالة الأساسية لرسم النص
def create_text_clip(text, duration, start_time, video_w, video_h, fontsize=30, color='white'):
    img = Image.new('RGBA', (int(video_w), 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((20, 20), text, fill=color)
    return ImageClip(np.array(img)).set_duration(duration).set_start(start_time).set_position('center')

st.set_page_config(page_title="AI Shorts Batch Generator", layout="centered")
st.title("🎬 AI Shorts Batch Generator")

uploaded_file = st.file_uploader("Upload your long video:", type=["mp4", "mov"])

if uploaded_file is not None:
    local_video_path = "temp_input_video.mp4"
    with open(local_video_path, "wb") as f:
        f.write(uploaded_file.read())
    
    st.video(local_video_path)

    if st.button("🚀 Generate All Possible Shorts"):
        with st.spinner("Processing video into 30s clips..."):
            try:
                full_video = VideoFileClip(local_video_path)
                
                # 1. قص الفيديو ليصبح طولياً (9:16)
                w, h = full_video.size
                target_ratio = 9/16
                new_w = h * target_ratio
                x1 = (w - new_w) / 2
                full_video = full_video.crop(x1=x1, y1=0, x2=x1+new_w, y2=h)
                
                # 2. تحويل الكلام لنص مرة واحدة للسرعة
                model = whisper.load_model("base")
                result = model.transcribe(local_video_path)
                segments = result["segments"]
                
                # 3. تقسيم الفيديو لـ Shorts (كل 30 ثانية)
                for i in range(0, int(full_video.duration), 30):
                    start = i
                    end = min(i + 30, full_video.duration)
                    clip = full_video.subclip(start, end)
                    
                    # دمج المقاطع مع النصوص
                    ui_clips = [clip]
                    for seg in segments:
                        if seg["start"] >= start and seg["end"] <= end:
                            sub = create_text_clip(seg["text"], min(seg["end"], end) - seg["start"], seg["start"] - start, clip.w, clip.h)
                            ui_clips.append(sub)
                    
                    final_clip = CompositeVideoClip(ui_clips)
                    output_name = f"short_{i}.mp4"
                    final_clip.write_videofile(output_name, codec="libx264", audio_codec="aac")
                    
                    # عرض النتائج
                    st.success(f"Generated: {output_name}")
                    st.video(output_name)
                    with open(output_name, "rb") as f:
                        st.download_button(f"Download {output_name}", f, output_name)

                full_video.close()
                os.remove(local_video_path)
            except Exception as e:
                st.error(f"Error: {e}")
