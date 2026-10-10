"""EP010's 22-second original sound design and real Gemini/Groq speech cues.

No Blender or render side effects. Optional NumPy audio dependencies are declared
in requirements-cloud.txt; credential values never enter cache metadata or logs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys
import time

from ep009_audio import (catalog_gender_evidence, file_hash, fit_line, mouth_shape,
                         normalized_words, read_wav, speech_signature, write_wav)
from speech_api import (KeyPool, SpeechAPIError, gemini_models, gemini_tts,
                        groq_transcribe, load_key_pools)

ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "02_EPISODES/EP010_Binge_Watching"
FPS, SR, DURATION = 24, 48000, 22
FRAME_END = FPS * DURATION
SILENCE_START = 21.5
LINES = [
    {"id": "L01", "speaker": "peter", "start": 0, "end": 2,
     "text": "Just one episode before bed.",
     "style": "Relaxed, lightly amused and confident. Natural conversational delivery with a small smile, finish in under two seconds."},
    {"id": "L02", "speaker": "inner", "start": 2, "end": 4,
     "text": "You said that yesterday.",
     "style": "Same person's inner thought, playful dry teasing, one eyebrow raised. No character impersonation. Under two seconds."},
    {"id": "L03", "speaker": "peter", "start": 4, "end": 6,
     "text": "Tonight, I'm being responsible.",
     "style": "Cheerful self-assurance with a tiny pause after Tonight. Brisk and conversational, under two seconds."},
    {"id": "L04", "speaker": "announcer", "voice": "Puck", "start": 6, "end": 8,
     "text": "Next episode starts in five seconds.",
     "style": "Polished neutral streaming app announcement. Clean, brisk and evenly paced; finish clearly in under two seconds."},
    {"id": "L05", "speaker": "peter", "start": 8, "end": 10,
     "text": "Okay, this is the last one.",
     "style": "Tired conversational reassurance, a slightly guilty little smile. Quick and clear, under two seconds."},
    {"id": "L06", "speaker": "inner", "start": 10, "end": 12,
     "text": "You have work in four hours.",
     "style": "Same person's inner thought, dry incredulous warning. Keep the same natural voice identity. Brisk, under two seconds."},
    {"id": "L07", "speaker": "peter", "start": 12, "end": 15,
     "text": "I NEED TO KNOW WHAT HAPPENS!",
     "style": "Comically desperate emphatic outburst, incredulous stress on NEED and HAPPENS. Intelligible, no extra cries, under three seconds."},
    {"id": "L08", "speaker": "peter", "start": 15, "end": 18,
     "text": "Wait… why are the birds singing?",
     "style": "Sleep-deprived confusion, tiny beat after Wait, quiet but clearly intelligible. Natural tired delivery, under three seconds."},
    {"id": "L09", "speaker": "peter", "start": 18, "end": 20,
     "text": "I have work in thirty minutes.",
     "style": "Exhausted flat deadpan, stunned realization with almost no energy. Keep words clear and brisk, under two seconds."},
    {"id": "L10", "speaker": "peter", "start": 20, "end": SILENCE_START,
     "text": "Worth it.",
     "style": "Very dry exhausted little smile, resigned yet satisfied. Two clear words, under one second; no added sigh or words."},
]
DOCS = {
    "gemini_tts": "https://ai.google.dev/gemini-api/docs/speech-generation",
    "gemini_free_tier": "https://ai.google.dev/gemini-api/docs/pricing",
    "gemini_voice_gender": "https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#voice_options",
    "groq_whisper": "https://console.groq.com/docs/speech-to-text",
    "groq_rate_limits": "https://console.groq.com/docs/rate-limits",
}


def configured_lines(defaults):
    """Thoughts and ordinary dialogue both belong to the locked Peter identity."""
    identity = defaults.get("tts_character_voices", {}).get("Peter")
    if not isinstance(identity, dict) or not identity.get("voice"):
        raise SpeechAPIError("Configure Peter's permanent voice before generation")
    if identity.get("provider") != "Gemini" or identity.get("gender", "").lower() != "male" \
            or identity.get("locked") is not True or identity.get("allow_voice_fallback") is not False:
        raise SpeechAPIError("Peter requires his locked male Gemini voice with no fallback")
    result = []
    for original in LINES:
        spec = dict(original)
        if spec["speaker"] in ("peter", "inner"):
            spec.update(voice=identity["voice"], character="Peter")
            spec["style"] = identity["profile"] + ". " + spec["style"]
        result.append(spec)
    return result, identity


def authoritative_words(expected, response, offset, duration):
    """Validate real ASR words, restore exact script punctuation, record clamping."""
    script, detected = expected.split(), response.get("words", [])
    got = [re.sub(r"[^a-z0-9]", "", item["word"].lower()) for item in detected]
    if got != normalized_words(expected):
        raise ValueError("Actual ASR words differ from the scripted dialogue; review or regenerate the line")
    result, previous = [], 0.0
    for word, measured in zip(script, detected):
        start, end = float(measured["start"]), float(measured["end"])
        if start < previous - .03 or end < start or start > duration + .04:
            raise ValueError("ASR word timestamps are invalid")
        start = min(duration, max(0, start))
        end = min(duration, max(start + 1 / FPS, end))
        previous = start
        result.append({"word": word, "start": round(offset + start, 5), "end": round(offset + end, 5),
                       "start_frame": min(FRAME_END, int(round((offset + start) * FPS)) + 1),
                       "end_frame": min(FRAME_END, int(math.ceil((offset + end) * FPS))),
                       "end_clamped_to_audio": float(measured["end"]) > duration})
    return result


def make_mouth_frames(dialogue, lines):
    import numpy as np
    rows = []
    for frame in range(1, FRAME_END + 1):
        t = (frame - 1) / FPS
        a, b = int(t * SR), min(len(dialogue), int((t + 1 / FPS) * SR))
        rms = float(np.sqrt(np.mean(dialogue[a:b] ** 2))) if b > a else 0
        line = next((line for line in lines if line["start"] <= t < line["end"]), None)
        word = next((w for w in line["words"] if w["start"] <= t < w["end"]), None) if line else None
        shape = "rest"
        if word and rms > .011:
            shape = mouth_shape(word["word"], (t - word["start"]) / max(1 / FPS, word["end"] - word["start"]))
        rows.append({"frame": frame, "time": round(t, 5), "speaker": line["speaker"] if line else None,
                     "shape": shape, "openness": round(min(1, rms / .13) if shape != "rest" else 0, 4),
                     "rms": round(rms, 5)})
    return rows


def original_music_sfx():
    """Sparse original audio: cozy motif -> compulsive ticks -> morning silence."""
    import numpy as np
    rng = np.random.default_rng(101010)
    length = DURATION * SR
    music, sfx = np.zeros((length, 2)), np.zeros((length, 2))
    events = []

    def add(at, data, gain=1, pan=0, name="sfx", destination=sfx):
        at = round(at * FPS) / FPS
        start, stop = int(at * SR), min(length, int(at * SR) + len(data))
        data = data[:stop - start] * gain
        destination[start:stop, 0] += data * math.sqrt((1 - pan) / 2)
        destination[start:stop, 1] += data * math.sqrt((1 + pan) / 2)
        if destination is sfx:
            events.append({"name": name, "seconds": at, "frame": int(round(at * FPS)) + 1,
                           "duration_seconds": round(len(data) / SR, 5), "original_synthesis": True})

    def pluck(freq, seconds=.5, decay=8):
        t = np.arange(int(seconds * SR)) / SR
        return (np.sin(2 * np.pi * freq * t) + .18 * np.sin(4 * np.pi * freq * t)) \
            * np.exp(-decay * t) * np.minimum(1, t / .006)

    def dry_click(seconds=.03):
        t = np.arange(int(seconds * SR)) / SR
        return rng.normal(0, .65, len(t)) * np.exp(-t * 155) * np.minimum(1, t / .001)

    # An original, quiet two-note major-sixth motif instead of a busy beat track.
    for at, notes in ((.5, (261.63, 440)), (2, (220, 369.99)), (3.5, (196, 329.63)), (5, (220, 392))):
        add(at, pluck(notes[0], .8, 5), .024, -.35, destination=music)
        add(at + .25, pluck(notes[1], .65, 6), .019, .3, destination=music)
        add(at, pluck(notes[0] / 2, .35, 10), .012, 0, destination=music)
    # A sparse ostinato nudges the spiral without covering the character's acting.
    at, step = 6.5, .65
    n = 0
    while at < 14.7:
        add(at, pluck((220, 233.08, 293.66, 233.08)[n % 4], .24, 15), .019, (-.15 if n % 2 else .15), destination=music)
        at += step
        step = max(.22, step * .945)
        n += 1
    fade = int(.12 * SR)
    music[int(14.88 * SR):int(15 * SR)] *= np.linspace(1, 0, fade)[:, None]
    music[int(15 * SR):] = 0
    add(3.958333, dry_click(), .06, .15, "remote_click")
    add(5.791667, pluck(659.25, .2, 16) + pluck(987.77, .2, 19), .043, -.2, "original_streaming_chime")
    for at in (6.208333, 6.958333, 7.708333):
        add(at, pluck(1280, .028, 120), .036, -.2, "countdown_tick")
    add(7.916667, dry_click(), .072, .15, "remote_next_episode_click")
    for at in (9.25, 10.125, 10.833333, 11.416667, 11.916667, 12.333333, 12.708333, 13.041667, 13.333333, 13.583333, 13.791667, 14, 14.166667, 14.333333):
        add(at, dry_click(.025) + pluck(760, .025, 125) * .24, .048, -.15, "accelerating_clock_tick")
    # A tiny rising pluck sells the cliffhanger; the shout carries the punch.
    add(11.958333, pluck(293.66, .28, 11) + pluck(311.13, .28, 11), .05, 0, "tiny_cliffhanger_tension")
    for at, base in ((15.041667, 1900), (15.416667, 2450), (16.083333, 2100), (17.333333, 2600)):
        t = np.arange(int(.18 * SR)) / SR
        phase = 2 * np.pi * (base * t + 290 * t * t / .18 + 42 * np.sin(2 * np.pi * 17 * t) / (2 * np.pi * 17))
        chirp = np.sin(phase) * np.sin(np.pi * np.linspace(0, 1, len(t))) ** 2
        add(at, chirp, .046, -.45, "original_morning_bird_chirp")
    add(21.166667, dry_click(.028), .036, .15, "final_remote_click")
    music[int(SILENCE_START * SR):] = 0
    sfx[int(SILENCE_START * SR):] = 0
    return music, sfx, events


def main():
    import numpy as np
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--model", default="gemini-3.8-flash-tts")
    parser.add_argument("--version", default="v001")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"v\d{3}", args.version):
        raise ValueError("Audio version must be v followed by three digits")
    audio_dir, edit_dir = EPISODE / "audio" / args.version, EPISODE / "edit" / args.version
    dialogue_file = audio_dir / f"EP010_Dialogue_22s_{args.version}.wav"
    mix_file = audio_dir / f"EP010_Final_Mix_22s_{args.version}.wav"
    cues_file = edit_dir / f"speech_cues_{args.version}.json"
    if mix_file.exists() or cues_file.exists():
        raise FileExistsError("Delivered audio/cues are protected; choose a new version")
    defaults = json.loads((ROOT / "config/production_defaults.json").read_text())
    lines, identity = configured_lines(defaults)
    audio_dir.mkdir(parents=True, exist_ok=True)
    edit_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    model = args.model
    evidence_path = edit_dir / f"peter_voice_catalog_{args.version}.json"
    if args.offline:
        gemini_pool = groq_pool = None
        evidence = json.loads(evidence_path.read_text())
        if evidence.get("voice") != identity["voice"] or evidence.get("gender") != "male":
            raise SpeechAPIError("Cached Peter voice evidence differs from current configuration")
    else:
        pools = load_key_pools(args.env_file)
        print("Server-side key pool counts:", {name: len(keys) for name, keys in pools.items()}, flush=True)
        gemini_pool, groq_pool = KeyPool(pools["GEMINI_API_KEYS"]), KeyPool(pools["GROQ_API_KEYS"])
        if model != "gemini-3.8-flash-tts" or model not in gemini_models(gemini_pool):
            raise SpeechAPIError("Documented free-tier Gemini 3.8 Flash TTS is unavailable; no voice/provider fallback")
        evidence = catalog_gender_evidence(gemini_pool, identity)
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
    print("Peter voice verified:", identity["voice"], "male; TTS", model, flush=True)
    dialogue = np.zeros(DURATION * SR)
    stereo_dialogue = np.zeros((DURATION * SR, 2))
    completed, generation = [], []
    for spec in lines:
        raw, fitted = audio_dir / f'{spec["id"]}_Gemini_Raw.wav', audio_dir / f'{spec["id"]}_Dialogue.wav'
        line_meta = audio_dir / f'{spec["id"]}_generation.json'
        signature = speech_signature(spec, model)
        cached = json.loads(line_meta.read_text()) if line_meta.exists() else {}
        if not (raw.is_file() and cached.get("signature") == signature and cached.get("raw_sha256") == file_hash(raw)):
            if args.offline:
                raise SpeechAPIError(f'{spec["id"]}: changed or missing actual Gemini audio')
            print("Generating", spec["id"], spec["speaker"], spec["voice"], flush=True)
            raw.write_bytes(gemini_tts(gemini_pool, spec["text"], spec["voice"], spec["style"], model))
            cached = {"signature": signature, "raw_sha256": file_hash(raw), "voice": spec["voice"], "tts_model": model}
            line_meta.write_text(json.dumps(cached, indent=2) + "\n")
        fit = fit_line(raw, fitted, spec["end"] - spec["start"])
        data, _ = read_wav(fitted)
        stt_path = audio_dir / f'{spec["id"]}_Groq_Whisper.json'
        stt = json.loads(stt_path.read_text()) if stt_path.exists() else {}
        if stt.get("input_sha256") != file_hash(fitted):
            if args.offline:
                raise SpeechAPIError(f'{spec["id"]}: changed or missing actual Groq transcript')
            print("Word-aligning", spec["id"], "whisper-large-v3", flush=True)
            stt = {"model": "whisper-large-v3", "input_sha256": file_hash(fitted),
                   "response": groq_transcribe(groq_pool, fitted, prompt=spec["text"])}
            stt_path.write_text(json.dumps(stt, indent=2) + "\n")
        words = authoritative_words(spec["text"], stt["response"], spec["start"], len(data) / SR)
        completed.append({**spec, "words": words, "audio": fitted.relative_to(ROOT).as_posix(), **fit})
        start = int(spec["start"] * SR)
        dialogue[start:start + len(data)] += data
        pan = {"inner": -.18, "announcer": .24}.get(spec["speaker"], 0)
        # Small positional distinction only; inner Peter retains his unprocessed voice.
        stereo_dialogue[start:start + len(data), 0] += data * math.sqrt(1 - pan)
        stereo_dialogue[start:start + len(data), 1] += data * math.sqrt(1 + pan)
        generation.append({"id": spec["id"], "speaker": spec["speaker"], "voice": spec["voice"],
                           "tts_model": model, "cache_signature": signature, "raw_audio_sha256": file_hash(raw),
                           "fitted_audio_sha256": file_hash(fitted), "raw_audio": raw.relative_to(ROOT).as_posix(),
                           "fitted_audio": fitted.relative_to(ROOT).as_posix(), **fit})
        print(spec["id"], "ready", len(words), "words, fit", fit["speed_factor"], flush=True)
    music, sfx, events = original_music_sfx()
    envelope = np.sqrt(np.convolve(dialogue ** 2, np.ones(480) / 480, mode="same"))
    music *= np.where(envelope[:, None] > .014, .27, 1)
    sfx *= np.where(envelope[:, None] > .014, .55, 1)
    mix = stereo_dialogue + music + sfx
    mix_gain = min(1, .89 / max(.001, float(np.max(np.abs(mix)))))
    mix *= mix_gain
    mix[int(SILENCE_START * SR):] = 0
    write_wav(dialogue_file, stereo_dialogue)
    write_wav(mix_file, mix)
    write_wav(audio_dir / f"EP010_Original_Music_SFX_22s_{args.version}.wav", music + sfx)
    mouths = make_mouth_frames(dialogue, completed)
    for line in completed:
        line["mouth_frames"] = [row for row in mouths if line["start"] <= row["time"] < line["end"]]
    audio_choices = {"music": "Original sparse warm two-note motif, then restrained accelerating ostinato; cut at dawn 15s",
                     "foley": "Small remote/chime/countdown/clock accents; original morning bird chirps",
                     "punchline": "Dry dialogue against silence; no busy sting or loud scratch obscuring the acting",
                     "prompt_audio_treated_as_reference": True, "external_audio_assets": [],
                     "original_sfx_seed": 101010, "last_half_second": "Digital silence"}
    cues = {"schema_version": 1, "episode": "EP010_Binge_Watching", "duration_seconds": DURATION,
            "fps": FPS, "frame_start": 1, "frame_end": FRAME_END, "sample_rate": SR, "channels": 2,
            "tts_provider": "Gemini", "tts_model": model, "stt_provider": "Groq", "stt_model": "whisper-large-v3",
            "audio_version": args.version, "character_voices": {"Peter": identity},
            "peter_voice": {**identity, "catalog_gender_verified": True}, "peter_voice_catalog_evidence": evidence,
            "speech_audio_evidence": generation, "timing_source": "Actual fitted speech transcribed by Groq Whisper with word timestamps",
            "lip_sync_method": "Measured 24fps RMS and word-based heuristic vowel/consonant visemes; not phoneme forced alignment",
            "viseme_shapes": ["rest", "A", "E", "O", "MBP", "FV"], "lines": completed,
            "words": [{**w, "speaker": line["speaker"], "line_id": line["id"]} for line in completed for w in line["words"]],
            "mouth_frames": mouths, "sfx": events, "audio_choices": audio_choices,
            "dialogue_file": dialogue_file.relative_to(ROOT).as_posix(), "mix_file": mix_file.relative_to(ROOT).as_posix(),
            "documentation": DOCS}
    cues_file.write_text(json.dumps(cues, indent=2) + "\n")
    metadata = {"tts_model": model, "stt_model": "whisper-large-v3", "lines": generation,
                "sample_rate": SR, "channels": 2, "duration_seconds": DURATION,
                "mix_peak_dbfs": round(20 * math.log10(float(np.max(np.abs(mix)))), 3), "mix_gain": mix_gain,
                "elapsed_seconds": round(time.monotonic() - started, 3), "audio_version": args.version,
                "character_voices": {"Peter": identity}, "voice_catalog_evidence": evidence,
                "final_half_second_silent": bool(np.max(np.abs(mix[int(SILENCE_START * SR):])) == 0),
                "documentation_checked_at": datetime.now(timezone.utc).isoformat(),
                "free_tier_documentation_checked": "Gemini 3.8 Flash TTS standard pricing lists input/output free of charge; actual account quota still applies",
                "audio_choices": audio_choices, "docs": DOCS, "listening_review_performed": False}
    (audio_dir / f"speech_generation_{args.version}.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("Complete:", mix_file.relative_to(ROOT), "22s / 528 frames / 48kHz stereo", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (SpeechAPIError, FileExistsError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
