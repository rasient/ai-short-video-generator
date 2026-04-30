# \# 🎬 AI Short Video Generator

# 

# A Streamlit app that turns raw videos into short-form content using \*\*AI + smart scene detection\*\*.

# 

# \---

# 

# \# 🚀 What this app does

# 

# \* Upload a raw video

# \* Generate an AI edit plan (ChatGPT)

# \* Automatically detect important scenes

# \* Cut the video into a short (no manual editing needed)

# \* Add:

# 

# &#x20; \* Title overlay

# &#x20; \* Captions / felirat

# &#x20; \* Optional logo

# &#x20; \* Optional background music

# &#x20; \* Premium credit screen

# \* Export a ready-to-post short video

# 

# \---

# 

# \# 🧠 Core idea

# 

# Most tools edit video.

# 

# This tool decides:

# 

# > \*\*Which parts of the video actually matter\*\*

# 

# \---

# 

# \# ✂️ Smart Scene Cutting

# 

# The app uses lightweight scene detection:

# 

# 1\. Samples frames across the video

# 2\. Detects visual changes

# 3\. Splits into segments

# 4\. Selects best scenes

# 5\. Combines them into a short

# 

# No manual trimming needed.

# 

# \---

# 

# \# 🎬 Premium Credit Screen

# 

# The video ends with a clean LinkedIn-style credit:

# 

# ```

# BUDAPEST BIKE MAFFIA

# 

# ────────

# 

# EDITED BY

# 

# Alexander Berg

# ```

# 

# Features:

# 

# \* Centered layout

# \* Clean typography

# \* Dark premium background

# \* Fade in / fade out

# 

# \---

# 

# \# ⚙️ Recommended Settings

# 

# ```

# Output format: Same as original - no resize

# Target length: 30 sec

# 

# Smart scene cutting: ON

# Scenes: 4

# Sensitivity: 32

# 

# Logo size: 380

# Caption size: 78

# Credit size: 92

# ```

# 

# \---

# 

# \# 📦 Installation

# 

# ```bash

# pip install -r requirements.txt

# ```

# 

# \---

# 

# \# ▶️ Run the app

# 

# ```bash

# streamlit run app.py

# ```

# 

# \---

# 

# \# 🔐 Environment variables

# 

# Create a `.env` file:

# 

# ```env

# OPENAI\_API\_KEY=your\_api\_key\_here

# ```

# 

# \---

# 

# \# 🧪 Tech Stack

# 

# \* Streamlit

# \* OpenAI API

# \* MoviePy

# \* Pillow

# \* NumPy

# \* FFmpeg (via imageio-ffmpeg)

# 

# \---

# 

# \# ⚠️ Notes

# 

# \* The AI generates a plan, but:

# 

# &#x20; \* only structured fields are executed

# &#x20; \* `editing\_notes` is informational

# \* Smart cutting works even without AI

# \* “Same as original” avoids video stretching issues

# 

# \---

# 

# \# 🔮 Recommended Future Features

# 

# \* 🎤 Whisper auto-transcription

# \* ⏱️ Word-level subtitle timing

# \* 🧠 Face / emotion detection

# \* 🎵 Beat-based editing

# \* 📱 Export presets (TikTok / Reels / Shorts)

# \* 🎨 Brand templates

# \* 📊 Analytics (views, retention)

# \* ☁️ Cloud rendering queue

# 

# \---

# 

# \# 👤 Author

# 

# \*\*Alexander Berg\*\*

# Budapest, Hungary

# 

# \---

# 

# \# 💡 Vision

# 

# This is not just a video editor.

# 

# It’s a step toward:

# 

# > \*\*AI-powered content systems that understand what matters\*\*



