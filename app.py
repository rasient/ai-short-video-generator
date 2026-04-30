import os
import json
import tempfile
from pathlib import Path

import streamlit as st
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# Fix MoviePy 1.0.3 with modern Pillow.
# Pillow removed Image.ANTIALIAS; MoviePy still expects it.
from PIL import Image, ImageDraw, ImageFont
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    CompositeAudioClip,
)

load_dotenv()

st.set_page_config(
    page_title="AI Short Video Generator",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 AI Short Video Generator")
st.write("Upload a raw video, describe the goal, and generate a polished short video.")

api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
client = OpenAI(api_key=api_key) if api_key else None

if not api_key:
    st.warning("OPENAI_API_KEY is missing. AI planning is disabled, but manual rendering still works.")

with st.sidebar:
    st.header("Video Settings")
    target_format = st.selectbox("Output format", ["9:16 vertical", "1:1 square", "16:9 horizontal"])
    target_length = st.slider("Target length in seconds", 10, 90, 30)
    mute_original = st.checkbox("Mute original audio", value=False)
    add_title_overlay = st.checkbox("Add title overlay", value=True)
    add_captions = st.checkbox("Add captions / felirat", value=True)
    use_background_music = st.checkbox("Use background music", value=False)

uploaded_video = st.file_uploader("Upload raw video", type=["mp4", "mov", "m4v", "avi"])

col1, col2 = st.columns(2)
with col1:
    title = st.text_input("Short video title", placeholder="Example: Volunteers making sandwiches for people in need")
    url = st.text_input("Optional URL", placeholder="LinkedIn / website / campaign link")
with col2:
    description = st.text_area(
        "Description / instructions for ChatGPT",
        placeholder="Example: Make this emotional, human, short, with Hungarian captions.",
        height=120,
    )

caption_text = st.text_area(
    "Caption / felirat text",
    placeholder="Paste caption lines here. Each line becomes one subtitle block.",
    height=140,
)

background_music = None
if use_background_music:
    background_music = st.file_uploader("Upload background music", type=["mp3", "wav", "m4a"])


def get_ai_edit_plan(title, url, description, target_length, target_format, caption_text):
    fallback_lines = [line.strip() for line in caption_text.splitlines() if line.strip()]
    fallback = {
        "hook": title or "Short video",
        "recommended_start": 0,
        "recommended_end": target_length,
        "caption_lines": fallback_lines,
        "music_mood": "soft inspirational",
        "editing_notes": "Manual fallback plan used.",
    }

    if not client:
        return fallback

    prompt = f"""
You are a short-form video editor.
Create a practical edit plan for a short social video.

Return ONLY valid JSON with this structure:
{{
  "hook": "short title overlay",
  "recommended_start": 0,
  "recommended_end": 30,
  "caption_lines": ["caption line 1", "caption line 2"],
  "music_mood": "background music mood",
  "editing_notes": "brief editing direction"
}}

Video title: {title}
URL: {url}
Description: {description}
Target length: {target_length} seconds
Target format: {target_format}
Available caption/transcript text:
{caption_text}
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        raw_text = response.output_text.strip()
        return json.loads(raw_text)
    except Exception as e:
        fallback["editing_notes"] = f"AI planning failed, fallback used. Error: {e}"
        return fallback


def target_size_for_format(fmt):
    if fmt == "9:16 vertical":
        return 1080, 1920
    if fmt == "1:1 square":
        return 1080, 1080
    return 1920, 1080


def resize_for_format(video, fmt):
    target_w, target_h = target_size_for_format(fmt)

    # Resize by aspect ratio, then center crop.
    video_ratio = video.w / video.h
    target_ratio = target_w / target_h

    if video_ratio > target_ratio:
        video = video.resize(height=target_h)
    else:
        video = video.resize(width=target_w)

    return video.crop(
        x_center=video.w / 2,
        y_center=video.h / 2,
        width=target_w,
        height=target_h,
    )


def load_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    dummy = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(dummy)

    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_text_overlay(text, video_w, video_h, duration, position="bottom", font_size=64):
    img = Image.new("RGBA", (video_w, video_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(font_size)

    max_width = int(video_w * 0.86)
    lines = wrap_text(text, font, max_width)
    line_heights = []
    total_h = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_h += h + 12
    total_h = max(0, total_h - 12)

    if position == "top":
        y = int(video_h * 0.08)
    else:
        y = int(video_h * 0.78) - total_h // 2

    padding_x = 28
    padding_y = 20
    bg_top = max(0, y - padding_y)
    bg_bottom = min(video_h, y + total_h + padding_y)
    draw.rounded_rectangle(
        [int(video_w * 0.05), bg_top, int(video_w * 0.95), bg_bottom],
        radius=24,
        fill=(0, 0, 0, 145),
    )

    for line, h in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (video_w - text_w) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += h + 12

    return ImageClip(np.array(img)).set_duration(duration)


def render_video(video_file, music_file, plan):
    temp_dir = tempfile.mkdtemp()
    input_path = Path(temp_dir) / "input_video.mp4"
    output_path = Path(temp_dir) / "final_short_video.mp4"

    with open(input_path, "wb") as f:
        f.write(video_file.getbuffer())

    video = VideoFileClip(str(input_path))

    start = max(0, float(plan.get("recommended_start", 0)))
    end = min(video.duration, float(plan.get("recommended_end", target_length)))
    if end <= start:
        start = 0
        end = min(video.duration, target_length)

    video = video.subclip(start, end)
    video = resize_for_format(video, target_format)

    overlays = [video]

    if add_title_overlay:
        hook = plan.get("hook", title or "Short video")
        title_clip = make_text_overlay(
            hook,
            video.w,
            video.h,
            duration=min(4, video.duration),
            position="top",
            font_size=62,
        )
        overlays.append(title_clip)

    if add_captions:
        lines = plan.get("caption_lines", [])[:8]
        if lines:
            segment_duration = video.duration / len(lines)
            for i, line in enumerate(lines):
                clip = make_text_overlay(
                    line,
                    video.w,
                    video.h,
                    duration=segment_duration,
                    position="bottom",
                    font_size=56,
                ).set_start(i * segment_duration)
                overlays.append(clip)

    final = CompositeVideoClip(overlays)

    audio_tracks = []
    if not mute_original and video.audio:
        audio_tracks.append(video.audio.volumex(0.8))

    if music_file is not None:
        music_path = Path(temp_dir) / "background_music"
        with open(music_path, "wb") as f:
            f.write(music_file.getbuffer())
        music = AudioFileClip(str(music_path))
        music = music.subclip(0, min(video.duration, music.duration)).volumex(0.18)
        audio_tracks.append(music)

    if audio_tracks:
        final = final.set_audio(CompositeAudioClip(audio_tracks))
    else:
        final = final.without_audio()

    final.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="ultrafast",
        threads=2,
    )

    video.close()
    final.close()

    return output_path


if uploaded_video:
    st.video(uploaded_video)

    if st.button("✨ Generate AI edit plan"):
        with st.spinner("Creating edit plan..."):
            st.session_state["edit_plan"] = get_ai_edit_plan(
                title, url, description, target_length, target_format, caption_text
            )

    if "edit_plan" in st.session_state:
        st.subheader("AI Edit Plan")
        st.json(st.session_state["edit_plan"])

        if st.button("🎞️ Generate Short Video"):
            with st.spinner("Rendering video..."):
                output_path = render_video(uploaded_video, background_music, st.session_state["edit_plan"])
                st.success("Short video generated.")
                st.video(str(output_path))
                with open(output_path, "rb") as f:
                    st.download_button(
                        "Download final short video",
                        data=f,
                        file_name="final_short_video.mp4",
                        mime="video/mp4",
                    )
else:
    st.info("Upload a video to begin.")
