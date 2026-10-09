"""Build EP009's original 18-second mix and Gemini/Groq speech cue sheet.

Run with the optional audio dependencies in requirements-cloud.txt. Requests are
cached per line; never stores or prints credentials. No Blender/render side effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import wave

from production_paths import RuntimePaths
from speech_api import KeyPool, SpeechAPIError, gemini_models, gemini_tts, groq_transcribe, load_key_pools, request_json

ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "02_EPISODES/EP009_Wrong_Screen"
FPS, SR, DURATION = 24, 48000, 18
LINES = [
    {"id": "L01", "speaker": "employee", "start": 0, "end": 2,
     "text": "Okay, everyone. Let me share my screen.",
     "style": "Conversational and upbeat, confident smile. Crisp, brisk delivery. Complete the sentence in under two seconds."},
    {"id": "L02", "speaker": "host", "voice": "Puck", "start": 2, "end": 4,
     "text": "Yep, we can see it!", "style": "Friendly professional meeting host, bright and completely unaware. Crisp delivery, under two seconds."},
    {"id": "L03", "speaker": "employee", "start": 4, "end": 6,
     "text": "Perfect. Very professional.", "style": "Confident conversational office worker, smug little smile, a tiny pause after Perfect. Under two seconds."},
    {"id": "L04", "speaker": "employee", "start": 6, "end": 8,
     "text": "Wait. That's not the presentation.", "style": "Sudden worried realization. Tiny pause after Wait. Crisp and quickly panicked, under two seconds."},
    {"id": "L05", "speaker": "host", "voice": "Puck", "start": 8, "end": 10,
     "text": "Interesting search history.", "style": "Friendly professional host, innocently curious and deadpan, a tiny pause after Interesting. Under two seconds."},
    {"id": "L06", "speaker": "employee", "start": 10, "end": 13,
     "text": "WHY IS THE WHOLE DESKTOP SHARING?!", "style": "Comically panicked emphatic shout, crisp intelligible words, incredulous stress on whole desktop. Complete in under three seconds."},
    {"id": "L07", "speaker": "employee", "start": 13, "end": 15,
     "text": "I'm changing careers.", "style": "Defeated and embarrassed whisper, dry comic resignation. Intelligible quiet voice. Under two seconds."},
]
DOCS = {
    "gemini_tts": "https://ai.google.dev/gemini-api/docs/speech-generation",
    "gemini_free_tier": "https://ai.google.dev/gemini-api/docs/pricing",
    "groq_whisper": "https://console.groq.com/docs/speech-to-text",
    "groq_rate_limits": "https://console.groq.com/docs/rate-limits",
    "gemini_voice_catalog": "https://ai.google.dev/api/voices",
    "gemini_voice_gender": "https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#voice_options",
}


def configured_lines(defaults):
    """Peter's fixed voice is production configuration, never an episode guess."""
    identity = defaults.get("tts_character_voices", {}).get("Peter")
    if not isinstance(identity, dict) or not identity.get("voice"):
        raise SpeechAPIError("Configure the permanent Peter voice in tts_character_voices.Peter")
    if identity.get("gender", "").lower() != "male" or identity.get("locked") is not True:
        raise SpeechAPIError("Peter must have an explicitly locked male voice identity")
    if identity.get("provider") != "Gemini" or identity.get("allow_voice_fallback") is not False:
        raise SpeechAPIError("Peter's permanent identity requires Gemini and no voice fallback")
    result = []
    for original in LINES:
        spec = dict(original)
        if spec["speaker"] == "employee":
            spec["voice"] = identity["voice"]
            spec["character"] = "Peter"
        result.append(spec)
    return result, identity


def speech_signature(spec, model):
    identity = {name: spec[name] for name in ("voice", "style", "text")}
    identity["model"] = model
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def reuse_host_cache(audio_dir, spec, model):
    """Copy only a verified unchanged Puck line into the new version directory."""
    if spec["speaker"] != "host":
        return False
    old_cues = json.loads((EPISODE / "edit/speech_cues_v001.json").read_text())
    old = next((line for line in old_cues["lines"] if line["id"] == spec["id"]), None)
    if not old or old_cues.get("tts_model") != model \
            or any(old.get(name) != spec.get(name) for name in ("voice", "style", "text")):
        return False
    source = EPISODE / "audio"
    old_meta = json.loads((source / f'{spec["id"]}_generation.json').read_text())
    raw = source / f'{spec["id"]}_Gemini_Raw.wav'
    if old_meta.get("raw_sha256") != file_hash(raw):
        return False
    for suffix in ("_Gemini_Raw.wav", "_Dialogue.wav", "_Groq_Whisper.json"):
        shutil.copyfile(source / (spec["id"] + suffix), audio_dir / (spec["id"] + suffix))
    new_meta = {**old_meta, "signature": speech_signature(spec, model), "reused_from_audio_version": "v001"}
    (audio_dir / f'{spec["id"]}_generation.json').write_text(json.dumps(new_meta, indent=2) + "\n")
    return True


def catalog_gender_evidence(pool, identity):
    voice = identity["voice"]
    # The configured catalogue ID contains no secret; provider key stays in a header.
    if not re.fullmatch(r"[A-Za-z0-9_-]+", voice):
        raise SpeechAPIError("Configured voice ID is invalid")
    response = pool.call(lambda key: request_json(
        f"https://generativelanguage.googleapis.com/v1beta/voices?search={voice}&gender=male&language_code=en-US&page_size=1000",
        headers={"x-goog-api-key": key}))
    candidates = [item for item in response.get("voices", [])
                  if item.get("id", item.get("name", "").removeprefix("voices/")).casefold() == voice.casefold()]
    if not candidates or not any(item.get("gender", "").lower() == "male" for item in candidates):
        raise SpeechAPIError("Configured Peter voice not verified as male by the live Gemini catalog")
    entry = next(item for item in candidates if item.get("gender", "").lower() == "male")
    return {"voice": voice, "catalog_id": entry.get("id"), "display_name": entry.get("display_name"),
            "gender": "male", "type": entry.get("type"),
            "language_code": entry.get("language_code"), "pitch": entry.get("pitch"),
            "verified_live_catalog": True, "source": DOCS["gemini_voice_catalog"],
            "voice_gender_documentation": DOCS["gemini_voice_gender"], "credentials_stored": False}


def read_wav(path):
    import numpy as np
    with wave.open(str(path), "rb") as stream:
        if stream.getsampwidth() != 2:
            raise ValueError("Speech WAV must be PCM16")
        audio = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2").astype(float) / 32768
        return audio.reshape(-1, stream.getnchannels()).mean(axis=1), stream.getframerate()


def write_wav(path, audio, sample_rate=SR):
    import numpy as np
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    channels = 1 if audio.ndim == 1 else audio.shape[1]
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(channels)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fit_line(source, target, seconds):
    """Trim boundary silence; pitch-preserving speed fit only when necessary."""
    import numpy as np
    audio, rate = read_wav(source)
    source_rate = rate
    width = max(1, rate // 200)
    envelope = np.sqrt(np.convolve(audio * audio, np.ones(width) / width, mode="same"))
    voiced = np.flatnonzero(envelope > max(0.003, envelope.max() * 0.018))
    if not len(voiced):
        raise ValueError("Gemini speech audio is silent")
    start, stop = max(0, voiced[0] - int(rate * .025)), min(len(audio), voiced[-1] + int(rate * .065))
    audio = audio[start:stop]
    # Keep a short pause before the next speaker and prevent sentence truncation.
    allowed = seconds - .11
    speed = max(1.0, len(audio) / rate / allowed)
    if speed > 2.0:
        raise ValueError(f"Speech too long to fit naturally ({speed:.2f}x); regenerate with quicker delivery")
    if speed > 1.005 or rate != SR:
        temp = target.with_name(target.stem + "_trim.wav")
        write_wav(temp, audio, rate)
        ffmpeg = RuntimePaths.discover().resolve_tool("ffmpeg")
        result = subprocess.run([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y", "-i", str(temp),
            "-af", f"atempo={speed:.9f}", "-ar", str(SR), "-ac", "1", str(target)], capture_output=True)
        temp.unlink(missing_ok=True)
        if result.returncode:
            raise ValueError("Pitch-preserving speech fit failed")
        audio, rate = read_wav(target)
    if len(audio) > int((seconds - .06) * SR):
        raise ValueError("Fitted speech exceeds its scene slot")
    peak = max(.001, float(np.max(np.abs(audio))))
    audio *= .69 / peak
    write_wav(target, audio)
    return {"trim_start_seconds": round(start / source_rate, 5), "speed_factor": round(speed, 6),
            "fitted_duration_seconds": round(len(audio) / SR, 6)}


def normalized_words(text):
    return [re.sub(r"[^a-z0-9]", "", word.lower()) for word in text.split()]


def authoritative_words(expected, response, offset, duration):
    """Keep exact scripted punctuation while validating actual ASR word count/text."""
    script = expected.split()
    detected = response.get("words", [])
    got = [re.sub(r"[^a-z0-9]", "", item["word"].lower()) for item in detected]
    if got != normalized_words(expected):
        raise ValueError(f"ASR transcript differs from script: expected {len(script)} words, got {len(got)}; review speech before captions")
    result = []
    previous = 0.0
    for word, measured in zip(script, detected):
        start, end = float(measured["start"]), float(measured["end"])
        if start < previous - .03 or end < start or start > duration + .04:
            raise ValueError("ASR word timestamps are invalid")
        # Some Whisper function words have zero duration; keep accurate onset with one-frame caption visibility.
        start = min(duration, max(0, start))
        end = min(duration, max(start + 1 / FPS, end))
        previous = start
        result.append({"word": word, "start": round(offset + start, 5), "end": round(offset + end, 5),
                       "start_frame": min(432, int(round((offset + start) * FPS)) + 1),
                       "end_frame": min(432, int(math.ceil((offset + end) * FPS))),
                       "end_clamped_to_audio": float(measured["end"]) > duration})
    return result


def mouth_shape(word, phase):
    word = re.sub(r"[^a-z]", "", word.lower())
    if phase < .22 and word[:1] in "mbp":
        return "MBP"
    if phase < .25 and word[:1] in "fv":
        return "FV"
    vowel = next((v for v in word if v in "aeiou"), "a")
    return {"a": "A", "e": "E", "i": "E", "o": "O", "u": "O"}[vowel]


def make_mouth_frames(dialogue, lines):
    import numpy as np
    rows = []
    for frame in range(1, 433):
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
    import numpy as np
    rng = np.random.default_rng(9009)
    music, sfx = np.zeros((DURATION * SR, 2)), np.zeros((DURATION * SR, 2))
    events = []
    def add(at, wave_data, gain=1, pan=0, name="sfx"):
        start = int(at * SR)
        stop = min(DURATION * SR, start + len(wave_data))
        wave_data = wave_data[:stop - start] * gain
        sfx[start:stop, 0] += wave_data * math.sqrt((1 - pan) / 2)
        sfx[start:stop, 1] += wave_data * math.sqrt((1 + pan) / 2)
        events.append({"name": name, "seconds": at, "frame": int(round(at * FPS)) + 1})
    def tone(freq, seconds, decay=12):
        t = np.arange(int(seconds * SR)) / SR
        return np.sin(2 * np.pi * freq * t) * np.exp(-decay * t) * np.minimum(1, t / .004)
    # Original plucked chord progression at 100 BPM, intentionally quiet under dialogue.
    chords = [(261.63, 329.63, 392), (220, 261.63, 329.63), (174.61, 220, 261.63), (196, 246.94, 293.66)]
    for beat in range(22):
        at = beat * .6
        if at >= 13:
            break
        chord = chords[(beat // 4) % len(chords)]
        t = np.arange(int(.58 * SR)) / SR
        sound = sum(np.sin(2 * np.pi * f * t) + .22 * np.sin(4 * np.pi * f * t) for f in chord) / 3
        sound *= np.exp(-7 * t) * np.minimum(1, t / .01) * .034
        start = int(at * SR)
        music[start:start + len(sound)] += sound[:, None]
        if beat % 2 == 0:
            kick = tone(70, .18, 19) * .011
            music[start:start + len(kick)] += kick[:, None]
    music[:int(.5 * SR)] *= np.linspace(0, 1, int(.5 * SR))[:, None]
    music[int(12.96 * SR):int(13 * SR)] *= np.linspace(1, 0, int(.04 * SR))[:, None]
    for at in (.42, .53, .68, 9.95, 10.3, 10.5, 10.65, 11.1, 11.23, 11.34, 11.55, 12.1):
        noise = rng.normal(0, 1, int(.037 * SR)) * np.exp(-np.arange(int(.037 * SR)) / SR * 125)
        add(at, noise, .05, -.15, "keyboard_tap")
    for at in (4, 6.32, 8.9, 9.3, 10.02, 10.36, 10.67, 11.35, 12.25):
        add(at, tone(1500, .025, 150), .09, -.12, "mouse_click")
    add(5, tone(659.25, .35, 9) + tone(987.77, .35, 11), .075, .08, "call_confirmation")
    t = np.arange(int(.34 * SR)) / SR
    scratch = np.sin(2 * np.pi * (900 * t - 800 * t * t)) * rng.normal(0, .5, len(t))
    scratch *= np.sin(np.pi * np.linspace(0, 1, len(t)))
    add(6, scratch, .16, 0, "original_record_scratch")
    t = np.arange(int(.72 * SR)) / SR
    boom = np.sin(2 * np.pi * (75 * t - 31 * t * t)) * np.exp(-7 * t)
    add(7, boom, .18, 0, "low_cinematic_boom")
    for at in (8, 8.85, 9.63, 10.3, 10.86, 11.38, 11.86, 12.28, 12.68):
        add(at, tone(52, .12, 22), .065, 0, "heartbeat")
        add(at + .15, tone(65, .09, 27), .038, 0, "heartbeat_tail")
    for at in (10, 10.15, 10.42):
        add(at, tone(1175, .28, 15), .1, .13, "notification_ping")
    for at in (7.8, 9.75, 12.35):
        add(at, tone(1568, .19, 18), .035, .3, "sweat_plink")
    add(15, tone(760, .12, 24) + tone(640, .12, 24), .075, 0, "tiny_error_beep")
    # Last half second is digital silence, not merely very quiet music.
    music[int(17.5 * SR):] = 0
    sfx[int(17.5 * SR):] = 0
    return music, sfx, events


def main():
    import numpy as np
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--model", default=None)
    parser.add_argument("--version", default="v002", help="New audio version directory, v002 or later; delivered outputs are protected")
    parser.add_argument("--offline", action="store_true", help="Use cached speech and transcripts only")
    args = parser.parse_args()
    if not re.fullmatch(r"v\d{3}", args.version) or int(args.version[1:]) < 2:
        raise ValueError("Use a new version v002 or later; original delivered v001 is preserved")
    audio_dir, edit_dir = EPISODE / "audio" / args.version, EPISODE / "edit" / args.version
    dialogue_file = audio_dir / f"EP009_Dialogue_18s_{args.version}.wav"
    mix_file = audio_dir / f"EP009_Final_Mix_18s_{args.version}.wav"
    cues_file = edit_dir / f"speech_cues_{args.version}.json"
    if mix_file.exists() or cues_file.exists():
        raise FileExistsError(f"Delivered {args.version} audio/cues are protected; choose a new --version")
    defaults = json.loads((ROOT / "config/production_defaults.json").read_text())
    lines, peter_identity = configured_lines(defaults)
    audio_dir.mkdir(parents=True, exist_ok=True)
    edit_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    metadata_path = audio_dir / f"speech_generation_{args.version}.json"
    previous = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
    if args.offline:
        model = args.model or previous.get("tts_model") or defaults.get("tts_model")
        if not model:
            raise SpeechAPIError("No cached speech metadata for offline generation")
        gemini_pool = groq_pool = None
    else:
        pools = load_key_pools(args.env_file)
        print("Configured server-side speech pools:", {name: len(keys) for name, keys in pools.items()}, flush=True)
        gemini_pool, groq_pool = KeyPool(pools["GEMINI_API_KEYS"]), KeyPool(pools["GROQ_API_KEYS"])
        available = gemini_models(gemini_pool)
        preferred = ("gemini-3.8-flash-tts", "gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts")
        model = args.model or next((model for model in preferred if model in available), None)
        if not model:
            raise SpeechAPIError("No documented free-tier Gemini TTS model is available to these keys")
        print("Selected documented free-tier TTS model:", model, flush=True)
    evidence_path = edit_dir / f"peter_voice_catalog_{args.version}.json"
    if args.offline:
        if not evidence_path.is_file():
            raise SpeechAPIError("Offline generation requires previously verified male Peter catalog evidence")
        voice_evidence = json.loads(evidence_path.read_text())
        if voice_evidence.get("voice") != peter_identity["voice"] or voice_evidence.get("gender") != "male":
            raise SpeechAPIError("Cached male voice identity differs from configured Peter voice")
    else:
        voice_evidence = catalog_gender_evidence(gemini_pool, peter_identity)
        evidence_path.write_text(json.dumps(voice_evidence, indent=2) + "\n")
    print("Permanent Peter voice verified:", peter_identity["voice"], "male", flush=True)
    dialogue = np.zeros(DURATION * SR)
    completed, generation = [], []
    for spec in lines:
        raw, fitted = audio_dir / f'{spec["id"]}_Gemini_Raw.wav', audio_dir / f'{spec["id"]}_Dialogue.wav'
        line_meta = audio_dir / f'{spec["id"]}_generation.json'
        signature = speech_signature(spec, model)
        cached = json.loads(line_meta.read_text()) if line_meta.exists() else {}
        if not raw.exists() and reuse_host_cache(audio_dir, spec, model):
            cached = json.loads(line_meta.read_text())
            print("Reusing unchanged", spec["id"], "Puck host audio and real transcript", flush=True)
        if not (raw.exists() and cached.get("signature") == signature and cached.get("raw_sha256") == file_hash(raw)):
            if args.offline:
                raise SpeechAPIError(f'{spec["id"]}: missing or changed cached Gemini audio')
            print("Generating", spec["id"], spec["speaker"], spec["voice"], flush=True)
            raw.write_bytes(gemini_tts(gemini_pool, spec["text"], spec["voice"], spec["style"], model))
            cached = {"signature": signature, "raw_sha256": file_hash(raw), "tts_model": model, "voice": spec["voice"]}
            line_meta.write_text(json.dumps(cached, indent=2) + "\n")
        fit = fit_line(raw, fitted, spec["end"] - spec["start"])
        data, _ = read_wav(fitted)
        stt_path = audio_dir / f'{spec["id"]}_Groq_Whisper.json'
        stt_signature = file_hash(fitted)
        stt = json.loads(stt_path.read_text()) if stt_path.exists() else {}
        if stt.get("input_sha256") != stt_signature:
            if args.offline:
                raise SpeechAPIError(f'{spec["id"]}: missing or changed cached Groq transcript')
            print("Word-aligning", spec["id"], "with whisper-large-v3", flush=True)
            response = groq_transcribe(groq_pool, fitted, prompt=spec["text"])
            stt = {"model": "whisper-large-v3", "input_sha256": stt_signature, "response": response}
            stt_path.write_text(json.dumps(stt, indent=2) + "\n")
        words = authoritative_words(spec["text"], stt["response"], spec["start"], len(data) / SR)
        line = {**spec, "words": words, "audio": str(fitted.relative_to(ROOT)).replace("\\", "/"), **fit}
        completed.append(line)
        start = int(spec["start"] * SR)
        dialogue[start:start + len(data)] += data
        generation.append({"id": spec["id"], "speaker": spec["speaker"], "voice": spec["voice"],
                           "tts_model": model, "cache_signature": signature,
                           "raw_audio_sha256": file_hash(raw), "fitted_audio_sha256": file_hash(fitted),
                           "raw_audio": raw.relative_to(ROOT).as_posix(),
                           "fitted_audio": fitted.relative_to(ROOT).as_posix(),
                           "reused_from_audio_version": cached.get("reused_from_audio_version"), **fit})
        print(spec["id"], "ready", len(words), "timed words; speed", fit["speed_factor"], flush=True)
    music, sfx, sfx_cues = original_music_sfx()
    # Voice-aware ducking and conservative mix headroom; no hard clip distortions.
    envelope = np.sqrt(np.convolve(dialogue ** 2, np.ones(480) / 480, mode="same"))
    duck = np.where(envelope > .014, .28, 1.0)
    music *= duck[:, None]
    sfx *= np.where(envelope[:, None] > .014, .60, 1.0)
    mix = dialogue[:, None] + music + sfx
    peak = float(np.max(np.abs(mix)))
    mix_gain = min(1, .89 / max(.001, peak))
    mix *= mix_gain
    mix[int(17.5 * SR):] = 0
    write_wav(dialogue_file, np.repeat(dialogue[:, None], 2, axis=1))
    write_wav(mix_file, mix)
    write_wav(audio_dir / f"EP009_Original_Music_SFX_18s_{args.version}.wav", music + sfx)
    mouths = make_mouth_frames(dialogue, completed)
    for line in completed:
        line["mouth_frames"] = [row for row in mouths if line["start"] <= row["time"] < line["end"]]
    cues = {"schema_version": 1, "episode": "EP009_Wrong_Screen", "duration_seconds": DURATION,
            "fps": FPS, "frame_start": 1, "frame_end": 432, "sample_rate": SR, "channels": 2,
            "tts_provider": "Gemini", "tts_model": model, "stt_provider": "Groq", "stt_model": "whisper-large-v3",
            "audio_version": args.version, "character_voices": {"Peter": peter_identity},
            "peter_voice": {**peter_identity, "catalog_gender_verified": True},
            "peter_voice_catalog_evidence": voice_evidence,
            "speech_audio_evidence": generation,
            "timing_source": "Groq Whisper word timestamps on actual fitted speech audio",
            "lip_sync_method": "Measured 24fps RMS envelope plus word-based heuristic vowel/consonant visemes; not phoneme forced alignment",
            "viseme_shapes": ["rest", "A", "E", "O", "MBP", "FV"], "lines": completed,
            "words": [{**word, "speaker": line["speaker"], "line_id": line["id"]} for line in completed for word in line["words"]],
            "mouth_frames": mouths, "sfx": sfx_cues,
            "dialogue_file": str(dialogue_file.relative_to(ROOT)).replace("\\", "/"),
            "mix_file": str(mix_file.relative_to(ROOT)).replace("\\", "/"), "documentation": DOCS}
    cues_file.write_text(json.dumps(cues, indent=2) + "\n")
    metadata = {"tts_model": model, "stt_model": "whisper-large-v3", "lines": generation,
                "sample_rate": SR, "channels": 2, "duration_seconds": DURATION,
                "mix_peak_dbfs": round(20 * math.log10(float(np.max(np.abs(mix)))), 3),
                "mix_gain": mix_gain, "elapsed_seconds": round(time.monotonic() - started, 3),
                "final_half_second_silent": bool(np.max(np.abs(mix[int(17.5 * SR):])) == 0),
                "audio_version": args.version, "character_voices": {"Peter": peter_identity},
                "voice_catalog_evidence": voice_evidence,
                "docs": DOCS, "listening_review_performed": False}
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    print("Complete:", mix_file.relative_to(ROOT), "18s / 432 frames / 48kHz stereo", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (SpeechAPIError, FileExistsError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
