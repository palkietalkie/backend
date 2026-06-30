from scripts.asc.fetch_testflight_feedback import Submission, build_version_of, summarize_crash_log

_CRASH_LOG = """Incident Identifier: AC10DEBB
Exception Type:  EXC_CRASH (SIGABRT)
Termination Reason: SIGNAL 6 Abort trap: 6
Triggered by Thread:  2

Last Exception Backtrace:
3   AVFAudio      0x1bd3da2f4 AVAudioEngineGraph::_Connect(...) + 332 (AVAudioEngineGraph.mm:2161)
6   PalkieTalkie  0x100e79cac RealInputNode.setVoiceProcessingEnabled(_:) + 64 (AudioEngineProtocol.swift:99)
8   PalkieTalkie  0x100e7d858 AudioStreamer.start() + 1276 (AudioStreamer.swift:125)
"""


def test_summarize_pulls_exception_and_app_frames() -> None:
    lines = summarize_crash_log(_CRASH_LOG)
    assert any(line.startswith("Exception Type:") for line in lines)
    assert any(line.startswith("Termination Reason:") for line in lines)
    assert any("AudioEngineProtocol.swift:99" in line for line in lines)
    # AVFAudio frame is NOT ours (no PalkieTalkie) so it must be dropped from the app-frame summary.
    assert not any("AVAudioEngineGraph.mm" in line for line in lines)


def test_summarize_caps_app_frames_at_four() -> None:
    log = "\n".join(
        f"{i}   PalkieTalkie  0x{i} Foo.bar{i}() + 4 (Foo.swift:{i})" for i in range(10)
    )
    frames = [line for line in summarize_crash_log(log) if ".swift:" in line]
    assert len(frames) <= 4


def test_summarize_empty_log_is_empty() -> None:
    assert summarize_crash_log("") == []


def test_build_version_of_maps_build_id_to_version() -> None:
    submission = Submission.model_validate(
        {"id": "x", "relationships": {"build": {"data": {"id": "b1"}}}}
    )
    assert build_version_of(submission, {"b1": "28"}) == "28"


def test_build_version_of_unknown_build_is_question_mark() -> None:
    assert build_version_of(Submission.model_validate({"id": "y"}), {}) == "?"
