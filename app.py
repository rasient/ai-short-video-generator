```python
# === AI SHORT VIDEO GENERATOR v14 ===
# Smart scene cutting + premium credit screen

import os
import json
import tempfile
import subprocess
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import imageio_ffmpeg

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    ImageClip,
    ColorClip,
    concatenate_videoclips,
)

# ---------------- CONFIG ----------------
load_dotenv()

st.set_page_config(page_title="AI Short Video Generator", page_icon="🎬", layout="wide")

st.title("🎬 AI Short Video Generator")

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

# ---------------- UI ----------------
with st.sidebar:
    target_format = st.selectbox(
        "Output format",
        ["Same as original - no resize", "9:16 vertical", "1:1 square", "16:9 horizontal"]
    )

    target_length = st.slider("Target length", 10, 90, 30)

    use_smart = st.checkbox("Smart scene cutting", True)
    max_scenes = st.slider("Scenes", 1, 8, 4)
    sensitivity = st.slider("Sensitivity", 10.0, 80.0, 32.0)

    logo_size = st.slider("Logo size", 120, 700, 380)
    caption_size = st.slider("Caption size", 36, 120, 78)
    credit_size = st.slider("Credit size", 40, 140, 92)

uploaded_video = st.file_uploader("Upload video", type=["mp4"])

organization = st.text_input("Organization", "Budapest Bike Maffia")
name = st.text_input("Your name", "Alexander Berg")
role = st.text_input("Role", "Edited by")

# ---------------- SMART CUT ----------------
def detect(video):
    duration = video.duration
    cuts = [0]
    prev = None

    for t in np.arange(0, duration, 1):
        try:
            f = video.get_frame(t)
            g = np.mean(f)
            if prev is not None and abs(g - prev) > sensitivity:
                cuts.append(t)
            prev = g
        except:
            pass

    cuts.append(duration)

    segs = []
    for i in range(len(cuts)-1):
        segs.append((cuts[i], cuts[i+1]))

    return segs

def build(video):
    segs = detect(video)
    clips = []

    total = 0
    for s,e in segs:
        if total >= target_length:
            break
        clips.append(video.subclip(s,e))
        total += (e-s)

    return concatenate_videoclips(clips)

# ---------------- CREDIT ----------------
def credit_clip(size):
    w,h = size
    img = Image.new("RGB",(w,h),(12,14,18))
    draw = ImageDraw.Draw(img)

    txt = f"{organization}\n\n{role}\n{name}"

    draw.text((w//2,h//2), txt, anchor="mm", fill="white")

    return ImageClip(np.array(img)).set_duration(3).fadein(0.5).fadeout(0.5)

# ---------------- RENDER ----------------
if uploaded_video:

    if st.button("Generate"):
        temp = Path(tempfile.mkdtemp())
        input_path = temp/"in.mp4"
        out_path = temp/"out.mp4"

        with open(input_path,"wb") as f:
            f.write(uploaded_video.getbuffer())

        video = VideoFileClip(str(input_path))

        if use_smart:
            short = build(video)
        else:
            short = video.subclip(0,target_length)

        credit = credit_clip((int(short.w),int(short.h)))
        final = concatenate_videoclips([short,credit])

        final.write_videofile(str(out_path),codec="libx264")

        st.video(str(out_path))
```
