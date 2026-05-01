# 🎬 AI Short Video Generator

Create high-quality short videos automatically from one or more input videos.

## 🚀 Features
- Multi-video upload & merging
- Smart motion-based scene selection
- Caption overlays (top + bottom)
- Logo overlay
- Credit screen
- Vertical (9:16) mode
- AI-powered music search (Jamendo)
- Free music preview + selection
- Automatic video normalization (FFmpeg)
- Large file protection & warnings

---

## ⚙️ Setup

### 1. Clone repo
```bash
git clone https://github.com/YOUR_USERNAME/ai-short-video-generator.git
cd ai-short-video-generator
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create `.env`
```env
OPENAI_API_KEY=your_openai_key
JAMENDO_CLIENT_ID=your_jamendo_client_id
```

---

## ▶️ Run the app
```bash
streamlit run app.py
```

---

## 🎯 Usage
1. Upload one or more videos
2. (Optional) Upload logo
3. Click **Find best free music**
4. Preview & select music
5. Click **Generate Short**
6. Download final video

---

## ⚠️ Large Files
- Files over ~500MB may fail
- Recommended:
  - 720p–1080p
  - under 300–500MB per file

### Compress video
```bash
ffmpeg -i input.mp4 -vf "scale=1280:-2" -c:v libx264 -crf 28 -preset fast -c:a aac -b:a 96k output.mp4
```

---

## 🔮 Future Improvements
- Auto caption generation (speech-to-text)
- Face tracking for better vertical crops
- AI highlight detection (beyond motion)
- Beat-sync editing with music
- Drag-and-drop timeline editor
- Export presets (TikTok, Reels, Shorts)
- Cloud rendering support

---

## 💡 Tech Stack
- Streamlit
- MoviePy
- FFmpeg
- OpenAI API
- Jamendo API
- Pillow (PIL)
- NumPy

---

## 📦 Output
- MP4 (H.264)
- AAC audio
- Optimized for social media

---

## 👤 Author
Alexander Berg

---

## ⭐ If you like it
Give it a star on GitHub and share 🚀
