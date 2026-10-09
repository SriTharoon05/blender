"""Read-only EP009 delivery audit; writes only its verification report.

Checks the actual encoded video, measured speech/caption metadata, puppet build
report and protected source assets. It never builds, renders or encodes a movie.
"""
from __future__ import annotations

import argparse
from array import array
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import wave

from production_paths import RuntimePaths


ROOT = Path(__file__).resolve().parents[1]
EPISODE = "02_EPISODES/EP009_Wrong_Screen"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def command(argv, *, binary=False):
    result = subprocess.run([str(item) for item in argv], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Validation subprocess failed: {Path(str(argv[0])).name}; exit {result.returncode}")
    return result.stdout if binary else result.stdout.decode("utf-8", errors="replace")


def verify_caption_metadata(project, cues):
    records, words = project["spoken_caption_records"], cues["words"]
    errors = []
    if len(records) != len(words) or len(words) != 32:
        errors.append("Expected exactly 32 caption records and measured spoken words")
    occupancy = [[] for _ in range(433)]
    tolerance = .02  # Native float transforms can differ by a few millionths of a pixel.
    bounds = (130, 1340, 870, 1470)
    max_delta, min_delta = 0, 0
    for index, (record, word) in enumerate(zip(records, words)):
        if record["word"] != word["word"]:
            errors.append(f"Caption {index + 1} wording differs from actual scripted speech")
        if record["start_frame"] != word["start_frame"]:
            errors.append(f"Caption {index + 1} onset differs from measured speech frame")
        end_delta = record["end_frame"] - word["end_frame"]
        max_delta, min_delta = max(max_delta, end_delta), min(min_delta, end_delta)
        if end_delta not in (-1, 0):
            errors.append(f"Caption {index + 1} end adjustment exceeds one-frame nonoverlap correction")
        measured = record["max_bounds_px"]
        if not (measured[0] >= bounds[0] - tolerance and measured[1] >= bounds[1] - tolerance
                and measured[2] <= bounds[2] + tolerance and measured[3] <= bounds[3] + tolerance):
            errors.append(f"Caption {index + 1} exceeds the lower safe band at maximum pop")
        start, end = record["start_frame"], record["end_frame"]
        if not 1 <= start <= end <= 432:
            errors.append(f"Caption {index + 1} invalid frame interval")
            continue
        for frame in range(start, end + 1):
            occupancy[frame].append(record["word"])
    overlapping = [frame for frame, active in enumerate(occupancy) if len(active) > 1]
    if overlapping:
        errors.append("Multiple spoken word captions active on the same frame")
    title = project["final_title_bounds_px"]
    title_ok = title[0] >= 108 - tolerance and title[1] >= 300 - tolerance \
        and title[2] <= 918 + tolerance and title[3] <= 480 + tolerance
    if not title_ok:
        errors.append("POV title exceeds its upper safe band")
    return {"word_count": len(words), "caption_count": len(records),
            "speech_timing_source": cues["timing_source"], "caption_onsets_match_measured_frames": not any("onset" in error for error in errors),
            "caption_end_adjustment_frames": [min_delta, max_delta],
            "maximum_simultaneously_active_spoken_words": max(map(len, occupancy)),
            "overlap_frames": overlapping, "safe_band_px": list(bounds),
            "max_pop_bounds_within_safe_band": not any("safe band" in error for error in errors),
            "title_bounds_px": title, "title_within_top_safe_band": title_ok,
            "source_of_geometry_bounds": "Actual Blender scene authoring report; pixel legibility reviewed separately",
            "geometry_tolerance_px": tolerance, "errors": errors}


def protected_assets():
    baseline_raw = command(["git", "show", "HEAD:config/approved_assets.json"])
    baseline = json.loads(baseline_raw)["assets"]
    checks = []
    errors = []
    for name, expected in baseline.items():
        path = ROOT / name
        valid = path.is_file() and path.stat().st_size == expected["bytes"] and sha256(path) == expected["sha256"]
        checks.append({"path": name, "unchanged": valid})
        if not valid:
            errors.append(f"Protected approved source changed: {name}")
    # Existing episode projects are compared with committed binary bytes; no asset inventory is refreshed.
    names = command(["git", "ls-tree", "-r", "--name-only", "HEAD", "02_EPISODES/"]).splitlines()
    previous_projects = [name for name in names if name.endswith(".blend")
                         and not name.startswith(EPISODE + "/")]
    project_checks = []
    for name in previous_projects:
        original = command(["git", "show", f"HEAD:{name}"], binary=True)
        path = ROOT / name
        valid = path.is_file() and sha256(path) == hashlib.sha256(original).hexdigest()
        project_checks.append({"path": name, "unchanged": valid})
        if not valid:
            errors.append(f"Previously committed episode project changed: {name}")
    return {"baseline_git_revision": command(["git", "rev-parse", "HEAD"]).strip(),
            "approved_asset_count": len(checks), "approved_assets": checks,
            "historical_episode_project_count": len(project_checks), "historical_episode_projects": project_checks,
            "inventory_refreshed": False, "all_unchanged": not errors, "errors": errors}


def unused_background_work(edit):
    entries = []
    for name in ("plate_render_time_v001.json", "plate_render_time_v002.json", "plate_render_time.json"):
        path = edit / name
        if path.is_file():
            report = read_json(path)
            entries.append({"source": relative(path), "seconds": report.get("static_plate_render_seconds", 0),
                            "used_in_final": False, "engine": report.get("engine"), "gpu": report.get("gpu")})
    return {"used_in_final": False, "previous_3d_background_versions": entries,
            "recorded_unused_3d_background_render_seconds": sum(row["seconds"] for row in entries),
            "note": "Earlier Cycles background preparation was superseded by the user's single flat-background instruction; excluded from final render time"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Repository-relative final MP4")
    parser.add_argument("--queue-state", required=True, help="Repository-relative completed queue state.json")
    parser.add_argument("--output", default=f"{EPISODE}/edit/delivery_verification.json")
    parser.add_argument("--visual-review-note", default="", help="Only supply after actual rendered frames were inspected")
    parser.add_argument("--encoded-review-frames", nargs="+", type=int, default=[], help="Actual decoded final MP4 frames visually inspected")
    parser.add_argument("--phone-preview-width", type=int, default=None, help="Actual preview width in pixels, if reviewed")
    parser.add_argument("--encoded-review-artifact", default=None, help="Repository-relative inspected contact sheet, if available")
    parser.add_argument("--audio-listening-reviewed", action="store_true", help="Only supply after actual listening")
    args = parser.parse_args()
    runtime = RuntimePaths.discover()
    video, state_path = runtime.repo_path(args.video, must_exist=True), runtime.repo_path(args.queue_state, must_exist=True)
    output = runtime.repo_path(args.output)
    if any(frame < 1 or frame > 432 for frame in args.encoded_review_frames):
        raise ValueError("Encoded review frame numbers must be inside 1..432")
    if args.encoded_review_artifact:
        runtime.repo_path(args.encoded_review_artifact, must_exist=True)
    edit = ROOT / EPISODE / "edit"
    ffprobe, ffmpeg = runtime.resolve_tool("ffprobe"), runtime.resolve_tool("ffmpeg")
    project, cues = read_json(edit / "project_verification.json"), read_json(edit / "speech_cues_v001.json")
    state, delivery = read_json(state_path), read_json(state_path.parent / "delivery.json")
    started = time.monotonic()
    probe = json.loads(command([ffprobe, "-v", "error", "-count_frames", "-show_streams", "-show_format",
                                "-of", "json", video]))
    videos = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
    audios = [stream for stream in probe["streams"] if stream["codec_type"] == "audio"]
    errors = []
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError("Final MP4 must contain one video and one audio stream")
    v, a = videos[0], audios[0]
    video_checks = {"resolution": [v["width"], v["height"]],
                    "fps": float(Fraction(v["avg_frame_rate"])), "frame_count": int(v["nb_read_frames"]),
                    "video_seconds": float(v["duration"]), "container_seconds": float(probe["format"]["duration"]),
                    "codec": v["codec_name"], "pixel_format": v["pix_fmt"],
                    "audio_codec": a["codec_name"], "audio_sample_rate": int(a["sample_rate"]),
                    "audio_channels": a["channels"], "audio_seconds": float(a["duration"]),
                    "video_start_seconds": float(v.get("start_time", 0)),
                    "audio_start_seconds": float(a.get("start_time", 0))}
    required = {"resolution": [1080, 1920], "fps": 24.0, "frame_count": 432,
                "codec": "h264", "pixel_format": "yuv420p", "audio_codec": "aac",
                "audio_sample_rate": 48000, "audio_channels": 2}
    for name, expected in required.items():
        if video_checks[name] != expected:
            errors.append(f"Final media {name} differs from required {expected}")
    for name in ("video_seconds", "container_seconds", "audio_seconds"):
        if abs(video_checks[name] - 18) > .025:
            errors.append(f"Final media {name} differs from 18 seconds")
    decode_start = time.monotonic()
    command([ffmpeg, "-hide_banner", "-v", "error", "-xerror", "-i", video,
             "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"])
    decode_seconds = time.monotonic() - decode_start
    samples = array("f")
    samples.frombytes(command([ffmpeg, "-hide_banner", "-v", "error", "-xerror", "-i", video,
                               "-map", "0:a:0", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], binary=True))
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max(map(abs, samples), default=0)
    final_samples = samples[int(17.5 * 48000 * 2):int(18 * 48000 * 2)]
    final_peak = max(map(abs, final_samples), default=0)
    final_rms = math.sqrt(sum(sample * sample for sample in final_samples) / max(1, len(final_samples)))
    if len(final_samples) != 48000 or final_peak > .00001:
        errors.append("Decoded final half-second is not effectively silent")
    audio = {"decoded_samples_per_channel": len(samples) // 2,
             "decoded_peak_dbfs": 20 * math.log10(peak) if peak > 0 else None,
             "decoded_pcm_clipping_abs_ge_1": peak >= 1,
             "final_half_second_peak": final_peak, "final_half_second_rms": final_rms,
             "final_half_second_effectively_silent": len(final_samples) == 48000 and final_peak <= .00001,
             "listening_review_performed": args.audio_listening_reviewed}
    if peak >= 1:
        errors.append("Decoded AAC audio clips at or above full scale")
    if abs(video_checks["audio_start_seconds"] - video_checks["video_start_seconds"]) > 1 / 48000:
        errors.append("Encoded audio and video stream start times differ")
    # Compare actual decoded AAC against the source mix at zero delay. This checks
    # that the correct dialogue/music track reached the movie without an AV offset.
    reference_path = runtime.repo_path(cues["mix_file"], must_exist=True)
    with wave.open(str(reference_path), "rb") as stream:
        if (stream.getframerate(), stream.getnchannels(), stream.getsampwidth()) != (48000, 2, 2):
            raise ValueError("Reference mix must be 48k stereo PCM16")
        reference = array("h")
        reference.frombytes(stream.readframes(stream.getnframes()))
    if sys.byteorder != "little":
        reference.byteswap()
    if len(samples) < len(reference):
        errors.append("Decoded movie audio is shorter than the source mix")
    source_energy = decoded_energy = product = error_energy = 0.0
    for encoded, original in zip(samples, reference):
        expected = original / 32768
        source_energy += expected * expected
        decoded_energy += encoded * encoded
        product += encoded * expected
        error_energy += (encoded - expected) ** 2
    correlation = product / math.sqrt(max(1e-30, source_energy * decoded_energy))
    snr = 10 * math.log10(max(1e-30, source_energy) / max(1e-30, error_energy))
    audio.update(source_mix=cues["mix_file"], source_mix_sha256=sha256(reference_path),
                 decoded_aac_zero_delay_source_correlation=correlation,
                 decoded_aac_vs_source_snr_db=snr,
                 correct_source_mix_and_zero_delay_verified=correlation >= .985 and snr >= 18)
    if correlation < .985 or snr < 18:
        errors.append("Decoded AAC differs excessively from the source mix at zero delay")
    captions = verify_caption_metadata(project, cues)
    errors.extend(captions["errors"])
    puppet_required = {"frames": 432, "video_seconds": 18, "resolution": [1080, 1920], "fps": 24,
                       "engine": "BLENDER_EEVEE", "static_character_parts": 25, "skeletal_bones": 17,
                       "character_geometry_redraws_per_frame": 0, "character_mesh_animation": False,
                       "background_count": 1, "caption_font": "LuckiestGuy-Regular.ttf"}
    for name, expected in puppet_required.items():
        if project.get(name) != expected:
            errors.append(f"Puppet scene report {name} differs from expected {expected}")
    if delivery.get("status") != "complete" or state.get("render", {}).get("status") != "complete" \
            or state.get("encode", {}).get("status") != "complete":
        errors.append("Queue records do not establish completed rendering and encoding")
    if delivery.get("video") != args.video:
        errors.append("Queue delivery references a different movie")
    video_hash = sha256(video)
    if state.get("encode", {}).get("sha256") != video_hash:
        errors.append("Final movie hash differs from completed queue encoding")
    flat = read_json(edit / "flat_plate_render_time.json")
    if project.get("background_plate") != flat.get("plate_png"):
        errors.append("Puppet scene references a different flat plate")
    plate = runtime.repo_path(flat["plate_png"], must_exist=True)
    if sha256(plate) != flat["sha256"]:
        errors.append("Final flat background plate hash changed after its render")
    protected = protected_assets()
    errors.extend(protected["errors"])
    animation_seconds = float(delivery["render_seconds"])
    final_plate_seconds = float(flat["actual_static_plate_render_seconds"])
    preview = read_json(edit / "cutout_review_render_time.json")
    report = {"schema_version": 1, "episode": "EP009_Wrong_Screen", "status": "passed" if not errors else "failed",
              "checked_utc": datetime.now(timezone.utc).isoformat(), "video": args.video,
              "video_sha256": video_hash, "editable_project": str(project["built_project"]).replace("\\", "/"),
              "media": video_checks, "full_video_and_audio_decode_passed": True,
              "full_decode_seconds": round(decode_seconds, 3), "audio": audio, "captions": captions,
              "puppet": {name: project[name] for name in puppet_required},
              "background_plate": flat["plate_png"], "gpu": delivery.get("gpu"), "render_backend": "Blender queue",
              "actual_render_times": {"animation_render_seconds": animation_seconds,
                  "final_static_flat_plate_render_seconds": final_plate_seconds,
                  "final_plate_plus_animation_render_seconds": animation_seconds + final_plate_seconds,
                  "encoding_seconds": float(delivery["encode_seconds"]),
                  "representative_frame_render_seconds": preview["review_render_seconds"]},
              "representative_render_timing_scope": {"frames": preview["frames"],
                  "note": "Latest measured preview batch only; not a cumulative total of earlier preview work"},
              "unused_3d_background_work": unused_background_work(edit), "protected_sources": protected,
              "visual_review_performed": bool(args.visual_review_note), "visual_review_note": args.visual_review_note or None,
              "encoded_video_visual_review": {"performed": bool(args.encoded_review_frames and args.visual_review_note),
                  "frames": args.encoded_review_frames, "phone_preview_width_px": args.phone_preview_width,
                  "artifact": args.encoded_review_artifact,
                  "scope": "Representative decoded MP4 frames; not a complete motion or phoneme-sync review"},
              "lip_sync_method": cues["lip_sync_method"],
              "limitations": ["Word/amplitude-driven visemes are estimates, not phoneme forced alignment",
                  "Caption geometry is checked against the evaluated project report; actual encoded-frame visual review has the limited scope recorded separately"],
              "verification_elapsed_seconds": round(time.monotonic() - started, 3), "errors": errors}
    if not args.audio_listening_reviewed:
        report["limitations"].append("No audio listening review performed")
    if not args.visual_review_note:
        report["limitations"].append("No final visual/lip-sync review claimed by this verifier")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "video_seconds": video_checks["video_seconds"],
                      "frame_count": video_checks["frame_count"], "render_seconds": animation_seconds,
                      "encode_seconds": delivery["encode_seconds"], "approved_assets_unchanged": protected["approved_asset_count"],
                      "historical_projects_unchanged": protected["historical_episode_project_count"],
                      "errors": errors, "report": relative(output)}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
