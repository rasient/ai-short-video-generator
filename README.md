# AI Short Video Generator MVP

A Streamlit MVP for turning raw videos into short social videos.

## What the app does

- Upload a raw video
- Add a title, URL, and description
- Generate an AI edit plan with ChatGPT/OpenAI
- Trim the video
- Add title overlay
- Add captions / felirat
- Mute original audio if needed
- Add optional background music
- Export a short MP4 video

## Current MVP limitations

- Captions are currently based on manually pasted transcript/caption text.
- The app does not yet automatically transcribe speech from video.
- The app creates a simple edit plan but does not yet detect visual highlights automatically.
- Rendering can be slow for long videos.
- Some systems may need ImageMagick configured for MoviePy text overlays.

## Recommended future features

### 1. Automatic speech-to-text transcription

Add Whisper/OpenAI transcription so the user can upload a video and automatically generate captions from the spoken audio.

### 2. Hungarian + English caption modes

Add language options:

- Hungarian captions
- English captions
- Bilingual captions
- Auto-translate captions

### 3. Auto-cut highlight detection

Analyze the transcript and video timeline to find the strongest moments automatically:

- emotional moments
- key sentences
- speaker pauses
- strong hooks
- repeated ideas
- call-to-action moments

### 4. Short-video templates

Add preset editing styles:

- LinkedIn professional
- TikTok fast-cut
- NGO / volunteer story
- educational explainer
- emotional documentary
- system-thinking commentary

### 5. Brand kit

Allow users to save recurring brand settings:

- font
- colors
- logo
- caption style
- intro/outro style
- default CTA

### 6. AI title and caption generator

Generate platform-ready text:

- LinkedIn post
- YouTube Shorts title
- TikTok caption
- Instagram Reel caption
- hashtags
- first-comment CTA

### 7. Background music recommendation

Let AI recommend background music mood based on the story:

- soft inspirational
- energetic
- emotional
- documentary
- hopeful
- dramatic

### 8. Audio cleanup

Add basic audio processing:

- noise reduction
- voice volume boost
- automatic mute during background noise
- music ducking under speech

### 9. Scene detection

Automatically detect scene changes and cut boring sections.

### 10. Timeline editor

Add a visual timeline where the user can adjust:

- start/end time
- caption timing
- music volume
- title placement
- mute sections

### 11. Direct social export formats

Add export presets:

- LinkedIn 1:1
- LinkedIn vertical
- TikTok 9:16
- YouTube Shorts 9:16
- Instagram Reels 9:16

### 12. Cloud storage and history

Save generated projects with:

- original video
- edit plan
- captions
- final video
- post text
- analytics notes

## Project structure

```text
ai_short_video_generator/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```
