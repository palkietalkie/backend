-- Symmetric naming for the two audio tracks now that we capture both: the iOS mic recording and the AI's raw PCM16 output. Was `audio / bytes / format` (implying "the" audio) + `model_audio*`. Becomes `mic_audio* / model_audio*` so neither track is privileged.

ALTER TABLE session_audio RENAME COLUMN audio  TO mic_audio;
ALTER TABLE session_audio RENAME COLUMN bytes  TO mic_audio_bytes;
ALTER TABLE session_audio RENAME COLUMN format TO mic_audio_format;
