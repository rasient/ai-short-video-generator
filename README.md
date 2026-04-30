# AI Short Video Generator

A Streamlit MVP that turns raw videos into short-form social content.

## What it does

- Upload raw video
- Add title / URL / description
- Generate AI edit plan
- Trim video
- Add title overlay
- Add Hungarian captions / felirat
- Optional mute
- Optional background music
- Optional logo overlay
- Optional credit screen
- Export MP4

## Important note

The renderer only executes structured fields from the AI plan, such as:

- `hook`
- `recommended_start`
- `recommended_end`
- `caption_lines`
- `logo_overlay_seconds`
- `credit_screen_text`

The `editing_notes` field is shown as guidance only. It is not automatically executed unless the feature is implemented in the renderer.

## Recommended future features

- Whisper auto-transcription
- Automatic subtitle timing by speech
- Real scene detection
- Automatic jump cuts
- Beat-synced music cuts
- Logo placement presets
- Brand template system
- Multi-language subtitles
- LinkedIn / TikTok / YouTube Shorts export presets
- Batch processing
- Cloud rendering queue
