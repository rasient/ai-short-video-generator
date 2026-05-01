import os
import requests
import tempfile
import subprocess
import imageio_ffmpeg
from pathlib import Path

import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    ImageClip,
    concatenate_videoclips,
)
from moviepy.video.fx.all import speedx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

st.set_page_config(page_title="AI Short Video Generator", layout="wide")
st.title("🎬 AI Short Video Generator")

with st.sidebar:
    target_length = st.slider("Target length (sec)", 10, 90, 30)
    use_smart = st.checkbox("Smart scene cutting", True)
    sensitivity = st.slider("Scene sensitivity", 10.0, 80.0, 24.0)
    logo_size = st.slider("Logo size", 100, 700, 320)
    caption_size = st.slider("Caption size", 30, 110, 64)
    credit_size = st.slider("Credit size", 40, 140, 86)
    mute_original = st.checkbox("Mute original audio", True)
    use_music = st.checkbox("Use background music", True)

uploaded_video = st.file_uploader("Upload video", type=["mp4", "mov", "m4v"])
uploaded_logo = st.file_uploader("Optional logo", type=["png", "jpg", "jpeg"])

music_file = None
if use_music:
    st.info("Use 'Find best free music' below, preview a track, then generate the video.")

title = st.text_input("Title", "Volunteers making sandwiches")
organization = st.text_input("Organization", "Budapest Bike Maffia")
name = st.text_input("Your name", "Alexander Berg")
role = st.text_input("Role", "Edited by")

captions = st.text_area(
    "Caption / felirat text",
    "Önkéntesek készítenek szendvicseket.\nEgy kis segítség.\nValódi emberi hatás.",
    height=120,
)


def font(size, bold=False):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def text_clip(text, size, duration, font_size, position):
    w, h = size
    img_h = max(180, int(h * 0.18))
    img = Image.new("RGBA", (w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    f = font(font_size, True)

    lines = []
    words = text.split()
    cur = ""

    for word in words:
        test = (cur + " " + word).strip()
        box = draw.textbbox((0, 0), test, font=f)
        if box[2] - box[0] < int(w * 0.85):
            cur = test
        else:
            lines.append(cur)
            cur = word

    if cur:
        lines.append(cur)

    lines = lines[:3]
    y = 20

    for line in lines:
        box = draw.textbbox((0, 0), line, font=f)
        x = (w - (box[2] - box[0])) // 2

        for dx, dy in [(-3,-3), (3,-3), (-3,3), (3,3)]:
            draw.text((x+dx, y+dy), line, font=f, fill=(0,0,0,230))

        draw.text((x, y), line, font=f, fill=(255,255,255,255))
        y += font_size + 12

    clip = ImageClip(np.array(img)).set_duration(duration)

    if position == "top":
        return clip.set_position(("center", int(h * 0.04)))

    return clip.set_position(("center", h - img_h - int(h * 0.05)))


def logo_clip(path, duration, width):
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    new_h = int(h * (width / w))
    img = img.resize((width, new_h), Image.Resampling.LANCZOS)
    return ImageClip(np.array(img)).set_duration(duration)


def credit_clip(size):
    w, h = size
    img = Image.new("RGBA", (w, h), (10, 12, 16, 255))
    draw = ImageDraw.Draw(img)

    f1 = font(max(24, credit_size // 2), False)
    f2 = font(credit_size, True)
    f3 = font(max(22, credit_size // 3), False)

    y = int(h * 0.35)

    def center(txt, fnt, y_pos, fill):
        box = draw.textbbox((0, 0), txt, font=fnt)
        x = (w - (box[2] - box[0])) // 2
        draw.text((x, y_pos), txt, font=fnt, fill=fill)
        return y_pos + (box[3] - box[1])

    y = center(organization.upper(), f1, y, (210, 218, 230, 255))
    y += 30

    line_w = int(w * 0.22)
    x1 = (w - line_w) // 2
    draw.rounded_rectangle([x1, y, x1 + line_w, y + 4], radius=2, fill=(90, 160, 130, 255))
    y += 35

    y = center(role.upper(), f3, y, (150, 162, 178, 255))
    y += 18

    y = center(name, f2, y, (255, 255, 255, 255))
    y += 34

    center("SHORT VIDEO SYSTEM", f3, y, (120, 132, 150, 255))

    return ImageClip(np.array(img)).set_duration(3.2).fadein(0.5).fadeout(0.5)

def build(video):
    max_output_seconds = float(target_length)

    if not use_smart:
        return video.subclip(0, min(video.duration, max_output_seconds))

    clips = []

    # Show the whole sandwich-making process:
    # beginning → middle → end
    steps = 5
    clip_length = max_output_seconds / steps
    video_duration = float(video.duration)

    if video_duration <= max_output_seconds:
        return video.subclip(0, video_duration)

    for i in range(steps):
        position = i / max(1, steps - 1)
        start = position * max(0, video_duration - clip_length)
        end = min(start + clip_length, video_duration)

        clip = video.subclip(start, end)

        # Slow down action/process moments slightly
        clip = clip.fx(speedx, 1.0)

        clips.append(clip)

    final_short = concatenate_videoclips(clips, method="compose")

    if final_short.duration > max_output_seconds:
        final_short = final_short.subclip(0, max_output_seconds)

    return final_short

def normalize_video(input_path, output_path):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg,
        "-y",
        "-i", str(input_path),
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1",
        "-metadata:s:v:0", "rotate=0",
        "-map_metadata", "-1",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-shortest",
        str(output_path),
    ]

    subprocess.run(cmd, check=True)
    
def ai_music_query(title, captions, description=""):
    text = f"""
    Choose 3 short music search keywords for this video.
    Video title: {title}
    Captions: {captions}
    Description: {description}

    Return only a simple search phrase.
    Example: soft emotional instrumental
    """

    if not client:
        return "soft emotional instrumental"

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=text,
    )

    return response.output_text.strip().replace('"', "")
    
def search_jamendo_music(query, limit=5):
    client_id = os.getenv("JAMENDO_CLIENT_ID")

    url = "https://api.jamendo.com/v3.0/tracks/"
    params = {
        "client_id": client_id,
        "format": "json",
        "limit": limit,
        "search": query,
        "include": "licenses musicinfo",
        "audioformat": "mp32",
        "audiodlformat": "mp32",
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()

    return r.json().get("results", [])
    
def download_music(url, output_path):
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(r.content)

    return output_path
    
if st.button("Find best free music"):
    query = ai_music_query(title, captions)
    st.write("AI music search:", query)

    tracks = search_jamendo_music(query)
    st.session_state["tracks"] = tracks

if "tracks" in st.session_state:
    options = {
        f"{t['name']} — {t['artist_name']}": t
        for t in st.session_state["tracks"]
    }

    selected = st.selectbox("Preview and choose music", list(options.keys()))
    track = options[selected]

    st.audio(track["audio"])
    st.write("License:", track.get("license_ccurl", "Check license"))

    st.session_state["selected_music_url"] = track.get("audiodownload") or track.get("audio")

if uploaded_video:
    if st.button("Generate Short"):
        temp = Path(tempfile.mkdtemp())

        video_path = temp / "input.mp4"
        out_path = temp / "output.mp4"

        with open(video_path, "wb") as f:
            f.write(uploaded_video.getbuffer())

        normalized_path = temp / "normalized.mp4"
        normalize_video(video_path, normalized_path)
        video = VideoFileClip(str(normalized_path))
        short = build(video)

        size = (int(short.w), int(short.h))
        layers = [short]

        layers.append(text_clip(title, size, min(4, short.duration), caption_size, "top"))

        cap_lines = [x.strip() for x in captions.splitlines() if x.strip()]
        if cap_lines:
            dur = max(1.2, short.duration / len(cap_lines))
            for i, line in enumerate(cap_lines[:8]):
                start = i * dur
                if start >= short.duration:
                    break
                layers.append(text_clip(line, size, min(dur, short.duration - start), caption_size, "bottom").set_start(start))

        if uploaded_logo:
            logo_path = temp / "logo.png"
            with open(logo_path, "wb") as f:
                f.write(uploaded_logo.getbuffer())

            layers.append(
                logo_clip(logo_path, min(3, short.duration), logo_size)
                .set_position(("center", int(size[1] * 0.04)))
                .fadein(0.2)
                .fadeout(0.2)
            )

        final = CompositeVideoClip(layers, size=size).set_duration(short.duration)

        credit = credit_clip(size)
        final = concatenate_videoclips([final, credit], method="compose")

        audio_tracks = []

        if not mute_original and short.audio:
            audio_tracks.append(short.audio.volumex(0.75))

        if use_music and st.session_state.get("selected_music_url"):
            music_path = temp / "music.mp3"
            download_music(st.session_state["selected_music_url"], music_path)

            music_clip = AudioFileClip(str(music_path))
            music_clip = music_clip.subclip(0, min(final.duration, music_clip.duration))
            audio_tracks.append(music_clip.volumex(0.18))

        if audio_tracks:
            final = final.set_audio(CompositeAudioClip(audio_tracks))
        else:
            final = final.without_audio()

        max_final_duration = float(target_length) + 3.5

        if final.duration > max_final_duration:
            final = final.subclip(0, max_final_duration)

        if final.audio:
            final = final.set_audio(final.audio.subclip(0, final.duration))

        final.write_videofile(
            str(out_path),
            codec="libx264",
            audio_codec="aac",
            fps=30,
            ffmpeg_params=["-shortest", "-vf", "setsar=1"],
        )

        st.success("Done!")
        col1, col2, col3 = st.columns([1,2,1])

        with col2:
            st.video(str(out_path), width=320)

        with open(out_path, "rb") as f:
            st.download_button("Download video", f, "final_short_video.mp4", "video/mp4")
