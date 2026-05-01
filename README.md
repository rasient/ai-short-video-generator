# 🎬 AI Short Video Generator (Production Version)

## 🚀 Overview

AI Short Video Generator is a system-driven video editing tool that transforms raw footage into structured, high-impact short videos.

Instead of manual editing, it applies:
- motion-based scene selection
- multi-video merging
- caption layering
- branding (logo + credits)
- AI-assisted music selection

---

## 🎯 Key Features

### 🎥 Multi-Video Input
Upload multiple clips and automatically combine them into a single short video.

### 🧠 Smart Motion-Based Cutting
Detects high-motion (important) segments and prioritizes them.

### ⚡ Dynamic Speed Control
- Important scenes → slightly slowed down  
- Less relevant scenes → slightly sped up  

### 📱 Vertical Mode (9:16)
Optional crop for TikTok / Reels / Shorts.

### 📝 Captions
- Multi-line smart wrapping  
- Auto-timed display  

### 🏷️ Branding
- Logo overlay  
- Title overlay  
- Premium credit screen  

### 🎵 Music System
- AI generates search query  
- Fetches free licensed tracks (Jamendo)  
- Preview + select inside app  

### 🔇 Audio Control
- Mute original audio  
- Mix with background music  

---

## 🧠 System Thinking

This is not just a video editor.

It is a **content production system**:

Raw video  
→ motion analysis  
→ segment selection  
→ narrative structure  
→ visual + audio layering  
→ final output  

---

## 🛠️ Tech Stack

- Python  
- Streamlit  
- MoviePy  
- FFmpeg  
- OpenAI API  
- Jamendo API  
- PIL (Pillow)  

---

## ⚙️ Installation

```bash
git clone https://github.com/YOUR_USERNAME/ai-short-video-generator.git
cd ai-short-video-generator

pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file:

```
OPENAI_API_KEY=your_openai_key
JAMENDO_CLIENT_ID=your_jamendo_client_id
```

---

## ▶️ Run the App

```bash
python -m streamlit run app.py
```

---

## 🧪 Example Use Case

**Scenario:** Volunteers preparing sandwiches  

Input:
- multiple raw clips (prep, assembly, packaging)

Output:
- 30-second structured video:
  - intro → process → result  
  - captions  
  - branding  
  - music  

---

## 🔮 Future Improvements

- AI highlight detection  
- Face / object recognition  
- Auto storytelling engine  
- Engagement optimization  
- Full automation mode  
- Multi-platform export presets  

---

## 👤 Author

Alexander Berg  
Budapest, Hungary  

LinkedIn:  
https://www.linkedin.com/in/alexander-berg-7ab863242/

---

## ⭐ Final Thought

We don’t have a video editing problem.  
We have a system design problem.
