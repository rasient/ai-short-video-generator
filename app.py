"""
AI Short Video Generator MVP

Upload a raw video, add title/URL/description, generate an AI edit plan,
then render a short social video with title overlay, captions/felirat,
optional mute, and optional background music.
"""

import json
import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
)
from openai import OpenAI

load_dotenv()

st.set_page_config(page_title="AI Short Video Generator", page_icon="🎬", layout="wide")

st.title("🎬 AI Short Video Generator")
st.write("Upload a raw video and turn it into a short social video.")

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

if not client:
    st.warning("OPENAI_API_KEY is missing. AI planning will use fallback settings.")

with st.sidebar:
    st.header("Output Settings")
    target_format = st.selectbox("Output format", ["9:16 vertical", "1:1 square", "16:9 horizontal"])
    target_length = st.slider("Target length", 10, 90, 30)
    mute_original = st.checkbox("Mute original video audio", value=False)
    add_title_overlay = st.checkbox("Add title overlay", value=True)
    add_captions = st.checkbox("Add captions / felirat", value=True)
    use_background_music = st.checkbox("Use background music", value=False)

uploaded_video = st.file_uploader("Upload raw video", type=["mp4", "mov", "m4v", "avi"])

col1, col2 = st.columns(2)
with col1:
    title = st.text_input("Title", placeholder="Example: Volunteers making sandwiches")
    url = st.text_input("Optional URL", placeholder="Campaign / LinkedIn / website link")
with col2:
    description = st.text_area(
        "Description / editing instruction",
        placeholder="Example: Make it emotional, human, short, with Hungarian captions.",
        height=120,
    )

caption_text = st.text_area(
    "Caption / felirat text",
    placeholder="Paste short transcript or caption lines here...",
    height=140,
)

background_music = None
if use_background_music:
    background_music = st.file_uploader("Upload background music", type=["mp3", "wav", "m4a"])


def parse_caption_lines(text: str):
    return [line.strip() for line in text.splitlines() if line.strip()]


def get_ai_edit_plan():
    fallback = {
        "hook": title or "Short video",
        "recommended_start": 0,
        "recommended_end": target_length,
        "caption_lines": parse_caption_lines(caption_text),
        "music_mood": "soft inspirational",
        "editing_notes": "Fallback plan used because OpenAI API key is missing or JSON parsing failed.",
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

Title: {title}
URL: {url}
Description: {description}
Target length: {target_length} seconds
Target format: {target_format}
Caption/transcript text:
{caption_text}
"""

    try:
        response = client.responses.create(model="gpt-4.1-mini", input=prompt)
        return json.loads(response.output_text.strip())
    except Exception as exc:
        fallback["editing_notes"] = f"Fallback plan used. AI planning error: {exc}"
        return fallback


def resize_for_format(video, fmt):
    if fmt == "9:16 vertical":
        target_w, target_h = 1080, 1920
    elif fmt == "1:1 square":
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


def make_text_clip(text, duration, position, fontsize=62):
    return (
        TextClip(
            text,
            fontsize=fontsize,
            color="white",
            font="Arial-Bold",
            stroke_color="black",
            stroke_width=3,
            method="caption",
            size=(950, None),
        )
        .set_duration(duration)
        .set_position(position)
    )


def render_video(video_file, music_file, plan):
    temp_dir = Path(tempfile.mkdtemp())
    input_path = temp_dir / "input_video.mp4"
    output_path = temp_dir / "final_short_video.mp4"

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
        overlays.append(make_text_clip(plan.get("hook", title or "Short video"), min(4, video.duration), ("center", "top"), 70))

    if add_captions:
        lines = plan.get("caption_lines", [])[:8]
        if lines:
            segment_duration = video.duration / len(lines)
            for i, line in enumerate(lines):
                overlays.append(
                    make_text_clip(line, segment_duration, ("center", "bottom"), 56).set_start(i * segment_duration)
                )

    final = CompositeVideoClip(overlays)

    audio_tracks = []
    if not mute_original and video.audio:
        audio_tracks.append(video.audio.volumex(0.8))

    if music_file is not None:
        music_path = temp_dir / "background_music.mp3"
        with open(music_path, "wb") as f:
            f.write(music_file.getbuffer())
        music_clip = AudioFileClip(str(music_path))
        music_clip = music_clip.subclip(0, min(video.duration, music_clip.duration)).volumex(0.18)
        audio_tracks.append(music_clip)

    if audio_tracks:
        final = final.set_audio(CompositeAudioClip(audio_tracks))
    else:
        final = final.without_audio()

    final.write_videofile(str(output_path), codec="libx264", audio_codec="aac", fps=30, preset="medium")
    return output_path


if uploaded_video:
    st.subheader("Preview")
    st.video(uploaded_video)

    if st.button("✨ Generate AI edit plan"):
        st.session_state["edit_plan"] = get_ai_edit_plan()

    if "edit_plan" in st.session_state:
        st.subheader("Edit Plan")
        st.json(st.session_state["edit_plan"])

        if st.button("🎞️ Generate short video"):
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
