"""Live integration test + recorded experiment: the tutor speaking-speed control.

Unconditionally skipped. To run, comment out the `pytest.mark.skip` in `pytestmark` below, then with real OpenAI creds:

    set -a; source .env; set +a
    uv run pytest app/services/openai/test_manual_openai_speed.py -s

It opens a real OpenAI Realtime WebSocket exactly like iOS does (Bearer ephemeral token from `mint_openai_session`), forces the persona to read a fixed passage, and measures OUTPUT AUDIO DURATION (PCM16 @ 24kHz → seconds). Words-per-minute = transcript words / minutes, robust even if the model paraphrases. `-s` prints the WPM per level so a human can eyeball the real pace.

EXPERIMENT ON RECORD (why speed is audio-only):
We wanted a "pre-processing" lever, the model GENERATING at a target pace from a prompt hint, so we wouldn't depend on the post-hoc `audio.output.speed` time-stretch (which warps the waveform and sounds artificial at the edges). It does not work. With playback pinned at 1.0 and ONLY the prompt varied between "speak at ~90 wpm" and "speak at ~210 wpm", the model produced ~the same pace both times (measured 216 vs 206 wpm, within noise): it ignores pace instructions and reverts to its native ~210 wpm. So `audio.output.speed` carries the entire effect, and we do NOT inject any pace text into the prompt (see assemble_prompt). The two tests below lock both facts in:
- the audio knob orders speed slow→fast (the working lever, a regression guard), and
- a prompt pace instruction is ignored (the finding; this test failing would mean OpenAI changed the behavior and a prompt lever is worth revisiting)."""

import asyncio
import base64
import json
import uuid
from datetime import UTC, datetime

import pytest
import websockets

from app.profile.tutor_speaking_speed import TutorSpeakingSpeed
from app.routers.conversation.assemble_prompt import PersonaPromptFields, assemble_prompt
from app.services.neon.rows import UserRow
from app.services.openai.constants import OpenAIVoiceId
from app.services.openai.mint_openai_session import mint_openai_session

# Manual only: a real OpenAI Realtime call costs money and is too slow/flaky for any automated run, so it's unconditionally skipped (CI, pre-push, everywhere). To run it, comment out the skip below.
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skip(reason="manual only: real OpenAI Realtime call; comment out this skip to run"),
]

_SAMPLE_RATE = 24000  # PCM16 mono, per mint_openai_session's audio.output.format
_PASSAGE = (
    "Let me tell you about my morning. I woke up early, made a strong cup of coffee, "
    "and went for a long walk around the neighborhood before sitting down to start my work."
)
_PERSONA = PersonaPromptFields(
    name="Tutor",
    role="a warm, encouraging English conversation tutor",
    age=None,
    background=None,
    vocabulary_register=None,
    conversational_style=None,
    topical_preferences=None,
)


def _make_user() -> UserRow:
    now = datetime.now(UTC)
    return UserRow(
        id=uuid.uuid4(),
        clerk_user_id="user_speedtest",
        email="speedtest@palkietalkie.test",
        premium=False,
        premium_ends_at=None,
        created_at=now,
        updated_at=now,
        preferred_name="Ayumi",
        name_pronunciation=None,
        native_languages=["Japanese"],
        target_language="English",
        target_accents=[],
        proficiency="intermediate",
        tutor_speaking_speed="normal",
        goals=None,
        location_city="San Francisco",
        timezone="America/Los_Angeles",
        personalization_consent=None,
        product_improvement_consent=None,
        consent_screen_seen_at=None,
        deleted_at=None,
    )


async def _measure_wpm(audio_speed: TutorSpeakingSpeed, extra_instruction: str = "") -> float:
    """Heard words-per-minute when audio.output.speed is set for `audio_speed` and `extra_instruction` (e.g. a pace request) is appended to the prompt. Splitting the two lets a test pin the audio knob and probe the prompt in isolation."""
    prompt = assemble_prompt(
        _PERSONA, _make_user(), kg_entities=[], weather_label=None, today_events_titles=[]
    )
    if extra_instruction:
        prompt = f"{prompt}\n\n{extra_instruction}"
    session = await mint_openai_session(prompt, OpenAIVoiceId.ALLOY, speaking_speed=audio_speed)

    audio_bytes = 0
    transcript = ""
    async with websockets.connect(
        session.ws_url,
        additional_headers={"Authorization": f"Bearer {session.ephemeral_token}"},
        max_size=None,
    ) as ws:

        async def _drive() -> None:
            nonlocal audio_bytes, transcript
            async for raw in ws:
                evt = json.loads(raw)
                kind = evt.get("type", "")
                if kind == "session.created":
                    await ws.send(
                        json.dumps(
                            {
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_text",
                                            "text": f"Read this aloud word for word, then stop: {_PASSAGE}",
                                        }
                                    ],
                                },
                            }
                        )
                    )
                    await ws.send(json.dumps({"type": "response.create"}))
                elif kind in ("response.output_audio.delta", "response.audio.delta"):
                    audio_bytes += len(base64.b64decode(evt["delta"]))
                elif kind in (
                    "response.output_audio_transcript.delta",
                    "response.audio_transcript.delta",
                ):
                    transcript += evt.get("delta", "")
                elif kind == "response.done":
                    return
                elif kind == "error":
                    raise AssertionError(f"OpenAI realtime error: {evt}")

        await asyncio.wait_for(_drive(), timeout=90)

    seconds = audio_bytes / 2 / _SAMPLE_RATE
    words = len(transcript.split())
    assert seconds > 0 and words > 0, (
        f"no audio/transcript captured (audio={seconds}s words={words})"
    )
    wpm = words / (seconds / 60)
    print(
        f"[speed] audio={audio_speed} extra={extra_instruction!r}: {wpm:.0f} wpm ({words} words / {seconds:.1f}s)"
    )
    return wpm


async def test_audio_speed_knob_orders_speech_slow_to_fast() -> None:
    # The working lever: audio.output.speed. Heard pace must increase very_slow → normal → very_fast.
    slow = await _measure_wpm("very_slow")
    normal = await _measure_wpm("normal")
    fast = await _measure_wpm("very_fast")
    assert slow < normal < fast, (
        f"speeds not ordered: slow={slow:.0f} normal={normal:.0f} fast={fast:.0f}"
    )


async def test_prompt_pace_instruction_is_ignored_by_the_model() -> None:
    # The recorded finding: with the audio knob pinned at 1.0, an explicit "speak at ~90 wpm" vs "speak at ~210 wpm" prompt produces ~the same pace, the model ignores it. If this ever FAILS (the two diverge), OpenAI changed the behavior and a prompt-based pace lever is worth revisiting.
    slow = await _measure_wpm(
        "normal",
        "Speak very slowly, at roughly 90 words per minute, with clear pauses between phrases.",
    )
    fast = await _measure_wpm(
        "normal",
        "Speak quickly, at roughly 210 words per minute, the fast pace of natives chatting.",
    )
    assert abs(slow - fast) < 30, (
        f"prompt pace instruction unexpectedly DID move the model: ~90wpm prompt={slow:.0f} vs "
        f"~210wpm prompt={fast:.0f} wpm. If reliable, a prompt pace lever is now viable, revisit."
    )
