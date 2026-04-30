"""
AI Short Video Generator MVP

Upload a raw video, add title/URL/description/caption text,
then generate a short MP4 with title overlay, captions, optional mute,
and optional background music.
"""

import os
import json
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    CompositeAudioClip,
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np

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

if not client:
    st.warning("OPENAI_API_KEY is missing. AI planning is disabled, but manual rendering can still work.")

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
        placeholder="Example: Make this emotional, human, short, with Hungarian captions. Focus on volunteers, kindness, and impact.",
        height=120,
    )

caption_text = st.text_area(
    "Caption/felirat text",
    placeholder=(
        "Paste transcript or short caption lines here. Example:\n"
        "Ma önkéntesek szendvicseket készítettek rászorulóknak.\n"
        "Egy apró gesztus.\n"
        "Nagy emberi hatás."
    ),
    height=140,
)

background_music = None
if use_background_music:
    background_music = st.file_uploader("Upload background music", type=["mp3", "wav", "m4a"])


def get_ai_edit_plan(title, url, description, target_length, target_format, caption_text):
    """Ask ChatGPT/OpenAI for a short-video edit plan."""
    fallback_lines = [line.strip() for line in caption_text.splitlines() if line.strip()]

    if not client:
        return {
            "hook": title or "Short video",
            "recommended_start": 0,
            "recommended_end": target_length,
            "caption_lines": fallback_lines,
            "music_mood": "soft inspirational",
            "editing_notes": "Manual fallback plan used because API key is missing.",
        }

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

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    raw_text = response.output_text.strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {
            "hook": title or "Short video",
            "recommended_start": 0,
            "recommended_end": target_length,
            "caption_lines": fallback_lines,
            "music_mood": "soft inspirational",
            "editing_notes": raw_text,
        }


def resize_for_format(video, target_format):
    """Resize/crop video to common social formats."""
    if target_format == "9:16 vertical":
        target_w, target_h = 1080, 1920
    elif target_format == "1:1 square":
        target_w, target_h = 1080, 1080
    else:
        target_w, target_h = 1920, 1080

    video = video.resize(height=target_h)
    if video.w < target_w:
        video = video.resize(width=target_w)

    return video.crop(
        x_center=video.w / 2,
        y_center=video.h / 2,
        width=target_w,
        height=target_h,
    )



def get_font(fontsize):
    """Load a safe default font available on most Linux/Streamlit systems."""
    for font_name in ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "Arial.ttf"]:
        try:
            return ImageFont.truetype(font_name, fontsize)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap_text(text, font, max_width):
    """Wrap text so captions fit inside the video width."""
    words = text.split()
    lines = []
    current = ""

    dummy = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(dummy)

    for word in words:
        test_line = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font, stroke_width=3)
        line_width = bbox[2] - bbox[0]
        if line_width <= max_width:
            current = test_line
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines or [text]


def make_text_clip(text, duration, placement, video_size, fontsize=64):
    """Create readable text overlay using Pillow, avoiding ImageMagick/TextClip issues."""
    width, height = video_size
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = get_font(fontsize)

    max_text_width = int(width * 0.86)
    lines = wrap_text(text, font, max_text_width)[:3]
    line_spacing = int(fontsize * 0.25)

    line_boxes = [draw.textbbox((0, 0), line, font=font, stroke_width=3) for line in lines]
    line_heights = [box[3] - box[1] for box in line_boxes]
    total_text_height = sum(line_heights) + line_spacing * (len(lines) - 1)

    if placement == "top":
        y = int(height * 0.06)
    elif placement == "bottom":
        y = height - total_text_height - int(height * 0.10)
    else:
        y = (height - total_text_height) // 2

    for line, box, line_height in zip(lines, line_boxes, line_heights):
        line_width = box[2] - box[0]
        x = (width - line_width) // 2
        draw.text((x, y), line, font=font, fill="white", stroke_width=4, stroke_fill="black")
        y += line_height + line_spacing

    return ImageClip(np.array(image)).set_duration(duration)


def save_uploaded_file(uploaded_file, path):
    uploaded_file.seek(0)
    with open(path, "wb") as f:
        f.write(uploaded_file.read())


def generate_video(video_file, music_file, plan, target_format, mute_original, add_title_overlay, add_captions):
    """Generate final video using MoviePy."""
    temp_dir = tempfile.mkdtemp()
    input_path = Path(temp_dir) / "input_video.mp4"
    output_path = Path(temp_dir) / "final_short_video.mp4"

    save_uploaded_file(video_file, input_path)

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
        title_clip = make_text_clip(hook, min(4, video.duration), "top", video.size, fontsize=70)
        overlays.append(title_clip)

    if add_captions:
        caption_lines = plan.get("caption_lines", [])[:6]
        if caption_lines:
            segment_duration = video.duration / len(caption_lines)
            for i, line in enumerate(caption_lines):
                caption_clip = make_text_clip(
                    line,
                    segment_duration,
                    "bottom",
                    video.size,
                    fontsize=58,
                ).set_start(i * segment_duration)
                overlays.append(caption_clip)

    final = CompositeVideoClip(overlays)

    audio_tracks = []
    if not mute_original and video.audio:
        audio_tracks.append(video.audio.volumex(0.8))

    if music_file is not None:
        music_path = Path(temp_dir) / "background_music.mp3"
        save_uploaded_file(music_file, music_path)
        music_clip = AudioFileClip(str(music_path))
        music = music_clip.subclip(0, min(video.duration, music_clip.duration)).volumex(0.18)
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
        preset="medium",
    )

    return output_path


if uploaded_video:
    st.video(uploaded_video)

    if st.button("✨ Generate AI edit plan"):
        with st.spinner("Creating edit plan..."):
            plan = get_ai_edit_plan(title, url, description, target_length, target_format, caption_text)
            st.session_state["edit_plan"] = plan

    if "edit_plan" in st.session_state:
        st.subheader("AI Edit Plan")
        st.json(st.session_state["edit_plan"])

        if st.button("🎞️ Generate Short Video"):
            with st.spinner("Rendering video..."):
                output_path = generate_video(
                    uploaded_video,
                    background_music,
                    st.session_state["edit_plan"],
                    target_format,
                    mute_original,
                    add_title_overlay,
                    add_captions,
                )

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
