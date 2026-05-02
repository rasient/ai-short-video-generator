# \# 🎬 AI Short Video Generator

# 

# A system for automatically transforming raw video footage into \*\*clean, cinematic short videos\*\* using motion-based editing, captions, and audio layering.

# 

# \---

# 

# \## 🚀 Overview

# 

# Most video tools require manual editing.

# 

# This system approaches the problem differently:

# 

# 👉 Detect where the action is

# 👉 Extract the most engaging moments

# 👉 Generate a short video automatically

# 

# \---

# 

# \## 🧠 Core Idea

# 

# Instead of:

# → editing everything manually

# 

# We do:

# → motion detection

# → highlight ranking

# → automated short creation

# 

# \---

# 

# \## ✨ Features

# 

# \* 🎯 Motion-based highlight detection

# \* ✂️ Automatic short video generation

# \* 🧾 Caption overlay system

# \* 🎵 Background music integration

# \* 🖼️ Logo \& credit support

# \* 📱 Horizontal \& vertical modes

# \* ⚡ Optimized for large raw footage

# 

# \---

# 

# \## 📁 Project Structure

# 

# ```id="x9y6pr"

# ai-short-video-generator/

# │

# ├── app.py

# ├── app\_fire\_horizontal\_preset.py

# ├── README.md

# ```

# 

# \---

# 

# \## 🔥 App Versions

# 

# \### 1. `app.py`

# 

# General-purpose generator:

# 

# \* vertical \& horizontal support

# \* flexible settings

# \* full control

# 

# Run:

# 

# ```bash id="0x8n6c"

# streamlit run app.py

# ```

# 

# \---

# 

# \### 2. `app\_fire\_horizontal\_preset.py`

# 

# Optimized for:

# 

# \* 🔥 fire performances

# \* 🎬 cinematic horizontal videos

# \* 📦 large raw footage

# 

# Preconfigured:

# 

# \* horizontal output

# \* lower memory usage

# \* compression-friendly

# \* stable processing for long videos

# 

# Run:

# 

# ```bash id="j7ql4k"

# streamlit run app\_fire\_horizontal\_preset.py

# ```

# 

# \---

# 

# \## 🔥 Use Case (Real Example)

# 

# Fire performance video:

# 

# Mandala of Fire × EUFlowria

# 📍 Budapest – Rakpart 2026

# 

# 👉 Raw footage → cinematic short

# 👉 Minimal manual editing

# 👉 Social-ready output

# 

# \---

# 

# \## ⚙️ Tech Stack

# 

# \* Python

# \* Streamlit

# \* MoviePy

# \* FFmpeg

# \* NumPy

# 

# \---

# 

# \## 🧩 How It Works

# 

# 1\. Upload raw video(s)

# 2\. System analyzes motion across frames

# 3\. Selects most dynamic moments

# 4\. Builds short clips

# 5\. Adds captions + audio + credits

# 6\. Exports final video

# 

# \---

# 

# \## 🛠️ Setup

# 

# ```bash id="7v3f2q"

# git clone https://github.com/rasient/ai-short-video-generator.git

# cd ai-short-video-generator

# 

# pip install -r requirements.txt

# ```

# 

# \---

# 

# \## 📁 Recommended Workflow

# 

# 1\. Compress large videos using FFmpeg

# 2\. Upload clips (or full video if optimized)

# 3\. Generate short

# 4\. Export \& publish

# 

# \---

# 

# \## ⚠️ Notes on Large Videos

# 

# \* Raw files (1–2 GB) should be compressed

# \* Recommended:

# 

# &#x20; \* 640p

# &#x20; \* 24 fps

# &#x20; \* CRF 34–36

# 

# Example:

# 

# ```bash id="qf5h2k"

# ffmpeg -i input.mp4 -vf "scale=640:-2,fps=24" -c:v libx264 -crf 34 -preset slow -c:a aac -b:a 64k output.mp4

# ```

# 

# \---

# 

# \## 🎯 Design Philosophy

# 

# This is not just a video tool.

# 

# It’s a \*\*system for extracting value from raw footage\*\*.

# 

# \---

# 

# \## 📈 Future Improvements

# 

# \* Auto compression pipeline

# \* Direct export to social platforms

# \* AI-generated captions

# \* Multi-style output (cinematic / viral / minimal)

# 

# \---

# 

# \## 👤 Author

# 

# Alexander Berg

# Systems-focused builder exploring AI + real-world applications

# 

# \---

# 

# \## 📌 Note

# 

# Videos are excluded from the repository due to size.

# Use your own footage when testing.

# 

# \---

# 

# \## 💡 Closing Thought

# 

# We don’t have a content creation problem.

# 

# We have a \*\*content extraction problem\*\*.

# 

# This project is one step toward solving it.



