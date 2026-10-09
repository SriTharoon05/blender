"""Encode and verify the rendered layered EP008 research short.

Run only after the full animation render has started. The completion marker is
written after the final image and animation timing record are saved.
"""

import hashlib
import json
import math
import shutil
import struct
import subprocess
import time
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EP = ROOT / '02_EPISODES/EP008_Research_Then_Now'
BIN = ROOT / 'tools/vendor/ffmpeg611/ffmpeg-6.1.1-essentials_build/bin'
FPS = 24
FRAMES = 576
DURATION = 24
FINAL = ROOT / '03_FINAL_OUTPUT/YouTube/EP008_Research_Then_Now_1080p24_v001.mp4'
PROJECT = EP / 'blend/EP008_Research_GP_v004.blend'
WAV = EP / 'audio/EP008_Original_Research_48k.wav'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def valid_seconds(value, name):
    value = float(value)
    require(math.isfinite(value) and value >= 0, f'Invalid {name}: {value}')
    return value


def plate_timings(record):
    """Accept a per-plate list or explicit A/B timings from the plate renderer."""
    plates = record.get('plates', [])
    if isinstance(plates, dict):
        plates = [dict(value, name=name) if isinstance(value, dict)
                  else {'name': name, 'render_seconds': value}
                  for name, value in plates.items()]
    if not plates:
        plates = [
            {'name': 'Plate A', 'render_seconds': record['plate_a_seconds']},
            {'name': 'Plate B', 'render_seconds': record['plate_b_seconds']},
        ]
    require(len(plates) == 2, 'Expected two independently rendered Cycles plates')
    details = []
    for index, plate in enumerate(plates):
        seconds = plate.get('render_seconds', plate.get('seconds'))
        detail = {
            'name': plate.get('name', f'Plate {index + 1}'),
            'render_seconds': valid_seconds(seconds, 'Cycles plate duration'),
            'gpu': plate.get('gpu', record.get('gpu', record.get('device'))),
        }
        if plate.get('path'):
            path = Path(plate['path'])
            if not path.is_absolute():
                path = ROOT / path
            with path.open('rb') as handle:
                header = handle.read(24)
            require(header[:8] == b'\x89PNG\r\n\x1a\n' and len(header) == 24,
                    f'Invalid Cycles plate PNG: {path}')
            require(struct.unpack('>2I', header[16:24]) == (1080, 1920),
                    f'Cycles plate must be 1080x1920: {path}')
            detail['path'] = str(path)
            detail['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        details.append(detail)
    total = sum(plate['render_seconds'] for plate in details)
    reported = record.get('total_render_seconds', record.get('render_seconds', total))
    # A combined plate timer may include scene preparation between the stills.
    combined = valid_seconds(reported, 'combined Cycles plate duration')
    require(combined + .05 >= total, 'Combined Cycles time is less than its plate times')
    return details, combined


def main():
    render_log_path = EP / 'edit/render_animation.log'
    while True:
        log = render_log_path.read_text(errors='replace') if render_log_path.exists() else ''
        if 'EP008_RENDER_COMPLETE' in log:
            break
        if 'Traceback' in log or 'EXCEPTION_ACCESS_VIOLATION' in log:
            raise RuntimeError(log[-3000:])
        time.sleep(3)

    folder = EP / 'renders/frames_1080p24'
    pngs = list(folder.glob('EP008_*.png'))
    require(len(pngs) == FRAMES, f'Expected {FRAMES} rendered frames, found {len(pngs)}')
    for frame in range(1, FRAMES + 1):
        path = folder / f'EP008_{frame:06d}.png'
        with path.open('rb') as handle:
            header = handle.read(24)
        require(header[:8] == b'\x89PNG\r\n\x1a\n', f'Invalid PNG signature: {path}')
        require(len(header) == 24 and struct.unpack('>2I', header[16:24]) == (1080, 1920),
                f'Unexpected frame resolution: {path}')

    require(PROJECT.is_file(), f'Missing final Blender project: {PROJECT}')
    with wave.open(str(WAV), 'rb') as sound:
        wav_details = {
            'sample_rate': sound.getframerate(),
            'channels': sound.getnchannels(),
            'sample_width': sound.getsampwidth(),
            'duration_seconds': sound.getnframes() / sound.getframerate(),
        }
    require(wav_details['sample_rate'] == 48000 and wav_details['channels'] == 2,
            'Original soundtrack must be 48 kHz stereo')
    require(abs(wav_details['duration_seconds'] - DURATION) < 1 / 48000,
            'Original soundtrack must be exactly 24 seconds')

    FINAL.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    with (EP / 'edit/encode.log').open('w') as log:
        subprocess.run([
            str(BIN / 'ffmpeg.exe'), '-hide_banner', '-y',
            '-framerate', str(FPS), '-start_number', '1',
            '-i', str(folder / 'EP008_%06d.png'), '-i', str(WAV),
            '-frames:v', str(FRAMES), '-t', str(DURATION),
            '-c:v', 'h264_nvenc', '-preset', 'p4', '-rc', 'vbr',
            '-cq', '18', '-b:v', '0', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
            '-movflags', '+faststart', str(FINAL),
        ], stdout=log, stderr=subprocess.STDOUT, check=True)
    encode_seconds = time.perf_counter() - started

    probe = json.loads(subprocess.check_output([
        str(BIN / 'ffprobe.exe'), '-v', 'error', '-show_streams',
        '-show_format', '-of', 'json', str(FINAL),
    ]))
    video = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
    audio = next(stream for stream in probe['streams'] if stream['codec_type'] == 'audio')
    require((video['width'], video['height'], video['avg_frame_rate'], int(video['nb_frames']))
            == (1080, 1920, '24/1', FRAMES), 'Unexpected video dimensions, fps, or frame count')
    require(video['codec_name'] == 'h264' and video['pix_fmt'] == 'yuv420p',
            'Video must use compatible H.264/yuv420p encoding')
    require(abs(float(probe['format']['duration']) - DURATION) < .05,
            'Unexpected final video duration')
    require(audio['sample_rate'] == '48000' and audio['channels'] == 2,
            'Final audio must be 48 kHz stereo')
    require(abs(float(audio.get('duration', DURATION)) - DURATION) < .05,
            'Unexpected final audio duration')
    with (EP / 'edit/decode_check.log').open('w') as log:
        subprocess.run([
            str(BIN / 'ffmpeg.exe'), '-v', 'error', '-xerror', '-i',
            str(FINAL), '-f', 'null', '-',
        ], stdout=log, stderr=subprocess.STDOUT, check=True)

    hashes = json.loads((EP / 'edit/protected_hashes.json').read_text())
    require(bool(hashes), 'Protected library/template/episode hashes must be present')
    for relative_path, expected in hashes.items():
        actual = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        require(actual == expected, f'Protected file changed: {relative_path}')

    render = json.loads((EP / 'edit/render_time.json').read_text())
    plate_record = json.loads((EP / 'edit/plate_render_time.json').read_text())
    project = json.loads((EP / 'edit/project_verification.json').read_text())
    gpu = render.get('gpu', render.get('actual_gpu'))
    require('1650' in str(gpu), f'Unexpected animation rendering GPU: {gpu}')
    animation_seconds = valid_seconds(render['render_seconds'], 'animation render duration')
    plates, plate_seconds = plate_timings(plate_record)
    for plate in plates:
        require('1650' in str(plate['gpu']), f'Unexpected Cycles plate GPU: {plate["gpu"]}')

    shutil.copy2(FINAL, EP / 'renders' / FINAL.name)
    report = {
        'status': 'Complete and verified',
        'video': str(FINAL),
        'project': str(PROJECT),
        'duration_seconds': DURATION,
        'resolution': [1080, 1920],
        'fps': FPS,
        'frames': FRAMES,
        'pipeline': 'Two static Cycles GPU background plates, transparent native Grease Pencil Eevee animation, compositor alpha-over',
        'renderer_gpu': gpu,
        'cycles_plate_timings': plates,
        'cycles_still_render_seconds': plate_seconds,
        'eevee_animation_render_seconds': animation_seconds,
        'render_seconds': plate_seconds + animation_seconds,
        'encode_seconds': encode_seconds,
        'render_and_encode_seconds': plate_seconds + animation_seconds + encode_seconds,
        'video_codec': video['codec_name'],
        'audio_codec': audio['codec_name'],
        'encoder': 'h264_nvenc / NVIDIA GTX 1650 Ti',
        'audio': 'Original library ambience/piano, page and pencil foley, record scratch, notification spam, frantic typing, rabbit-hole bass, overload thump, and error beep',
        'audio_source': wav_details,
        'project_verification': project,
        'full_decode_passed': True,
        'protected_files_unchanged': len(hashes),
        'file_size_bytes': FINAL.stat().st_size,
        'video_sha256': hashlib.sha256(FINAL.read_bytes()).hexdigest(),
    }
    (EP / 'edit/delivery_verification.json').write_text(json.dumps(report, indent=2))
    print('EP008_DELIVERY_COMPLETE', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
