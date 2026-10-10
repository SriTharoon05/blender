"""Read-only EP010 delivery audit; writes only one new verification report.

Inspect actual MP4 streams and decoded audio, speech/puppet provenance, static
GPU plates, transparent PNGs and immutable historical sources. No render calls.
"""
from __future__ import annotations

import argparse
from array import array
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
from pathlib import Path
import re
import sys
import time
import wave

from ep009_verify_delivery import command, committed_source_matches, read_json, relative, sha256
from production_paths import RuntimePaths
from production_queue import verify_png

ROOT = Path(__file__).resolve().parents[1]
EPISODE = "02_EPISODES/EP010_Binge_Watching"
FPS, FRAME_END, DURATION, SR = 24, 528, 22, 48000
EXPECTED_LINES = [
    ("L01", "peter", "Just one episode before bed."),
    ("L02", "inner", "You said that yesterday."),
    ("L03", "peter", "Tonight, I'm being responsible."),
    ("L04", "announcer", "Next episode starts in five seconds."),
    ("L05", "peter", "Okay, this is the last one."),
    ("L06", "inner", "You have work in four hours."),
    ("L07", "peter", "I NEED TO KNOW WHAT HAPPENS!"),
    ("L08", "peter", "Wait… why are the birds singing?"),
    ("L09", "peter", "I have work in thirty minutes."),
    ("L10", "peter", "Worth it."),
]
FINAL_TITLE = "POV: ONE EPISODE TURNED INTO THE WHOLE SEASON."


def inside_bounds(value, allowed, tolerance=.02):
    return isinstance(value, (list, tuple)) and len(value) == 4 \
        and value[0] >= allowed[0] - tolerance and value[1] >= allowed[1] - tolerance \
        and value[2] <= allowed[2] + tolerance and value[3] <= allowed[3] + tolerance \
        and value[0] <= value[2] and value[1] <= value[3]


def verify_caption_metadata(project, cues):
    records, words = project.get("spoken_caption_records", []), cues.get("words", [])
    errors, occupancy = [], [[] for _ in range(FRAME_END + 1)]
    if len(records) != len(words) or len(words) != 51:
        errors.append("Expected exactly 51 measured words and 51 spoken caption records")
    if [(line.get("id"), line.get("speaker"), line.get("text")) for line in cues.get("lines", [])] != EXPECTED_LINES:
        errors.append("Speech cues differ from the exact scripted dialogue/speakers")
    flattened = [(w["word"], line["speaker"]) for line in cues.get("lines", []) for w in line.get("words", [])]
    if [(w.get("word"), w.get("speaker")) for w in words] != flattened:
        errors.append("Flattened caption words differ from actual line-level measured words")
    bounds, min_delta, max_delta = (130, 1340, 870, 1470), 0, 0
    for index, (record, word) in enumerate(zip(records, words), 1):
        if (record.get("word"), record.get("speaker")) != (word.get("word"), word.get("speaker")):
            errors.append(f"Caption {index} wording/speaker differs from measured speech")
        if record.get("start_frame") != word.get("start_frame"):
            errors.append(f"Caption {index} onset differs from measured speech frame")
        end_delta = record.get("end_frame", -100) - word.get("end_frame", 0)
        min_delta, max_delta = min(min_delta, end_delta), max(max_delta, end_delta)
        if end_delta not in (-1, 0):
            errors.append(f"Caption {index} end adjustment exceeds one-frame overlap correction")
        if not inside_bounds(record.get("max_bounds_px"), bounds):
            errors.append(f"Caption {index} maximum pop exceeds the lower safe band")
        start, end = record.get("start_frame", 0), record.get("end_frame", 0)
        if not 1 <= start <= end <= FRAME_END:
            errors.append(f"Caption {index} has an invalid frame interval")
        else:
            for frame in range(start, end + 1):
                occupancy[frame].append(record["word"])
    overlap = [frame for frame, active in enumerate(occupancy) if len(active) > 1]
    if overlap:
        errors.append("More than one spoken word caption is visible on a frame")
    titles, title_checks = project.get("title_records", []), []
    if len(titles) != 2:
        errors.append("Expected setup and final title records")
    for index, title in enumerate(titles, 1):
        valid = inside_bounds(title.get("bounds_px"), (108, 300, 918, 480))
        interval = title.get("interval", [0, 0])
        interval_ok = len(interval) == 2 and 1 <= interval[0] <= interval[1] <= FRAME_END
        if not valid or not interval_ok:
            errors.append(f"Title {index} exceeds its top safe band or frame range")
        title_checks.append({**title, "within_top_safe_band": valid, "valid_interval": interval_ok})
    final = titles[-1] if titles else {}
    if " ".join(final.get("text", "").split()) != FINAL_TITLE or final.get("interval") != [517, 528]:
        errors.append("The exact final POV title must hold during frames 517..528")
    if project.get("caption_shake_fixed") is not True:
        errors.append("Caption metadata must establish that camera shake does not move text")
    mouth_rows = cues.get("mouth_frames", [])
    if [row.get("frame") for row in mouth_rows] != list(range(1, FRAME_END + 1)):
        errors.append("Measured lip-sync cues must cover all 528 frames")
    return {"word_count": len(words), "caption_count": len(records), "safe_band_px": list(bounds),
            "geometry_tolerance_px": .02, "max_pop_bounds_within_safe_band": not any("safe band" in e for e in errors),
            "caption_onsets_match_measured_frames": not any("onset" in e for e in errors),
            "caption_end_adjustment_frames": [min_delta, max_delta],
            "maximum_simultaneously_active_spoken_words": max(map(len, occupancy)), "overlap_frames": overlap,
            "title_records": title_checks, "speech_timing_source": cues.get("timing_source"),
            "source_of_geometry_bounds": "Actual Blender build report; encoded pixel review has separately recorded scope",
            "errors": errors}


def verify_peter_voice(project, cues, defaults, generation=None, hash_source=None):
    """Peter and inner Peter have one identity; provenance is separate from listening."""
    errors = []
    expected = {"provider": "Gemini", "voice": "Charon", "gender": "male",
                "locked": True, "allow_voice_fallback": False}
    configured = defaults.get("tts_character_voices", {}).get("Peter", {})
    cue_identity = cues.get("character_voices", {}).get("Peter", {})
    for label, identity in (("Production", configured), ("Speech cue", cue_identity)):
        for name, value in expected.items():
            if identity.get(name) != value:
                errors.append(f"{label} Peter identity must set {name}={value}")
    selected = project.get("peter_voice")
    project_voice = selected.get("voice") if isinstance(selected, dict) else selected
    if project_voice != "Charon":
        errors.append("Actual puppet project reports a different Peter voice")
    if cues.get("tts_provider") != "Gemini":
        errors.append("Peter cues must identify the Gemini TTS provider")
    lines = [line for line in cues.get("lines", []) if line.get("speaker") in ("peter", "inner")]
    if not lines or not any(line["speaker"] == "inner" for line in lines):
        errors.append("Peter dialogue and inner-thought lines must both exist")
    voice_rows = []
    for line in lines:
        valid = line.get("voice") == "Charon" and line.get("character") == "Peter"
        voice_rows.append({"line_id": line.get("id"), "speaker": line.get("speaker"),
                           "voice": line.get("voice"), "matches_permanent_identity": valid})
        if not valid:
            errors.append(f"Peter line {line.get('id')} uses a different voice or character")
    catalog = cues.get("peter_voice_catalog_evidence", {})
    catalog_ok = catalog.get("voice") == "Charon" and catalog.get("gender") == "male" \
        and catalog.get("verified_live_catalog") is True
    if not catalog_ok:
        errors.append("Male Charon is not established by live-catalog evidence")
    provenance = []
    if generation is None:
        errors.append("Actual speech generation provenance is unavailable")
    else:
        generated = {row.get("id"): row for row in generation.get("speech_audio_evidence") or generation.get("lines", [])}
        summaries = {row.get("id"): row for row in generation.get("lines", [])}
        # Check the announcer's selected source too, so every audible line has provenance.
        for line in cues.get("lines", []):
            row, summary = generated.get(line.get("id"), {}), summaries.get(line.get("id"), {})
            valid = row.get("voice") == line.get("voice") and row.get("speaker") == line.get("speaker") \
                and row.get("tts_model") == cues.get("tts_model") and row.get("fitted_audio") == line.get("audio") \
                and summary.get("voice") == line.get("voice") and summary.get("speaker") == line.get("speaker")
            if not valid:
                errors.append(f"Actual generation metadata differs for line {line.get('id')}")
            hashes = {}
            for label in ("raw", "fitted"):
                source, digest = row.get(f"{label}_audio"), row.get(f"{label}_audio_sha256")
                matched = None
                if not source or not digest:
                    errors.append(f"Missing {label} provenance for line {line.get('id')}")
                elif hash_source is not None:
                    try:
                        matched = hash_source(source) == digest
                    except (OSError, ValueError, KeyError):
                        matched = False
                    if not matched:
                        errors.append(f"Actual {label} audio hash differs for line {line.get('id')}")
                hashes[label] = {"source": source, "sha256": digest, "actual_hash_matches": matched}
            provenance.append({"line_id": line.get("id"), "speaker": line.get("speaker"),
                               "voice": row.get("voice"), "metadata_matches": valid, "audio_provenance": hashes})
    return {"configured_identity": configured, "cue_identity": cue_identity, "project_peter_voice": project_voice,
            "peter_line_count": len(lines), "inner_line_count": sum(line["speaker"] == "inner" for line in lines),
            "peter_lines": voice_rows, "live_catalog_matches_locked_male_voice": catalog_ok,
            "male_voice_catalog_evidence": catalog, "actual_generation_lines": provenance,
            "evidence_scope": "Voice ID, live gender catalogue, actual metadata and hashes; acoustic listening is separate",
            "all_voice_checks_passed": not errors, "errors": errors}


def protected_assets(revision):
    baseline = json.loads(command(["git", "show", f"{revision}:config/approved_assets.json"]))["assets"]
    checks, errors = [], []
    for name, expected in baseline.items():
        path = ROOT / name
        valid = path.is_file() and path.stat().st_size == expected["bytes"] and sha256(path) == expected["sha256"]
        checks.append({"path": name, "unchanged": valid})
        if not valid:
            errors.append(f"Protected approved asset changed: {name}")
    names = command(["git", "ls-tree", "-r", "--name-only", revision, "02_EPISODES/"]).splitlines()
    historical = []
    for name in names:
        valid = committed_source_matches(name, command(["git", "show", f"{revision}:{name}"], binary=True), ROOT / name)
        historical.append({"path": name, "unchanged": valid})
        if not valid:
            errors.append(f"Previously committed episode source changed: {name}")
    return {"baseline_git_revision": revision, "approved_asset_count": len(checks), "approved_assets": checks,
            "historical_episode_project_count": sum(row["path"].endswith(".blend") for row in historical),
            "historical_episode_source_count": len(historical), "historical_episode_sources": historical,
            "comparison_policy": "Exact binary bytes; text content permits CRLF/LF normalization only",
            "authorized_source_update_exceptions": [], "inventory_refreshed": False, "all_unchanged": not errors,
            "errors": errors}


def verify_plate_evidence(project, report, path_resolver, hash_source):
    errors, rows = [], report.get("plates", [])
    if len(rows) != 2 or project.get("background_plates") != [row.get("file") for row in rows]:
        errors.append("Selected two background plates differ from actual static render evidence")
    if report.get("engine") != "Cycles" or report.get("backend") not in ("OptiX", "CUDA") \
            or report.get("cpu_render_enabled") is not False:
        errors.append("Static plates were not established as Cycles GPU renders without CPU fallback")
    gpu = report.get("gpu", [])
    if not any("1650 ti" in row.get("name", "").lower() for row in gpu):
        errors.append("Static render evidence does not name the local GTX 1650 Ti")
    for row in rows:
        path = path_resolver(row["file"])
        if hash_source(row["file"]) != row.get("sha256") or path.stat().st_size != row.get("bytes"):
            errors.append(f"Static plate hash/size changed: {row['file']}")
        if not verify_png(path, 1080, 1920):
            errors.append(f"Static plate PNG integrity is invalid: {row['file']}")
    total = sum(float(row.get("render_seconds", 0)) for row in rows)
    if total <= 0 or abs(total - float(report.get("static_plate_render_seconds", 0))) > .00001:
        errors.append("Static render elapsed total differs from individual actual plate times")
    return {"plates": rows, "gpu": gpu, "cpu_render_enabled": report.get("cpu_render_enabled"),
            "static_plate_render_seconds": total, "engine": report.get("engine"), "backend": report.get("backend"),
            "blender_version": report.get("blender_version"), "errors": errors}


def verify_transparent_sequence(project, runtime, ffmpeg):
    folder = runtime.repo_path(project["transparent_foreground_sequence"], must_exist=True)
    files, errors = {}, []
    for path in folder.glob("*.png"):
        match = re.search(r"(\d+)$", path.stem)
        if match:
            frame = int(match.group(1))
            if frame in files:
                errors.append(f"Duplicate transparent PNG for frame {frame}")
            files[frame] = path
    if sorted(files) != list(range(1, FRAME_END + 1)):
        errors.append("Transparent foreground sequence does not cover exactly frames 1..528")
    for frame, path in files.items():
        with path.open("rb") as stream:
            header = stream.read(26)
        if len(header) < 26 or header[25] != 6 or not verify_png(path, 1080, 1920):
            errors.append(f"Transparent frame {frame} is not an intact 1080x1920 RGBA PNG")
    alpha_checks = []
    for frame in (1, 361, 528):
        if frame not in files:
            continue
        alpha = command([ffmpeg, "-v", "error", "-i", files[frame], "-vf", "alphaextract",
                         "-frames:v", "1", "-pix_fmt", "gray", "-f", "rawvideo", "-"], binary=True)
        valid = len(alpha) == 1080 * 1920 and min(alpha) == 0 and max(alpha) == 255
        alpha_checks.append({"frame": frame, "transparent_and_opaque_pixels": valid})
        if not valid:
            errors.append(f"Transparent frame {frame} lacks the expected clear/opaque foreground alpha")
    return {"folder": relative(folder), "png_count": len(files), "frame_range": [1, 528],
            "resolution": [1080, 1920], "color_mode": "RGBA", "png_headers_and_crcs_checked": True,
            "alpha_samples": alpha_checks, "errors": errors}


def verify_encoded_media(video, reference_path, ffprobe, ffmpeg, listening_reviewed=False):
    started = time.monotonic()
    probe = json.loads(command([ffprobe, "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", video]))
    videos = [row for row in probe["streams"] if row["codec_type"] == "video"]
    audios = [row for row in probe["streams"] if row["codec_type"] == "audio"]
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError("Final MP4 must contain exactly one video and one audio stream")
    v, a, errors = videos[0], audios[0], []
    media = {"resolution": [v["width"], v["height"]], "fps": float(Fraction(v["avg_frame_rate"])),
             "frame_count": int(v["nb_read_frames"]), "video_seconds": float(v["duration"]),
             "container_seconds": float(probe["format"]["duration"]), "codec": v["codec_name"],
             "pixel_format": v["pix_fmt"], "audio_codec": a["codec_name"], "audio_sample_rate": int(a["sample_rate"]),
             "audio_channels": a["channels"], "audio_seconds": float(a["duration"]),
             "video_start_seconds": float(v.get("start_time", 0)), "audio_start_seconds": float(a.get("start_time", 0))}
    required = {"resolution": [1080, 1920], "fps": 24.0, "frame_count": FRAME_END, "codec": "h264",
                "pixel_format": "yuv420p", "audio_codec": "aac", "audio_sample_rate": SR, "audio_channels": 2}
    for name, expected in required.items():
        if media[name] != expected:
            errors.append(f"Actual media {name} differs from required {expected}")
    for name in ("video_seconds", "container_seconds", "audio_seconds"):
        if abs(media[name] - DURATION) > .025:
            errors.append(f"Actual media {name} differs from 22 seconds")
    decode_started = time.monotonic()
    command([ffmpeg, "-hide_banner", "-v", "error", "-xerror", "-i", video,
             "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"])
    decode_seconds = time.monotonic() - decode_started
    samples = array("f")
    samples.frombytes(command([ffmpeg, "-v", "error", "-xerror", "-i", video, "-map", "0:a:0",
                               "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], binary=True))
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max(map(abs, samples), default=0)
    last = samples[int(21.5 * SR * 2):DURATION * SR * 2]
    final_peak = max(map(abs, last), default=0)
    final_rms = math.sqrt(sum(value * value for value in last) / max(1, len(last)))
    if len(last) != SR or final_peak > .00001:
        errors.append("Decoded final half-second is not effectively silent")
    if peak >= 1:
        errors.append("Decoded AAC audio clips at or above full scale")
    if abs(media["audio_start_seconds"] - media["video_start_seconds"]) > 1 / SR:
        errors.append("Encoded audio/video stream start times differ")
    with wave.open(str(reference_path), "rb") as stream:
        if (stream.getframerate(), stream.getnchannels(), stream.getsampwidth(), stream.getnframes()) != (SR, 2, 2, DURATION * SR):
            raise ValueError("Reference audio must be exactly 22s of 48kHz stereo PCM16")
        reference = array("h")
        reference.frombytes(stream.readframes(stream.getnframes()))
    if sys.byteorder != "little":
        reference.byteswap()
    if any(reference[int(21.5 * SR * 2):]):
        errors.append("Source mix final half-second is not digitally silent")
    if len(samples) < len(reference):
        errors.append("Decoded AAC audio is shorter than the actual source mix")
    source_energy = decoded_energy = product = error_energy = 0.0
    for encoded, original in zip(samples, reference):
        expected = original / 32768
        source_energy += expected * expected
        decoded_energy += encoded * encoded
        product += encoded * expected
        error_energy += (encoded - expected) ** 2
    correlation = product / math.sqrt(max(1e-30, source_energy * decoded_energy))
    snr = 10 * math.log10(max(1e-30, source_energy) / max(1e-30, error_energy))
    if correlation < .985 or snr < 18:
        errors.append("Decoded AAC differs excessively from the source mix at zero delay")
    audio = {"source_mix": relative(reference_path), "source_mix_sha256": sha256(reference_path),
             "decoded_samples_per_channel": len(samples) // 2, "decoded_peak_dbfs": 20 * math.log10(peak) if peak else None,
             "decoded_pcm_clipping_abs_ge_1": peak >= 1, "final_half_second_peak": final_peak, "final_half_second_rms": final_rms,
             "final_half_second_effectively_silent": len(last) == SR and final_peak <= .00001,
             "decoded_aac_zero_delay_source_correlation": correlation, "decoded_aac_vs_source_snr_db": snr,
             "correct_source_mix_and_zero_delay_verified": correlation >= .985 and snr >= 18,
             "listening_review_performed": listening_reviewed}
    return {"media": media, "audio": audio, "full_video_and_audio_decode_passed": True,
            "full_decode_seconds": round(decode_seconds, 3), "media_verification_seconds": round(time.monotonic() - started, 3),
            "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True)
    parser.add_argument("--queue-state", required=True)
    parser.add_argument("--project-report", default=f"{EPISODE}/edit/v001/project_verification_v001.json")
    parser.add_argument("--cues", default=f"{EPISODE}/edit/v001/speech_cues_v001.json")
    parser.add_argument("--plates-report", default=f"{EPISODE}/edit/plate_render_time_v002.json")
    parser.add_argument("--audio-generation", default=None)
    parser.add_argument("--output", required=True, help="New verification JSON; existing files are protected")
    parser.add_argument("--baseline-revision", default="HEAD")
    parser.add_argument("--visual-review-note", default="")
    parser.add_argument("--encoded-review-frames", nargs="+", type=int, default=[])
    parser.add_argument("--phone-preview-width", type=int, default=None)
    parser.add_argument("--encoded-review-artifact", default=None)
    parser.add_argument("--audio-listening-reviewed", action="store_true")
    args = parser.parse_args()
    runtime = RuntimePaths.discover()
    video, state_path, project_path, cues_path, plates_path = [runtime.repo_path(value, must_exist=True)
        for value in (args.video, args.queue_state, args.project_report, args.cues, args.plates_report)]
    output = runtime.repo_path(args.output)
    if output.exists() or output.suffix.lower() != ".json":
        raise FileExistsError("Use a new, nonexistent versioned JSON output path")
    if command(["git", "ls-tree", "-r", "--name-only", "HEAD", "--", relative(output)]).strip():
        raise FileExistsError("Selected output is an already committed historical report")
    if any(frame < 1 or frame > FRAME_END for frame in args.encoded_review_frames):
        raise ValueError("Review frame numbers must be inside 1..528")
    if args.encoded_review_artifact:
        runtime.repo_path(args.encoded_review_artifact, must_exist=True)
    revision = command(["git", "rev-parse", "--verify", args.baseline_revision + "^{commit}"]).strip()
    started = time.monotonic()
    project, cues, plates = read_json(project_path), read_json(cues_path), read_json(plates_path)
    state, delivery = read_json(state_path), read_json(state_path.parent / "delivery.json")
    defaults = read_json(ROOT / "config/production_defaults.json")
    ffprobe, ffmpeg = runtime.resolve_tool("ffprobe"), runtime.resolve_tool("ffmpeg")
    reference = runtime.repo_path(cues["mix_file"], must_exist=True)
    media = verify_encoded_media(video, reference, ffprobe, ffmpeg, args.audio_listening_reviewed)
    captions = verify_caption_metadata(project, cues)
    generation_path = runtime.repo_path(args.audio_generation, must_exist=True) if args.audio_generation else \
        reference.parent / f"speech_generation_{cues['audio_version']}.json"
    generation = read_json(generation_path) if generation_path.is_file() else None
    voices = verify_peter_voice(project, cues, defaults, generation, lambda name: sha256(runtime.repo_path(name, must_exist=True)))
    plate_checks = verify_plate_evidence(project, plates, lambda name: runtime.repo_path(name, must_exist=True),
                                        lambda name: sha256(runtime.repo_path(name, must_exist=True)))
    transparent = verify_transparent_sequence(project, runtime, ffmpeg)
    protected = protected_assets(revision)
    errors = [error for report in (media, captions, voices, plate_checks, transparent, protected) for error in report["errors"]]
    required = {"frames": FRAME_END, "video_seconds": DURATION, "resolution": [1080, 1920], "fps": FPS,
                "engine": "BLENDER_EEVEE", "character_geometry_redraws_per_frame": 0, "character_mesh_animation": False,
                "background_count": 2, "caption_font": "LuckiestGuy-Regular.ttf", "packed_audio": True,
                "caption_shake_fixed": True, "compositor_device": "GPU"}
    for name, expected in required.items():
        if project.get(name) != expected:
            errors.append(f"Native scene {name} differs from required {expected}")
    puppet = project.get("puppet_metadata", {})
    parts = int(puppet.get("main_static_parts", 0)) + int(puppet.get("inner_static_parts", 0))
    bones = int(puppet.get("skeletal_bones_per_character", 0)) * 2
    if parts < 28 or project.get("static_character_parts") != parts or bones < 32 or project.get("skeletal_bones") != bones \
            or puppet.get("parts_rigidly_bound") is not True:
        errors.append("Static modular part/bone counts or rigid puppet binding are not established")
    if project.get("speech_cues") != relative(cues_path) or project.get("audio") != cues.get("mix_file"):
        errors.append("Project references different speech cues or source audio")
    blend_path = runtime.repo_path(project["built_project"], must_exist=True)
    recorded_outputs = state.get("build", {}).get("output_hashes", {})
    for path in (blend_path, project_path):
        if recorded_outputs.get(relative(path)) != sha256(path):
            errors.append(f"Actual build output differs from queue evidence: {relative(path)}")
    if delivery.get("status") != "complete" or any(state.get(stage, {}).get("status") != "complete" for stage in ("build", "render", "encode")):
        errors.append("Queue does not establish completed build, render and encode stages")
    if delivery.get("video") != relative(video):
        errors.append("Queue delivery references a different movie")
    video_hash = sha256(video)
    if state.get("encode", {}).get("sha256") != video_hash:
        errors.append("Final movie hash differs from completed queue encoding")
    if "1650 ti" not in str(delivery.get("gpu", "")).lower():
        errors.append("Animation delivery lacks the actual GTX 1650 Ti GPU evidence")
    if len(state.get("render", {}).get("frame_hashes", {})) != FRAME_END:
        errors.append("Queue render record does not establish all 528 frame hashes")
    animation_seconds = float(delivery.get("render_seconds", 0))
    encoding_seconds = float(delivery.get("encode_seconds", 0))
    plate_seconds = plate_checks["static_plate_render_seconds"]
    if animation_seconds <= 0 or encoding_seconds <= 0:
        errors.append("Actual render/encoding elapsed measurements are unavailable")
    report = {"schema_version": 1, "episode": "EP010_Binge_Watching", "status": "passed" if not errors else "failed",
              "checked_utc": datetime.now(timezone.utc).isoformat(), "video": relative(video), "video_sha256": video_hash,
              "editable_project": relative(blend_path), "editable_project_sha256": sha256(blend_path),
              "selected_project_report": relative(project_path), "selected_speech_cues": relative(cues_path),
              **{key: value for key, value in media.items() if key != "errors"}, "captions": captions,
              "peter_voice_verification": voices, "audio_generation_source": relative(generation_path) if generation else None,
              "puppet": {name: project[name] for name in required}, "static_character_parts": parts, "skeletal_bones": bones,
              "static_plate_verification": plate_checks, "selected_plates_report": relative(plates_path),
              "transparent_foreground": transparent, "gpu": delivery.get("gpu"), "render_backend": "Blender sequential queue",
              "actual_render_times": {"static_plate_render_seconds": plate_seconds, "animation_render_seconds": animation_seconds,
                  "final_plate_plus_animation_render_seconds": plate_seconds + animation_seconds, "encoding_seconds": encoding_seconds,
                  "timing_scope": "Selected final two-plate version and final animation only; development/preview attempts excluded"},
              "protected_sources": protected, "visual_review_performed": bool(args.visual_review_note),
              "visual_review_note": args.visual_review_note or None,
              "encoded_video_visual_review": {"performed": bool(args.encoded_review_frames and args.visual_review_note),
                  "frames": args.encoded_review_frames, "phone_preview_width_px": args.phone_preview_width,
                  "artifact": args.encoded_review_artifact,
                  "scope": "Representative decoded MP4 frames; no complete motion or phoneme-sync review claimed"},
              "lip_sync_method": cues["lip_sync_method"], "audio_choices": cues.get("audio_choices"),
              "limitations": ["Word/amplitude visemes estimate mouth timing; not phoneme forced alignment",
                  "Caption geometry comes from evaluated native build metadata; encoded frame review scope is recorded separately"],
              "verification_elapsed_seconds": round(time.monotonic() - started, 3), "errors": errors}
    if not args.audio_listening_reviewed:
        report["limitations"].append("No subjective audio listening review performed")
    if not args.visual_review_note:
        report["limitations"].append("No final visual/lip-sync review claimed by this verifier")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "video_seconds": media["media"]["video_seconds"],
                      "frame_count": media["media"]["frame_count"], "static_plate_seconds": plate_seconds,
                      "animation_seconds": animation_seconds, "encoding_seconds": encoding_seconds,
                      "approved_asset_count": protected["approved_asset_count"],
                      "historical_project_count": protected["historical_episode_project_count"],
                      "historical_source_count": protected["historical_episode_source_count"],
                      "peter_voice": voices["project_peter_voice"], "errors": errors, "report": relative(output)}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
