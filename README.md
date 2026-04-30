# AI Short Video Generator

A Streamlit MVP that turns a raw video into a short social video.

## Features

- Upload raw video
- Add title, URL, and description
- Generate an AI edit plan with OpenAI / ChatGPT
- Trim the video
- Add title overlay
- Add captions / felirat
- Mute original audio if needed
- Add background music
- Export MP4

## Local setup

### 1. Download or clone this project

```bash
git clone https://github.com/YOUR_USERNAME/ai-short-video-generator.git
cd ai-short-video-generator
```

Or download the ZIP and extract it.

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Mac / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your OpenAI API key

Create a file named `.env` in the project folder:

```env
OPENAI_API_KEY=your_api_key_here
```

### 5. Run the app

```bash
streamlit run app.py
```

## Streamlit Cloud deployment

### 1. Push the project to GitHub

Create a new GitHub repository, then run:

```bash
git init
git add .
git commit -m "Initial AI short video generator MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-short-video-generator.git
git push -u origin main
```

### 2. Deploy on Streamlit

1. Go to Streamlit Community Cloud.
2. Click **New app**.
3. Choose your GitHub repository.
4. Set main file path to:

```text
app.py
```

5. Open **Advanced settings**.
6. Add this secret:

```toml
OPENAI_API_KEY = "your_api_key_here"
```

7. Click **Deploy**.

## Important notes

This is an MVP. It does not yet auto-transcribe speech from the video.

Best next upgrade:

```text
Video audio → Whisper transcription → GPT caption rewrite → automatic burned subtitles
```

## Recommended future features

- Automatic speech-to-text transcription
- Auto scene detection
- Auto highlight detection
- Subtitle timing per spoken sentence
- Logo/watermark upload
- Multiple export formats
- LinkedIn/TikTok/Instagram templates
- Hungarian/English caption mode
- Direct social-media caption generation


## Cloud compatibility note

This repo includes `runtime.txt` to force Python 3.11 on Streamlit Cloud and pins Pillow/MoviePy versions to avoid video resize crashes caused by incompatible dependency versions.
