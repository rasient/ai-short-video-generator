
import os
import json
import tempfile
import subprocess
from pathlib import Path
import imageio_ffmpeg

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Pillow compatibility for text overlays
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    ImageClip,
    ColorClip,
)

load_dotenv()

st.set_page_config(
    page_title="AI Short Video Generator",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 AI Short Video Generator")
st.write("Upload a raw video, describe the goal, and generate a polished short video.")

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

if not api_key:
    st.warning("OPENAI_API_KEY is missing. AI planning will use fallback mode.")

with st.sidebar:
    st.header("Video Settings")
    target_format = st.selectbox("Output format", ["9:16 vertical", "1:1 square", "16:9 horizontal"])
    target_length = st.slider("Target length in seconds", 10, 90, 30)
    mute_original = st.checkbox("Mute original audio", value=False)
    add_title_overlay = st.checkbox("Add title overlay", value=True)
    add_captions = st.checkbox("Add captions / felirat", value=True)
    resize_mode = st.selectbox(
        "Resize mode",
        [
            "Crop to fill - best for Shorts/Reels",
            "Fit with padding - never stretch",
        ],
        index=1,
    )
    use_background_music = st.checkbox("Use background music", value=False)
    add_credit_screen = st.checkbox("Add credit screen", value=True)
    use_crossfade = st.checkbox("Use gentle fade in/out", value=True)

uploaded_video = st.file_uploader("Upload raw video", type=["mp4", "mov", "m4v", "avi"])
uploaded_logo = st.file_uploader("Optional logo overlay", type=["png", "jpg", "jpeg"])

col1, col2 = st.columns(2)

with col1:
    title = st.text_input("Short video title", placeholder="Example: Volunteers making sandwiches for people in need")
    url = st.text_input("Optional URL", placeholder="LinkedIn / website / campaign link")
    credit_text = st.text_input("Credit screen text", value="Budapest Bike Maffia ©")

with col2:
    description = st.text_area(
        "Description / instructions for ChatGPT",
        placeholder="Example: Make this emotional, human, short, with Hungarian captions. Focus on volunteers, kindness, and impact.",
        height=120,
    )

caption_text = st.text_area(
    "Caption / felirat text",
    placeholder="Paste transcript or short caption lines here.",
    height=140,
)

background_music = None
if use_background_music:
    background_music = st.file_uploader("Upload background music", type=["mp3", "wav", "m4a"])


def fallback_plan():
    lines = [line.strip() for line in caption_text.splitlines() if line.strip()]
    return {
        "hook": title or "Short video",
        "recommended_start": 0,
        "recommended_end": target_length,
        "caption_lines": lines if lines else [
            "Önkéntesek készítenek szendvicseket.",
            "Egy kis segítség.",
            "Valódi emberi hatás.",
        ],
        "logo_overlay_seconds": 2,
        "credit_screen_text": credit_text or "Budapest Bike Maffia ©",
        "music_mood": "gentle emotional background music",
        "editing_notes": "Fallback used. Actionable fields still control render where supported.",
    }


def get_ai_edit_plan():
    if not client:
        return fallback_plan()

    prompt = f"""
You are a short-form video editor.

Return ONLY valid JSON. Do not use markdown.

The renderer can execute ONLY these fields:
- hook
- recommended_start
- recommended_end
- caption_lines
- logo_overlay_seconds
- credit_screen_text
- music_mood
- editing_notes

Important:
Do not place critical actions only inside editing_notes.
Put actionable instructions into the fields above.

Return this exact JSON structure:
{{
  "hook": "short title overlay",
  "recommended_start": 0,
  "recommended_end": 30,
  "caption_lines": ["caption line 1", "caption line 2"],
  "logo_overlay_seconds": 2,
  "credit_screen_text": "Budapest Bike Maffia ©",
  "music_mood": "gentle emotional",
  "editing_notes": "Short optional notes only"
}}

Video title: {title}
URL: {url}
Description: {description}
Target length: {target_length}
Target format: {target_format}
Caption/transcript text:
{caption_text}
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "short_video_edit_plan",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "hook": {"type": "string"},
                            "recommended_start": {"type": "number"},
                            "recommended_end": {"type": "number"},
                            "caption_lines": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "logo_overlay_seconds": {"type": "number"},
                            "credit_screen_text": {"type": "string"},
                            "music_mood": {"type": "string"},
                            "editing_notes": {"type": "string"}
                        },
                        "required": [
                            "hook",
                            "recommended_start",
                            "recommended_end",
                            "caption_lines",
                            "logo_overlay_seconds",
                            "credit_screen_text",
                            "music_mood",
                            "editing_notes"
                        ]
                    }
                }
            }
        )
        return json.loads(response.output_text)
    except Exception as e:
        plan = fallback_plan()
        plan["editing_notes"] = f"AI planning failed, fallback used. Error: {e}"
        return plan


def get_target_size(target_format):
    if target_format == "9:16 vertical":
        return 1080, 1920
    if target_format == "1:1 square":
        return 1080, 1080
    return 1920, 1080


def ffmpeg_resize_video(input_path, output_path, target_format, resize_mode):
    """
    Resize with FFmpeg instead of MoviePy, avoiding Pillow/Image.ANTIALIAS crashes.
    """
    target_w, target_h = get_target_size(target_format)

    if resize_mode.startswith("Crop to fill"):
        vf = (
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h}"
        )
    else:
        vf = (
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black"
        )

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(output_path),
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        error_text = e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
        raise RuntimeError(f"FFmpeg resize failed: {error_text[:1200]}")



def load_font(size, bold=False):
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "arial.ttf",
    ]
    for font_path in font_candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def make_text_overlay(text, duration, size, position="bottom", font_size=58):
    width, height = size
    overlay_h = 260 if position == "bottom" else 220

    img = Image.new("RGBA", (width, overlay_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = load_font(font_size, bold=True)

    max_text_width = int(width * 0.82)
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_text_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_height = font_size + 12
    total_text_h = len(lines) * line_height
    y = (overlay_h - total_text_h) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2

        # shadow / stroke effect
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 3)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 210))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_height

    clip = ImageClip(np.array(img)).set_duration(duration)
    if position == "top":
        return clip.set_position(("center", 40))
    return clip.set_position(("center", height - overlay_h - 80))


def make_credit_screen(text, duration, size):
    width, height = size
    bg = ColorClip(size=(width, height), color=(12, 12, 12)).set_duration(duration)
    txt = make_text_overlay(text, duration, size, position="bottom", font_size=64)
    txt = txt.set_position(("center", "center"))
    return CompositeVideoClip([bg, txt], size=size).set_duration(duration)


def save_uploaded_file(uploaded_file, path):
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())


def render_video(uploaded_video_file, music_file, logo_file, plan):
    temp_dir = tempfile.mkdtemp()
    temp_dir = Path(temp_dir)

    input_path = temp_dir / "input_video.mp4"
    output_path = temp_dir / "final_short_video.mp4"
    save_uploaded_file(uploaded_video_file, input_path)

    original_video = VideoFileClip(str(input_path))

    start = max(0, float(plan.get("recommended_start", 0)))
    end = min(original_video.duration, float(plan.get("recommended_end", target_length)))

    if end <= start:
        start = 0
        end = min(original_video.duration, target_length)

    trimmed_path = temp_dir / "trimmed_video.mp4"
    resized_path = temp_dir / "resized_video.mp4"

    # First trim with MoviePy, then resize with FFmpeg to avoid MoviePy/Pillow resize bug.
    trimmed = original_video.subclip(start, end)
    trimmed.write_videofile(
        str(trimmed_path),
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="ultrafast",
        threads=2,
        verbose=False,
        logger=None,
    )

    ffmpeg_resize_video(trimmed_path, resized_path, target_format, resize_mode)
    video = VideoFileClip(str(resized_path))

    target_size = get_target_size(target_format)
    clips = [video]

    if use_crossfade:
        video = video.fadein(0.25).fadeout(0.35)
        clips = [video]

    if uploaded_logo is not None:
        logo_path = temp_dir / "logo.png"
        save_uploaded_file(uploaded_logo, logo_path)
        logo_duration = min(float(plan.get("logo_overlay_seconds", 2)), video.duration)
        logo = (
            ImageClip(str(logo_path))
            .resize(width=220)
            .set_duration(logo_duration)
            .set_position(("center", 80))
            .fadein(0.15)
            .fadeout(0.2)
        )
        clips.append(logo)

    if add_title_overlay:
        hook = plan.get("hook") or title or "Short video"
        clips.append(
            make_text_overlay(
                hook,
                min(4, video.duration),
                target_size,
                position="top",
                font_size=62,
            )
        )

    if add_captions:
        caption_lines = plan.get("caption_lines", [])
        caption_lines = [line for line in caption_lines if line.strip()]
        caption_lines = caption_lines[:8]

        if caption_lines:
            segment_duration = max(1.2, video.duration / len(caption_lines))
            for i, line in enumerate(caption_lines):
                start_time = i * segment_duration
                if start_time >= video.duration:
                    break
                duration = min(segment_duration, video.duration - start_time)
                clips.append(
                    make_text_overlay(
                        line,
                        duration,
                        target_size,
                        position="bottom",
                        font_size=56,
                    ).set_start(start_time)
                )

    final = CompositeVideoClip(clips, size=target_size).set_duration(video.duration)

    if add_credit_screen:
        credit = make_credit_screen(
            plan.get("credit_screen_text") or credit_text or "Budapest Bike Maffia ©",
            2.5,
            target_size,
        )
        final = CompositeVideoClip([final], size=target_size)
        final = final.fx(lambda c: c)  # keep compatibility
        final = concatenate_safe([final, credit], target_size)

    audio_tracks = []
    if not mute_original and video.audio:
        audio_tracks.append(video.audio.volumex(0.75))

    if music_file is not None:
        music_path = temp_dir / "background_music.mp3"
        save_uploaded_file(music_file, music_path)
        music_clip = AudioFileClip(str(music_path))
        music_clip = music_clip.subclip(0, min(final.duration, music_clip.duration)).volumex(0.18)
        audio_tracks.append(music_clip)

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

    return output_path


def concatenate_safe(clips, target_size):
    from moviepy.editor import concatenate_videoclips

    fixed = []
    target_w, target_h = target_size

    for c in clips:
        if tuple(c.size) != tuple(target_size):
            # Never stretch here. Put mismatched clips on a black canvas.
            bg = ColorClip(size=(target_w, target_h), color=(0, 0, 0)).set_duration(c.duration)
            c = CompositeVideoClip(
                [bg, c.set_position(("center", "center"))],
                size=(target_w, target_h),
            ).set_duration(c.duration)
        fixed.append(c)

    return concatenate_videoclips(fixed, method="compose")


if uploaded_video:
    st.video(uploaded_video)

    if st.button("✨ Generate AI edit plan"):
        with st.spinner("Creating edit plan..."):
            st.session_state["edit_plan"] = get_ai_edit_plan()

    if "edit_plan" in st.session_state:
        st.subheader("AI Edit Plan")
        st.json(st.session_state["edit_plan"])

        st.info("Note: only structured fields are rendered. `editing_notes` is advice, not executable instructions.")

        if st.button("🎞️ Generate Short Video"):
            with st.spinner("Rendering video..."):
                output_path = render_video(
                    uploaded_video,
                    background_music,
                    uploaded_logo,
                    st.session_state["edit_plan"],
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
