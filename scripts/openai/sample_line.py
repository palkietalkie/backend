def sample_line(voice: str) -> str:
    """Short greeting that includes the voice's display name.

    Length is deliberately short — TTS render time is roughly linear in character count, and the user pays this latency on every voice-picker tap once the WAV is bundled. Including the voice name in the sentence lets the listener tie the audio back to the row they tapped.
    """
    return f"Hi, I'm {voice.capitalize()}. Let's practice some English together."
