"""End-to-end probe of the Modal voice WebSocket.

Bypasses iOS entirely. Mints a real HMAC ticket (same secret as Fly + Modal), opens the same `/api/chat` WebSocket iOS would, sends valid Ogg-Opus packets encoded with `opuslib`, and asserts we receive a handshake byte + at least one audio/text frame from the model within a timeout.

If this passes, the iOS Ogg-Opus framing is the bug. If this fails, the Modal server pipeline is the bug.

Run: cd backend source .venv/bin/activate python scripts/probe_modal_voice.py"""

from __future__ import annotations

import asyncio
import os
import struct
import sys
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
import opuslib
import websockets

# Reuse the canonical HMAC ticket logic — same `mint()` Fly uses, single source of truth in `app.services.ws_ticket`. The probe reads `WS_TICKET_SECRET` from backend/.env so it signs with the exact same secret Modal verifies against.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for line in (Path(__file__).resolve().parents[1] / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from app.services.ws_ticket import mint  # noqa: E402

SAMPLE_RATE = 24000
CHANNELS = 1
FRAME_SAMPLES = 480  # 20ms @ 24kHz

MODAL_WS_BASE = "wss://palkietalkie-dev--api.modal.run"

# Same defaults the iOS-side handshake uses (from app/services/personaplex/sampling.py).
SAMPLING_DEFAULTS = {
    "text_temperature": "0.8",
    "text_topk": "25",
    "audio_temperature": "0.8",
    "audio_topk": "250",
    "pad_mult": "1",
    "text_seed": "42",
    "audio_seed": "42",
    "repetition_penalty_context": "64",
    "repetition_penalty": "1.0",
}


def build_ws_url() -> str:
    params = {
        "text_prompt": "You are a friendly conversation partner. Open the conversation in character.",
        "voice_prompt": "NATM1.pt",
        "auth_token": mint("probe-user"),
        **SAMPLING_DEFAULTS,
    }
    return f"{MODAL_WS_BASE}/api/chat?{urlencode(params, safe='')}"


# --- Ogg-Opus framing (mirror of iOS OggOpusWriter.swift) ---

OGG_CRC_POLY = 0x04C1_1DB7


def build_ogg_crc_table() -> list[int]:
    table = []
    for index in range(256):
        register = index << 24
        for _bit in range(8):
            register = (
                ((register << 1) ^ OGG_CRC_POLY) if (register & 0x8000_0000) else (register << 1)
            )
        table.append(register & 0xFFFF_FFFF)
    return table


OGG_CRC_TABLE = build_ogg_crc_table()


def ogg_crc32(data: bytes) -> int:
    crc = 0
    for b in data:
        idx = ((crc >> 24) ^ b) & 0xFF
        crc = ((crc << 8) ^ OGG_CRC_TABLE[idx]) & 0xFFFF_FFFF
    return crc


def make_page(packet: bytes, header_type: int, granule: int, serial: int, seq: int) -> bytes:
    seg = []
    if len(packet) == 0:
        seg.append(0)
    else:
        r = len(packet)
        while r > 0:
            take = min(r, 255)
            seg.append(take)
            r -= take
            if take < 255:
                break
        if len(packet) % 255 == 0:
            seg.append(0)
    page = bytearray()
    page += b"OggS"
    page.append(0)
    page.append(header_type)
    page += struct.pack("<Q", granule)
    page += struct.pack("<I", serial)
    page += struct.pack("<I", seq)
    page += struct.pack("<I", 0)
    page.append(len(seg))
    page += bytes(seg)
    page += packet
    crc = ogg_crc32(bytes(page))
    page[22:26] = struct.pack("<I", crc)
    return bytes(page)


def opus_head() -> bytes:
    p = bytearray()
    p += b"OpusHead"
    p.append(1)
    p.append(CHANNELS)
    p += struct.pack("<H", 0)
    p += struct.pack("<I", SAMPLE_RATE)
    p += struct.pack("<h", 0)
    p.append(0)
    return bytes(p)


def opus_tags() -> bytes:
    vendor = b"PalkieTalkie-probe"
    p = bytearray()
    p += b"OpusTags"
    p += struct.pack("<I", len(vendor))
    p += vendor
    p += struct.pack("<I", 0)
    return bytes(p)


async def main() -> int:
    url = build_ws_url()
    print(f"[probe] connecting to {url[:120]}...")
    try:
        async with websockets.connect(
            url, max_size=None, open_timeout=120, ping_interval=None
        ) as ws:
            print("[probe] WS open, waiting for server handshake byte (\\x00)...")

            # CRITICAL: do NOT send audio before receiving the server's handshake byte. The server's recv_loop only starts after `step_system_prompts_async` (~30s on cold start). If we send audio earlier, the bytes either get buffered (and the recv_loop misses the OpusHead headers when it finally starts) or get dropped by Modal's WS proxy. Either way sphn dies decoding mid-stream audio with no preceding header pages.
            hs = await asyncio.wait_for(ws.recv(), timeout=120)
            if not isinstance(hs, (bytes, bytearray)) or len(hs) == 0 or hs[0] != 0x00:
                print(f"[probe] unexpected first server frame: {hs!r}")
                return 4
            print(f"[probe] server handshake received ({len(hs)}B). Starting audio.")

            # Encoder + framer state.
            enc = opuslib.Encoder(SAMPLE_RATE, CHANNELS, opuslib.APPLICATION_VOIP)
            serial = 0xC0FFEE
            seq = 0
            granule = 0

            # Audio header pages.
            header_bytes = make_page(
                opus_head(), header_type=0x02, granule=0, serial=serial, seq=seq
            )
            seq += 1
            header_bytes += make_page(
                opus_tags(), header_type=0x00, granule=0, serial=serial, seq=seq
            )
            seq += 1

            # First send: 0x01 (audio tag) + headers + one silent audio page.
            silent_pcm_bytes = np.zeros(FRAME_SAMPLES, dtype=np.int16).tobytes()
            first_opus = enc.encode(silent_pcm_bytes, FRAME_SAMPLES)
            granule += FRAME_SAMPLES
            audio_page = make_page(
                first_opus, header_type=0x00, granule=granule, serial=serial, seq=seq
            )
            seq += 1
            first_payload = b"\x01" + header_bytes + audio_page
            await ws.send(first_payload)
            print(f"[probe] sent first frame: {len(first_payload)}B")

            # Send 30s of silence (50 frames/sec), then expect SOMETHING from server.
            first_inbound: bytes | None = None
            inbound_count = 0
            send_task_done = False

            async def send_silence() -> None:
                nonlocal seq, granule, send_task_done
                for _ in range(50 * 30):
                    pcm_bytes = np.zeros(FRAME_SAMPLES, dtype=np.int16).tobytes()
                    pkt = enc.encode(pcm_bytes, FRAME_SAMPLES)
                    granule += FRAME_SAMPLES
                    pg = make_page(pkt, header_type=0x00, granule=granule, serial=serial, seq=seq)
                    seq += 1
                    try:
                        await ws.send(b"\x01" + pg)
                    except Exception as e:
                        print(f"[probe] send failed at seq={seq}: {e}")
                        send_task_done = True
                        return
                    await asyncio.sleep(0.02)
                send_task_done = True

            # Post-handshake inbound frames: model output audio (kind=0x01) + transcript text (kind=0x02).
            async def recv_loop() -> None:
                nonlocal first_inbound, inbound_count
                try:
                    while True:
                        msg = await asyncio.wait_for(ws.recv(), timeout=30)
                        if isinstance(msg, (bytes, bytearray)):
                            inbound_count += 1
                            if first_inbound is None:
                                first_inbound = bytes(msg)
                                print(
                                    f"[probe] first model frame: {len(msg)}B, kind=0x{msg[0]:02x}, hex[:24]={msg[:24].hex()}"
                                )
                            elif inbound_count <= 5 or inbound_count % 25 == 0:
                                kind = msg[0]
                                label = (
                                    "audio"
                                    if kind == 1
                                    else "text"
                                    if kind == 2
                                    else f"kind=0x{kind:02x}"
                                )
                                print(f"[probe] inbound #{inbound_count}: {len(msg)}B {label}")
                except TimeoutError:
                    print(f"[probe] recv timeout — got {inbound_count} inbound frames total")
                except websockets.ConnectionClosed as e:
                    print(f"[probe] WS closed by server: code={e.code} reason={e.reason!r}")

            await asyncio.gather(send_silence(), recv_loop())

            print(
                f"[probe] DONE. inbound frames: {inbound_count}, first_inbound: {first_inbound[:24].hex() if first_inbound else None}"
            )
            return 0 if inbound_count > 0 else 1

    except websockets.InvalidStatusCode as e:
        print(f"[probe] WS handshake rejected: status={e.status_code}")
        return 2
    except Exception as e:
        print(f"[probe] error: {type(e).__name__}: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
