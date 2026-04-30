import os
import json
import tempfile
import subprocess
from pathlib import Path

import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from openai import OpenAI
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

load_dotenv()

st.set_page_config(page_title="AI Short Video Generator", page_icon="🎬", layout="wide")

st.title("🎬 AI Short Video Generator")
st.write("Upload a raw video and generate a short video with smart cuts, captions, logo, music, and premium credit.")

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

with st.sidebar:
st.header("Video Settings")

```
target_format = st.selectbox(
    "Output format",
    ["Same as original - no resize", "9:16 vertical", "1:1 square", "16:9 horizontal"],
    index=0,
)

resize_mode = st.selectbox(
    "Resize mode",
    ["Fit with padding - never stretch", "Crop to fill - best for Shorts/Reels"],
    index=0,
)

target_length = st.slider("Target length seconds", 10, 90, 30)

st.subheader("Smart Scene Cutting")
use_smart_cutting = st.checkbox("Use smart scene cutting", value=True)
max_scenes = st.slider("Maximum scenes", 1, 8, 4)
min_scene_seconds = st.slider("Minimum scene length", 1.0, 8.0, 2.0, step=0.5)
scene_sensitivity = st.slider("Scene sensitivity", 10.0, 80.0, 32.0, step=2.0)

st.subheader("Overlays")
logo_width = st.slider("Logo size", 120, 700, 380)
title_size = st.slider("Title size", 40, 130, 84)
caption_size = st.slider("Caption size", 36, 120, 78)
credit_size = st.slider("Credit name size", 40, 140, 92)

mute_original = st.checkbox("Mute original audio", value=False)
add_title = st.checkbox("Add title overlay", value=True)
add_captions = st.checkbox("Add captions / felirat", value=True)
add_credit = st.checkbox("Add premium credit screen", value=True)
use_music = st.checkbox("Use background music", value=False)
use_fade = st.checkbox("Use gentle fade", value=True)
```

uploaded_video = st.file_uploader("Upload video", type=["mp4", "mov", "m4v", "avi"])
uploaded_logo = st.file_uploader("Optional logo", type=["png", "jpg", "jpeg"])

col1, col2 = st.columns(2)

with col1:
title = st.text_input("Short video title", "Volunteers making sandwiches")
organization = st.text_input("Organization / project", "Budapest Bike Maffia")
credit_role = st.text_input("Credit role", "Edited by")
credit_name = st.text_input("Your name", "Alexander Berg")

with col2:
description = st.text_area(
"Description / instructions",
"Make this emotional, human, short, with Hungarian captions.",
height=120,
)

caption_text = st.text_area(
"Caption / felirat text",
"Önkéntesek készítenek szendvicseket.\nEgy kis segítség.\nValódi emberi hatás.",
height=140,
)

background_music = None
if use_music:
background_music = st.file_uploader("Upload background music", type=["mp3", "wav", "m4a"])

def save_uploaded_file(uploaded_file, path):
with open(path, "wb") as f:
f.write(uploaded_file.getbuffer())

def get_target_size(fmt):
if fmt == "9:16 vertical":
return 1080, 1920
if fmt == "1:1 square":
return 1080, 1080
if fmt == "16:9 horizontal":
return 1920, 1080
return None

def ffmpeg_resize(input_path, output_path, fmt, mode):
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

```
if fmt == "Same as original - no resize":
    vf = "setsar=1"
else:
    w, h = get_target_size(fmt)
    if mode.startswith("Crop"):
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"
    else:
        vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"

cmd = [
    ffmpeg_exe,
    "-y",
    "-i",
    str(input_path),
    "-vf",
    vf,
    "-c:v",
    "libx264",
    "-preset",
    "veryfast",
    "-crf",
    "23",
    "-c:a",
    "aac",
    "-movflags",
    "+faststart",
    str(output_path),
]

subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
```

def load_font(size, bold=False):
candidates = [
"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
"/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
]

```
for path in candidates:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        pass

return ImageFont.load_default()
```

def make_text_overlay(text, duration, size, position="bottom", font_size=78):
width, height = size
overlay_h = max(280, int(height * 0.17)) if position == "bottom" else max(240, int(height * 0.14))

```
img = Image.new("RGBA", (width, overlay_h), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
font = load_font(font_size, bold=True)

max_width = int(width * 0.86)
words = text.split()
lines = []
current = ""

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

lines = lines[:3]
line_h = font_size + 14
total_h = len(lines) * line_h
y = max(8, (overlay_h - total_h) // 2)

for line in lines:
    bbox = draw.textbbox((0, 0), line, font=font)
    text_w = bbox[2] - bbox[0]
    x = (width - text_w) // 2

    for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4), (0, 4)]:
        draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 230))

    draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
    y += line_h

clip = ImageClip(np.array(img)).set_duration(duration)

if position == "top":
    return clip.set_position(("center", int(height * 0.04)))

return clip.set_position(("center", height - overlay_h - int(height * 0.04)))
```

def make_logo_clip(logo_path, duration, target_width):
img = Image.open(logo_path).convert("RGBA")
w, h = img.size
scale = target_width / max(1, w)
new_h = max(1, int(h * scale))
img = img.resize((target_width, new_h), Image.Resampling.LANCZOS)
return ImageClip(np.array(img)).set_duration(duration)

def centered_text(draw, text, font, y, width, fill):
bbox = draw.textbbox((0, 0), text, font=font)
x = (width - (bbox[2] - bbox[0])) // 2
draw.text((x, y), text, font=font, fill=fill)
return y + (bbox[3] - bbox[1])

def make_premium_credit(size, organization, role, name, duration=3.2, name_size=92):
width, height = size
img = Image.new("RGBA", (width, height), (10, 12, 16, 255))
draw = ImageDraw.Draw(img)

```
for y in range(height):
    alpha = int(18 * (y / max(1, height)))
    draw.line([(0, y), (width, y)], fill=(18 + alpha, 22 + alpha, 30 + alpha, 255))

org_font = load_font(max(28, int(name_size * 0.38)), bold=False)
role_font = load_font(max(30, int(name_size * 0.48)), bold=False)
name_font = load_font(name_size, bold=True)
small_font = load_font(max(24, int(name_size * 0.30)), bold=False)

org = (organization or "Budapest Bike Maffia").upper()
role_text = (role or "Edited by").upper()
person = name or "Alexander Berg"

y = int(height * 0.37)

y = centered_text(draw, org, org_font, y, width, (210, 218, 230, 255))
y += 32

line_w = int(width * 0.22)
x1 = (width - line_w) // 2
draw.rounded_rectangle([x1, y, x1 + line_w, y + 4], radius=2, fill=(90, 160, 130, 255))
y += 36

y = centered_text(draw, role_text, role_font, y, width, (150, 162, 178, 255))
y += 18

y = centered_text(draw, person, name_font, y, width, (255, 255, 255, 255))
y += 34

centered_text(draw, "SHORT VIDEO SYSTEM", small_font, y, width, (120, 132, 150, 255))

margin = int(min(width, height) * 0.045)
draw.rounded_rectangle(
    [margin, margin, width - margin, height - margin],
    radius=26,
    outline=(255, 255, 255, 28),
    width=2,
)

return ImageClip(np.array(img)).set_duration(duration).fadein(0.45).fadeout(0.55)
```

def detect_scene_segments(video, sensitivity, min_scene_len):
duration = float(video.duration)
cuts = [0.0]
previous = None
motion_scores = []

```
for t in np.arange(0, duration, 1.0):
    try:
        frame = video.get_frame(float(t))
        small = Image.fromarray(frame).convert("L").resize((96, 54))
        arr = np.array(small).astype("float32")

        if previous is not None:
            diff = float(np.mean(np.abs(arr - previous)))
            motion_scores.append((float(t), diff))

            if diff > sensitivity and float(t) - cuts[-1] >= min_scene_len:
                cuts.append(float(t))

        previous = arr
    except Exception:
        continue

if cuts[-1] < duration:
    cuts.append(duration)

segments = []

for i in range(len(cuts) - 1):
    start = cuts[i]
    end = cuts[i + 1]

    if end - start < min_scene_len:
        continue

    scores = [score for ts, score in motion_scores if start <= ts < end]
    avg_motion = float(np.mean(scores)) if scores else 0.0
    score = avg_motion + min(end - start, 8.0) * 1.5 + (2.0 if start > 1.0 else 0.0)

    segments.append(
        {
            "start": round(start, 2),
            "end": round(end, 2),
            "score": round(score, 2),
        }
    )

if not segments:
    segments = [{"start": 0.0, "end": round(min(duration, target_length), 2), "score": 1.0}]

return segments
```

def choose_best_segments(segments, target_duration, max_count):
ranked = sorted(segments, key=lambda x: x["score"], reverse=True)
selected = []
total = 0.0

```
for seg in ranked:
    if len(selected) >= max_count:
        break

    remaining = target_duration - total
    if remaining <= 0:
        break

    seg_len = seg["end"] - seg["start"]
    if seg_len <= 0:
        continue

    take = min(seg_len, remaining)

    selected.append(
        {
            "start": seg["start"],
            "end": round(seg["start"] + take, 2),
            "score": seg["score"],
        }
    )

    total += take

selected = sorted(selected, key=lambda x: x["start"])

if not selected and segments:
    selected = [segments[0]]

return selected
```

def build_smart_short(video):
segments = detect_scene_segments(video, scene_sensitivity, min_scene_seconds)
selected = choose_best_segments(segments, float(target_length), int(max_scenes))

```
clips = []

for seg in selected:
    try:
        clips.append(video.subclip(seg["start"], seg["end"]))
    except Exception:
        pass

if not clips:
    return video.subclip(0, min(video.duration, target_length)), selected

if len(clips) == 1:
    return clips[0], selected

return concatenate_videoclips(clips, method="compose"), selected
```

def fallback_plan():
caption_lines = [line.strip() for line in caption_text.splitlines() if line.strip()]

```
return {
    "hook": title,
    "caption_lines": caption_lines,
    "logo_overlay_seconds": 2,
    "credit_screen_text": f"{organization} ©\n{credit_role} {credit_name}",
    "editing_notes": "Fallback plan used.",
}
```

def ai_plan():
if not client:
return fallback_plan()

```
prompt = f"""
```

Return only valid JSON.

Create a short-video edit plan.

Fields:
hook
caption_lines
logo_overlay_seconds
credit_screen_text
editing_notes

Title: {title}
Description: {description}
Captions:
{caption_text}

Credit:
{organization} ©
{credit_role} {credit_name}
"""

````
try:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    text = response.output_text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)

except Exception as e:
    plan = fallback_plan()
    plan["editing_notes"] = f"AI failed, fallback used: {e}"
    return plan
````

def concatenate_safe(clips, target_size):
fixed = []
target_w, target_h = target_size

```
for clip in clips:
    if tuple(clip.size) != tuple(target_size):
        bg = ColorClip(size=(target_w, target_h), color=(0, 0, 0)).set_duration(clip.duration)
        clip = CompositeVideoClip(
            [bg, clip.set_position(("center", "center"))],
            size=(target_w, target_h),
        ).set_duration(clip.duration)

    fixed.append(clip)

return concatenate_videoclips(fixed, method="compose")
```

def render_video(uploaded_video, uploaded_logo, uploaded_music, plan):
temp_dir = Path(tempfile.mkdtemp())

```
input_path = temp_dir / "input.mp4"
trimmed_path = temp_dir / "trimmed.mp4"
resized_path = temp_dir / "resized.mp4"
output_path = temp_dir / "final.mp4"

save_uploaded_file(uploaded_video, input_path)

video = VideoFileClip(str(input_path))

if use_smart_cutting:
    short, selected = build_smart_short(video)
    st.session_state["selected_segments"] = selected
else:
    short = video.subclip(0, min(video.duration, target_length))
    st.session_state["selected_segments"] = [{"start": 0, "end": min(video.duration, target_length), "score": 0}]

short.write_videofile(
    str(trimmed_path),
    codec="libx264",
    audio_codec="aac",
    fps=30,
    preset="ultrafast",
    threads=2,
    verbose=False,
    logger=None,
    ffmpeg_params=["-vf", "setsar=1"],
)

ffmpeg_resize(trimmed_path, resized_path, target_format, resize_mode)

base_video = VideoFileClip(str(resized_path))
size = (int(base_video.w), int(base_video.h))

if use_fade:
    base_video = base_video.fadein(0.2).fadeout(0.3)

layers = [base_video]

if uploaded_logo is not None:
    logo_path = temp_dir / "logo.png"
    save_uploaded_file(uploaded_logo, logo_path)

    logo = (
        make_logo_clip(
            logo_path,
            min(float(plan.get("logo_overlay_seconds", 2)), base_video.duration),
            logo_width,
        )
        .set_position(("center", int(size[1] * 0.04)))
        .fadein(0.15)
        .fadeout(0.2)
    )

    layers.append(logo)

if add_title:
    layers.append(
        make_text_overlay(
            plan.get("hook", title),
            min(4, base_video.duration),
            size,
            "top",
            title_size,
        )
    )

if add_captions:
    lines = plan.get("caption_lines", [])
    lines = [line for line in lines if str(line).strip()][:8]

    if lines:
        segment_duration = max(1.2, base_video.duration / len(lines))

        for i, line in enumerate(lines):
            start = i * segment_duration

            if start >= base_video.duration:
                break

            duration = min(segment_duration, base_video.duration - start)

            layers.append(
                make_text_overlay(
                    str(line),
                    duration,
                    size,
                    "bottom",
                    caption_size,
                ).set_start(start)
            )

final = CompositeVideoClip(layers, size=size).set_duration(base_video.duration)

if add_credit:
    credit = make_premium_credit(
        size,
        organization,
        credit_role,
        credit_name,
        duration=3.2,
        name_size=credit_size,
    )
    final = concatenate_safe([final, credit], size)

audio_tracks = []

if not mute_original and base_video.audio:
    audio_tracks.append(base_video.audio.volumex(0.75))

if uploaded_music is not None:
    music_path = temp_dir / "music.mp3"
    save_uploaded_file(uploaded_music, music_path)

    music = AudioFileClip(str(music_path))
    music = music.subclip(0, min(final.duration, music.duration)).volumex(0.18)
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
    ffmpeg_params=["-vf", "setsar=1"],
)

return output_path
```

if uploaded_video:
st.video(uploaded_video)

```
if st.button("✨ Generate AI edit plan"):
    with st.spinner("Creating AI edit plan..."):
        st.session_state["plan"] = ai_plan()

if "plan" in st.session_state:
    st.subheader("AI Edit Plan")
    st.json(st.session_state["plan"])

    if st.button("🎞️ Generate Short Video"):
        with st.spinner("Rendering video..."):
            output = render_video(
                uploaded_video,
                uploaded_logo,
                background_music,
                st.session_state["plan"],
            )

            st.success("Short video generated.")

            st.subheader("Selected scenes")
            st.json(st.session_state.get("selected_segments", []))

            st.video(str(output))

            with open(output, "rb") as f:
                st.download_button(
                    "Download final short video",
                    data=f,
                    file_name="final_short_video.mp4",
                    mime="video/mp4",
                )
```

else:
st.info("Upload a video to begin.")
