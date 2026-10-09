"""Original, sample-accurate EP007 sound design; no external audio samples."""
import hashlib
import json
import wave
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / '02_EPISODES' / 'EP007_Alarm_Expectation_Reality' / 'audio'
DEST.mkdir(parents=True, exist_ok=True)
SR, FPS, DURATION = 48000, 24, 18
T = np.arange(SR * DURATION) / SR
AUDIO = np.zeros((len(T), 2), dtype=np.float64)
RNG = np.random.default_rng(7007)


def envelope(t, attack=.01, release=.06):
    """Smooth onset and release for a time-localized sample array."""
    duration = (len(t) - 1) / SR
    return np.sin(np.minimum(t / attack, 1) * np.pi / 2) ** 2 * np.sin(
        np.minimum(np.maximum(duration - t, 0) / release, 1) * np.pi / 2
    ) ** 2


def place(signal, at, gain=1, pan=0, delay=0):
    first = round(at * SR)
    count = min(len(signal), len(T) - first)
    if count <= 0:
        return
    signal = signal[:count] * gain
    # Equal-power stereo image, with only a short reflection on diffuse sounds.
    angle = (pan + 1) * np.pi / 4
    AUDIO[first:first + count, 0] += signal * np.cos(angle)
    AUDIO[first:first + count, 1] += signal * np.sin(angle)
    if delay:
        reflection = round(delay * SR)
        reflected_count = min(count, len(T) - first - reflection)
        AUDIO[first + reflection:first + reflection + reflected_count, 0] += signal[:reflected_count] * .10 * np.sin(angle)
        AUDIO[first + reflection:first + reflection + reflected_count, 1] += signal[:reflected_count] * .10 * np.cos(angle)


def time_local(duration):
    return np.arange(round(duration * SR)) / SR


def filtered_noise(duration, low, high):
    n = round(duration * SR)
    noise = RNG.normal(size=n)
    freq = np.fft.rfftfreq(n, 1 / SR)
    weights = np.clip((freq - low) / max(low * .4, 1), 0, 1) * np.clip((high - freq) / max(high * .2, 1), 0, 1)
    noise = np.fft.irfft(np.fft.rfft(noise) * weights, n=n)
    return noise / max(np.std(noise), 1e-8)


# Quiet airy morning, with gentle major-chord overtones and a little air.
u = time_local(6)
pad = np.zeros(len(u))
for frequency, weight in [(196, .9), (246.94, .65), (293.66, .65), (392, .22)]:
    pad += weight * np.sin(2 * np.pi * frequency * u + .002 * np.sin(u * 1.4))
pad = pad * .0048 + filtered_noise(6, 300, 3500) * .0012
pad *= envelope(u, attack=.5, release=.13)
place(pad, 0, pan=-.08, delay=.037)


def bird(at, frequency, duration, pan):
    u = time_local(duration)
    # A curved upward/downward whistle, paired with a quieter breathy harmonic.
    frequency_curve = frequency + 950 * np.sin(np.pi * u / duration) + 180 * np.sin(2 * np.pi * 22 * u)
    phase = 2 * np.pi * np.cumsum(frequency_curve) / SR
    song = (np.sin(phase) + .10 * np.sin(2 * phase)) * envelope(u, .009, .045)
    place(song, at, gain=.028, pan=pan, delay=.026)


bird_cues = [(0.15, 2200, .16, -.65), (.41, 2600, .13, -.65), (1.12, 2900, .20, .6),
             (1.41, 2450, .14, .6), (2.18, 2100, .17, -.5), (2.43, 2700, .13, -.5),
             (3.67, 2550, .21, .65), (3.98, 2950, .14, .65), (5.05, 2350, .16, -.6),
             (5.29, 2750, .14, -.6), (5.59, 2850, .17, .4)]
for cue in bird_cues:
    bird(*cue)


def sparkle(at, frequencies, gain):
    for index, frequency in enumerate(frequencies):
        u = time_local(.76)
        bell = (np.sin(2 * np.pi * frequency * u) + .24 * np.sin(2 * np.pi * frequency * 2.001 * u))
        bell *= np.exp(-u * 5.4) * envelope(u, .002, .08)
        place(bell, at + index * .055, gain=gain, pan=(index - 1) * .2, delay=.045)


sparkle(3, [1046.5, 1318.51, 1567.98], .030)
sparkle(4.5, [784, 1046.5, 1318.51, 1567.98], .024)
# Exact hard edit: not a reverb tail after the expectation sequence.
AUDIO[6 * SR:7 * SR] = 0


HORN_TIMES = [7, 8.75, 10.25, 11.75, 13.25]


def foghorn(at, duration, gain):
    u = time_local(duration)
    # Two detuned low brass pipes with octave/odd-harmonic richness.
    pitch = 82 + 13 * (1 - np.exp(-u * 21)) + 1.4 * np.sin(2 * np.pi * 4.2 * u)
    phase = 2 * np.pi * np.cumsum(pitch) / SR
    signal = np.zeros(len(u))
    for harmonic, weight in [(1, 1), (2, .37), (3, .28), (4, .14), (5, .16), (7, .085), (9, .042)]:
        signal += weight * np.sin(harmonic * phase)
        signal += weight * .27 * np.sin(harmonic * phase * 1.012 + .4)
    signal += filtered_noise(duration, 200, 1900) * .045
    # Soft saturation makes a large round comedic horn instead of hard clipping.
    signal = np.tanh(signal * .8) * envelope(u, .007, .025)
    place(signal, at, gain=gain, pan=.12, delay=.014)


for index, at in enumerate(HORN_TIMES):
    foghorn(at, .95 if index < 4 else .75, .80 + index * .035)


# Clock's loose casing and feet rattle beneath every horn; no unrelated ambience.
for at in np.arange(7, 14, 1 / 24):
    u = time_local(.034)
    shake = (filtered_noise(.034, 1000, 11000) * .52 + np.sin(2 * np.pi * 1750 * u) * .23)
    shake *= np.exp(-u * 105) * envelope(u, .0008, .004)
    place(shake, float(at), gain=.090, pan=.35)


SPRING_TIME = 173 / 24  # Frame 174: first frame is t=0.
u = time_local(.68)
pitch = 120 + 1100 * np.exp(-u * 7.8)
phase = 2 * np.pi * np.cumsum(pitch) / SR
spring = (np.sin(phase) + .20 * np.sin(phase * 2.04)) * np.exp(-u * 5.8)
spring *= (.72 + .28 * np.cos(2 * np.pi * 19 * u)) * envelope(u, .002, .025)
place(spring, SPRING_TIME, gain=.24, pan=-.18)


# All mechanical alarm sound cuts sample-exactly at the clock smack at 14s.
AUDIO[14 * SR:] = 0
# Original low human-like voiced groan, separately layered after the alarm edit.
u = time_local(1.65)
pitch = 73 - 12 * u / 1.65 + 2 * np.sin(u * 13)
phase = 2 * np.pi * np.cumsum(pitch) / SR
voice = np.zeros(len(u))
for harmonic in range(1, 18):
    # Broad vowel formants around 260 and 690Hz, with a weak low fundamental.
    hz = harmonic * 67
    weight = (.16 + 1.7 * np.exp(-((hz - 260) / 130) ** 2) + .85 * np.exp(-((hz - 690) / 210) ** 2)) / harmonic
    voice += weight * np.sin(harmonic * phase + .07 * harmonic * np.sin(u * 9))
voice += filtered_noise(1.65, 80, 1000) * .07
voice = np.tanh(voice * 1.1) * envelope(u, .09, .30)
voice *= .80 + .20 * np.sin(u * 28)
place(voice, 13, gain=.14, pan=-.12)


# Pillow absorbs the fall: rounded bass thump and a little cloth, no sharp crack.
u = time_local(.28)
thud = np.sin(2 * np.pi * (72 * u - 28 * u ** 2)) * np.exp(-u * 24)
thud += filtered_noise(.28, 70, 1800) * .20 * np.exp(-u * 35)
thud *= envelope(u, .006, .035)
place(thud, 16.75, gain=.17, pan=-.1)
AUDIO[15 * SR:round(16.75 * SR)] = 0
AUDIO[round(17.1 * SR):] = 0


# Single overall normalization preserves the strong anticipation/punchline contrast.
target_peak = 10 ** (-1 / 20)
scale = target_peak / np.max(np.abs(AUDIO))
AUDIO *= scale
pcm = np.rint(np.clip(AUDIO, -1, 1) * 32767).astype('<i2')
path = DEST / 'EP007_Original_Alarm_Expectation_Reality_v001.wav'
with wave.open(str(path), 'wb') as stream:
    stream.setnchannels(2)
    stream.setsampwidth(2)
    stream.setframerate(SR)
    stream.writeframes(pcm.tobytes())


def cue(at, name, **details):
    return {'seconds': at, 'frame': round(at * FPS) + 1, 'sample': round(at * SR), 'event': name, **details}


sheet = {
    'source': 'Entirely original deterministic synthesis; no downloaded samples.',
    'file': path.name, 'sample_rate_hz': SR, 'channels': 2, 'pcm_bits': 16,
    'duration_seconds': DURATION, 'sample_count': len(T), 'frames': FPS * DURATION,
    'peak_dbfs': float(20 * np.log10(np.max(np.abs(AUDIO)))),
    'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'cue_events': [cue(0, 'Quiet airy morning and bird chirps begin'),
                   cue(3, 'Dreamy wake-up sparkle chime'),
                   cue(4.5, 'Happy expectation sparkle chime'),
                   cue(6, 'Morning stops hard; silence until first horn'),
                   *[cue(at, 'Comedic foghorn burst and clock rattle') for at in HORN_TIMES],
                   cue(SPRING_TIME, 'Cartoon spring launch'),
                   cue(13, 'Low original zombie groan', end_seconds=14.65),
                   cue(14, 'All alarm and rattles stop abruptly'),
                   cue(15, 'Dead silence holds'),
                   cue(16.75, 'Soft pillow landing thud'),
                   cue(17.1, 'Final digital silence')],
    'verified_silent_intervals_seconds': [[6, 7], [15, 16.75], [17.1, 18]],
    'bird_chirp_times_seconds': [entry[0] for entry in bird_cues],
    'intro_rms_dbfs': float(20 * np.log10(np.sqrt(np.mean(AUDIO[:6 * SR] ** 2)))),
    'punchline_rms_dbfs': float(20 * np.log10(np.sqrt(np.mean(AUDIO[7 * SR:14 * SR] ** 2)))),
}
for start, end in sheet['verified_silent_intervals_seconds']:
    assert np.max(np.abs(pcm[round(start * SR):round(end * SR)])) == 0
(DEST / 'audio_cue_sheet.json').write_text(json.dumps(sheet, indent=2), encoding='utf-8')
print(json.dumps({'status': 'EP007_AUDIO_READY', 'wav': str(path), 'sheet': str(DEST / 'audio_cue_sheet.json'),
                  'peak_dbfs': sheet['peak_dbfs'], 'intro_rms_dbfs': sheet['intro_rms_dbfs'],
                  'punchline_rms_dbfs': sheet['punchline_rms_dbfs']}, indent=2))
