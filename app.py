import os
import tempfile
import subprocess
import requests
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)
from moviepy.video.fx.all import speedx
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

st.set_page_config(page_title="AI Short Video Generator", page_icon="🎬", layout="wide")
st.title("🎬 AI Short Video Generator")
st.write("Multi-video short generator with motion-based cuts, captions, logo, selected free music, and premium credits.")


with st.sidebar:
    st.header("Video Settings")

    target_length = st.slider("Target length seconds", 10, 90, 30)
    use_smart = st.checkbox("Smart motion-based cutting", value=True)
    vertical_mode = st.checkbox("Vertical 9:16 crop", value=False)

    st.header("Visual Settings")
    logo_size = st.slider("Logo size", 100, 700, 320)
    title_size = st.slider("Title size", 30, 120, 64)
    caption_size = st.slider("Caption size", 30, 110, 64)
    credit_size = st.slider("Credit size", 40, 140, 86)

    st.header("Audio Settings")
    mute_original = st.checkbox("Mute original audio", value=True)
    use_music = st.checkbox("Use selected free background music", value=True)
    music_volume = st.slider("Music volume", 0.05, 0.80, 0.18, step=0.01)

    st.header("Advanced")
    motion_samples = st.slider("Motion samples per video", 10, 60, 30)
    selected_moments = st.slider("Selected moments per video", 3, 12, 6)
    max_file_mb = st.slider("Large file warning threshold MB", 100, 2000, 500, step=100)


uploaded_videos = st.file_uploader(
    "Upload one or more videos",
    type=["mp4", "mov", "m4v", "avi"],
    accept_multiple_files=True,
)

uploaded_logo = st.file_uploader("Optional logo", type=["png", "jpg", "jpeg"])

title = st.text_input("Title", "Volunteers making sandwiches")
organization = st.text_input("Organization", "Budapest Bike Maffia")
credit_name = st.text_input("Your name", "Alexander Berg")
credit_role = st.text_input("Credit role", "Edited by")

captions = st.text_area(
    "Caption / felirat text",
    "Önkéntesek készítenek szendvicseket.\nEgy kis segítség.\nValódi emberi hatás.",
    height=120,
)


if uploaded_videos:
    too_large_files = []

    for uploaded_video in uploaded_videos:
        size_mb = uploaded_video.size / (1024 * 1024)

        if size_mb > max_file_mb:
            too_large_files.append((uploaded_video.name, size_mb))

    if too_large_files:
        st.warning("Some uploaded videos are very large and may fail or process very slowly.")

        for file_name, size_mb in too_large_files:
            st.write(f"⚠️ {file_name}: {size_mb:.0f} MB")

        st.info(
            "Recommended: compress large videos before upload. "
            "Target each clip under 300–500 MB, 720p/1080p, 30 sec–3 min."
        )

        st.code(
            'ffmpeg -i input.mp4 -vf "scale=1280:-2" -c:v libx264 -crf 28 -preset fast -c:a aac -b:a 96k compressed.mp4',
            language="bash",
        )


def safe_font(size):
    candidates = [
        "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue

    return ImageFont.load_default()


def save_uploaded_file(uploaded_file, path):
    with open(path, "wb") as handle:
        handle.write(uploaded_file.getbuffer())


def normalize_video(input_path, output_path):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1",
        "-metadata:s:v:0",
        "rotate=0",
        "-map_metadata",
        "-1",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]

    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def motion_score(video, time_value):
    try:
        t1 = max(0, float(time_value))
        t2 = min(float(video.duration) - 0.1, t1 + 0.5)

        if t2 <= t1:
            return 0.0

        frame_1 = video.get_frame(t1).astype(float)
        frame_2 = video.get_frame(t2).astype(float)

        return float(np.mean(np.abs(frame_1 - frame_2)))

    except Exception:
        return 0.0


def find_interesting_times(video, samples=30, top_n=6):
    duration = float(video.duration)

    if duration <= 0:
        return []

    times = np.linspace(0, max(0.1, duration - 0.1), samples)
    scored = [(float(t), motion_score(video, float(t))) for t in times]
    scored.sort(key=lambda item: item[1], reverse=True)

    top = [time_value for time_value, _ in scored[:top_n]]
    return sorted(top)


def build_short_from_video(video, custom_target_length):
    target = float(custom_target_length)

    if target <= 0:
        return video.subclip(0, min(video.duration, 1))

    if not use_smart:
        return video.subclip(0, min(video.duration, target))

    interesting_times = find_interesting_times(
        video,
        samples=int(motion_samples),
        top_n=int(selected_moments),
    )

    if not interesting_times:
        return video.subclip(0, min(video.duration, target))

    clips = []
    segment_length = max(1.0, target / max(1, len(interesting_times)))

    for time_value in interesting_times:
        start = max(0, time_value - segment_length / 2)
        end = min(video.duration, start + segment_length)

        if end <= start:
            continue

        clip = video.subclip(start, end)
        score = motion_score(video, time_value)

        if score > 20:
            clip = clip.fx(speedx, 0.92)
        else:
            clip = clip.fx(speedx, 1.05)

        clips.append(clip)

    if not clips:
        return video.subclip(0, min(video.duration, target))

    result = concatenate_videoclips(clips, method="compose")

    if result.duration > target:
        result = result.subclip(0, target)

    return result


def apply_vertical_crop(clip):
    if not vertical_mode:
        return clip

    width, height = clip.size
    target_width = int(height * 9 / 16)

    if target_width < width:
        center = width // 2
        return clip.crop(
            x1=center - target_width // 2,
            x2=center + target_width // 2,
        )

    return clip


def make_text_clip(text, size, duration, font_size, position):
    width, height = size
    overlay_height = max(180, int(height * 0.18))

    image = Image.new("RGBA", (width, overlay_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = safe_font(font_size)

    max_width = int(width * 0.85)
    words = str(text).split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    lines = lines[:3]

    y = 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2

        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 3)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 230))

        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += font_size + 12

    clip = ImageClip(np.array(image)).set_duration(duration)

    if position == "top":
        return clip.set_position(("center", int(height * 0.04)))

    return clip.set_position(("center", height - overlay_height - int(height * 0.05)))


def make_logo_clip(path, duration, width):
    image = Image.open(path).convert("RGBA")
    original_width, original_height = image.size

    new_height = int(original_height * (width / max(1, original_width)))
    image = image.resize((width, new_height), Image.Resampling.LANCZOS)

    return ImageClip(np.array(image)).set_duration(duration)


def make_credit_clip(size):
    width, height = size
    image = Image.new("RGBA", (width, height), (10, 12, 16, 255))
    draw = ImageDraw.Draw(image)

    font_org = safe_font(max(24, credit_size // 2))
    font_name = safe_font(credit_size)
    font_small = safe_font(max(22, credit_size // 3))

    y = int(height * 0.35)

    def centered(text, font, y_position, fill):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y_position), text, font=font, fill=fill)
        return y_position + (bbox[3] - bbox[1])

    y = centered(organization.upper(), font_org, y, (210, 218, 230, 255))
    y += 30

    line_width = int(width * 0.22)
    x1 = (width - line_width) // 2
    draw.rounded_rectangle(
        [x1, y, x1 + line_width, y + 4],
        radius=2,
        fill=(90, 160, 130, 255),
    )

    y += 35
    y = centered(credit_role.upper(), font_small, y, (150, 162, 178, 255))
    y += 18
    y = centered(credit_name, font_name, y, (255, 255, 255, 255))
    y += 34
    centered("SHORT VIDEO SYSTEM", font_small, y, (120, 132, 150, 255))

    return ImageClip(np.array(image)).set_duration(3.2).fadein(0.4).fadeout(0.5)


def ai_music_query(video_title, caption_text, description=""):
    if not client:
        return "soft emotional instrumental"

    prompt = f"""
Choose one simple free-music search phrase for this short video.

Title: {video_title}
Captions: {caption_text}
Description: {description}

Return only the phrase.
Example: soft emotional instrumental
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        return response.output_text.strip().replace('"', "")

    except Exception:
        return "soft emotional instrumental"


def search_jamendo_music(query, limit=5):
    client_id = os.getenv("JAMENDO_CLIENT_ID")

    if not client_id:
        st.error("Missing JAMENDO_CLIENT_ID in .env")
        return []

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

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as error:
        st.error(f"Music search failed: {error}")
        return []


def download_music(url, output_path):
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    with open(output_path, "wb") as handle:
        handle.write(response.content)

    return output_path


if st.button("Find best free music"):
    query = ai_music_query(title, captions)
    st.write("AI music search:", query)

    tracks = search_jamendo_music(query)
    st.session_state["tracks"] = tracks

if "tracks" in st.session_state and st.session_state["tracks"]:
    options = {
        f"{track['name']} — {track['artist_name']}": track
        for track in st.session_state["tracks"]
    }

    selected_label = st.selectbox("Preview and choose music", list(options.keys()))
    selected_track = options[selected_label]

    st.audio(selected_track["audio"])
    st.write("License:", selected_track.get("license_ccurl", "Check license"))

    st.session_state["selected_music_url"] = selected_track.get("audiodownload") or selected_track.get("audio")


if uploaded_videos:
    st.success(f"{len(uploaded_videos)} video(s) uploaded.")

    if st.button("Generate Short"):
        large_files = [
            uploaded_video.name
            for uploaded_video in uploaded_videos
            if uploaded_video.size / (1024 * 1024) > max_file_mb
        ]

        if large_files:
            st.error(
                "Please compress the large files before generating. "
                "This prevents Streamlit/MoviePy crashes."
            )
            st.stop()

        temp_dir = Path(tempfile.mkdtemp())
        output_path = temp_dir / "final_short_video.mp4"

        processed_clips = []
        per_video_target = max(3.0, float(target_length) / len(uploaded_videos))

        with st.spinner("Processing videos..."):
            for index, uploaded_video in enumerate(uploaded_videos):
                input_path = temp_dir / f"input_{index}.mp4"
                normalized_path = temp_dir / f"normalized_{index}.mp4"

                save_uploaded_file(uploaded_video, input_path)
                normalize_video(input_path, normalized_path)

                source_clip = VideoFileClip(str(normalized_path))
                short_clip = build_short_from_video(source_clip, per_video_target)
                processed_clips.append(short_clip)

            main_video = concatenate_videoclips(processed_clips, method="compose")

            if main_video.duration > target_length:
                main_video = main_video.subclip(0, target_length)

            main_video = apply_vertical_crop(main_video)

            if main_video.duration > 2:
                intro = main_video.subclip(0, 2).fx(speedx, 0.98)
                rest = main_video.subclip(2, main_video.duration)
                main_video = concatenate_videoclips([intro, rest], method="compose")

            output_size = (int(main_video.w), int(main_video.h))
            layers = [main_video]

            if title.strip():
                layers.append(
                    make_text_clip(
                        title,
                        output_size,
                        min(4, main_video.duration),
                        title_size,
                        "top",
                    )
                )

            caption_lines = [line.strip() for line in captions.splitlines() if line.strip()]

            if caption_lines:
                duration_per_caption = max(1.2, main_video.duration / len(caption_lines))

                for index, line in enumerate(caption_lines[:8]):
                    start_time = index * duration_per_caption

                    if start_time >= main_video.duration:
                        break

                    caption_duration = min(duration_per_caption, main_video.duration - start_time)

                    layers.append(
                        make_text_clip(
                            line,
                            output_size,
                            caption_duration,
                            caption_size,
                            "bottom",
                        ).set_start(start_time)
                    )

            if uploaded_logo:
                logo_path = temp_dir / "logo.png"
                save_uploaded_file(uploaded_logo, logo_path)

                layers.append(
                    make_logo_clip(logo_path, min(3, main_video.duration), logo_size)
                    .set_position(("center", int(output_size[1] * 0.04)))
                    .fadein(0.2)
                    .fadeout(0.2)
                )

            final_video = CompositeVideoClip(layers, size=output_size).set_duration(main_video.duration)

            credit = make_credit_clip(output_size)
            final_video = concatenate_videoclips([final_video, credit], method="compose")

            audio_tracks = []

            if not mute_original and main_video.audio:
                audio_tracks.append(main_video.audio.volumex(0.75))

            selected_music_url = st.session_state.get("selected_music_url")

            if use_music and selected_music_url:
                music_path = temp_dir / "music.mp3"
                download_music(selected_music_url, music_path)

                music_clip = AudioFileClip(str(music_path))
                music_clip = music_clip.subclip(0, min(final_video.duration, music_clip.duration))
                audio_tracks.append(music_clip.volumex(float(music_volume)))

            if audio_tracks:
                final_video = final_video.set_audio(CompositeAudioClip(audio_tracks))
            else:
                final_video = final_video.without_audio()

            max_final_duration = float(target_length) + 3.5

            if final_video.duration > max_final_duration:
                final_video = final_video.subclip(0, max_final_duration)

            if final_video.audio:
                final_video = final_video.set_audio(final_video.audio.subclip(0, final_video.duration))

            final_video.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                fps=30,
                ffmpeg_params=["-shortest", "-vf", "setsar=1"],
            )

        st.success("Done!")

        preview_left, preview_center, preview_right = st.columns([1, 2, 1])

        with preview_center:
            st.video(str(output_path), width=320)

        with open(output_path, "rb") as handle:
            st.download_button(
                "Download final short video",
                handle,
                "final_short_video.mp4",
                "video/mp4",
            )
else:
    st.info("Upload one or more videos to begin.")
