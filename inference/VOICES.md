# Voice prompts (.pt and .wav)

Terminology: see /JARGON.md at the repo root.

PersonaPlex does zero-shot voice cloning. It needs ONE short audio sample of the voice you want it to imitate; from then on, the agent speaks in that voice. "Zero-shot" means we never fine-tune the model on the voice — we just hand it the sample at inference time. The sample itself IS required.

## Where samples come from

- Stock voices (today): NVIDIA ships 17 pre-encoded `.pt` files inside `voices.tgz` in the PersonaPlex HF repo. `voice_app.py:111` downloads the tarball at container build time, extracts it once, and `inference/moshi/server.py:152` loads the requested `.pt` per WebSocket handshake. IDs: `NATF0..NATF3`, `NATM0..NATM3`, `VARF0..VARF4`, `VARM0..VARM3`. Naming is acoustic: NAT = natural (TortoiseTTS), VAR = pitch/formant-shifted variants via Praat. No character mapping — just timbres.
- Our curated voices (TODO): when we add more voices (different accents, characters, public-domain speakers we've licensed), we encode each into a `.pt` and bundle them alongside the 17 stocks. Pipeline doesn't exist yet.
- User-uploaded voices: deliberately NOT pursued. See "What we're not doing" below.

## File formats the server accepts

- `.pt` — pre-encoded Mimi tensor + KV cache. Saves ~1s of cold-start CPU because Mimi encoding is already done. Use for any voice we ship in the container image.
- `.wav` — raw audio. Server runs `load_audio` + `normalize_audio` (`-24 LUFS`) + Mimi encode on every request. Use during experimentation / one-off testing; convert to `.pt` for production.

`url.py:52` decides extension; default is `.pt`.

## Sample requirements

| Property | Recommended | Why |
|---|---|---|
| Duration | 10–30 seconds | <5s under-conditions timbre; >30s wastes KV cache without quality gain. No hard cap in code. |
| Speakers | One | Two voices in the sample blend in the output. Strip dialog, interviews, music beds. |
| Background | Quiet, no music, no reverb | Normalization levels loudness, not noise. Noise carries into the cloned voice. |
| Sample rate | 24 kHz mono ideal | Mimi's native rate. Other rates resampled, slight quality loss. |
| Format | WAV / FLAC / MP3 | Anything `soundfile` / `torchaudio` can decode via `load_audio`. |
| Content | Natural conversational speech | Reading lists / robotic narration produces flat clones. |

## How to extract a voice sample from existing audio

These tools are commonly used; we don't yet ship any pipeline that uses them. Documenting for when we curate licensed samples.

- yt-dlp: `yt-dlp -x --audio-format wav <URL>` extracts audio. Don't use this for copyrighted content without a license.
- ffmpeg: `ffmpeg -i in.mp3 -ar 24000 -ac 1 -ss 30 -t 20 out.wav` = "take input.mp3, resample to 24kHz, downmix to mono, start at 30s, take 20s, write WAV."
- Demucs: `demucs --two-stems vocals input.wav` → isolates voice. Useful when audio has background music.
- pyannote: speaker diarization + voice activity detection. Useful for extracting one speaker's segments from a podcast interview.

## What we're not doing (and why)

- User-uploaded / user-recorded voice prompts: deliberately deprioritized. Users came to Palkie Talkie to practice speaking with a fluent native partner, not to hear themselves played back. Non-native learners specifically don't want their own (often non-native) voice as the tutor. Random users uploading their own voice has no clear product motivation — we don't ship a feature without one. If a future use case appears (family mode? celebrity-fan personas? voice-twins?) with a real reason for the user to invest 20 seconds of recording, revisit then. Until that motivation exists, this feature is dead weight.
- Cloning real people without consent: illegal in EU (AI Act), CA, NY, TN, and growing. Even if technically trivial — pulling 20s off any podcast — we will not ship a feature that does this. Curated voices must come with explicit license from the speaker.
