"""Deterministic, entirely original EP008 sound design, synchronized at 48 kHz."""
import hashlib
import json
import wave
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / '02_EPISODES/EP008_Research_Then_Now/audio'
DEST.mkdir(parents=True, exist_ok=True)
SR, FPS, DURATION = 48000, 24, 24
TOTAL = SR * DURATION
AUDIO = np.zeros((TOTAL, 2), dtype=np.float64)
RNG = np.random.default_rng(8008)
EVENTS = []


def time_local(duration):
    return np.arange(round(duration * SR)) / SR


def envelope(t, attack=.004, release=.035):
    duration = (len(t) - 1) / SR
    return np.sin(np.clip(t / attack, 0, 1) * np.pi / 2) ** 2 * np.sin(
        np.clip((duration - t) / release, 0, 1) * np.pi / 2
    ) ** 2


def filtered_noise(duration, low, high):
    count = round(duration * SR)
    noise = RNG.normal(size=count)
    freq = np.fft.rfftfreq(count, 1 / SR)
    taper = np.clip((freq - low) / max(low * .4, 1), 0, 1)
    taper *= np.clip((high - freq) / max(high * .2, 1), 0, 1)
    result = np.fft.irfft(np.fft.rfft(noise) * taper, n=count)
    return result / max(float(np.std(result)), 1e-8)


def place(signal, at, gain=1, pan=0, reflection=0):
    start = round(at * SR)
    count = min(len(signal), TOTAL - start)
    if count <= 0:
        return
    signal = signal[:count] * gain
    theta = (pan + 1) * np.pi / 4
    AUDIO[start:start + count, 0] += signal * np.cos(theta)
    AUDIO[start:start + count, 1] += signal * np.sin(theta)
    if reflection:
        delay = round(reflection * SR)
        reflected_count = min(count, TOTAL - start - delay)
        if reflected_count > 0:
            reflected = signal[:reflected_count] * .11
            AUDIO[start + delay:start + delay + reflected_count, 0] += reflected * np.sin(theta)
            AUDIO[start + delay:start + delay + reflected_count, 1] += reflected * np.cos(theta)


def cue(at, name, **details):
    event = {'seconds': round(float(at), 6), 'frame': round(at * FPS) + 1,
             'sample': round(at * SR), 'event': name, **details}
    EVENTS.append(event)
    return event


# Expectation: a softly ventilated library, far-away paper movement and felt piano.
u = time_local(9)
room = filtered_noise(9, 95, 1600) * .0008
room += filtered_noise(9, 250, 1900) * .00034 * (.5 + .5 * np.sin(u * 2.3) ** 2)
room += .0007 * np.sin(2 * np.pi * 60 * u)
room *= envelope(u, .2, .012)
place(room, 0, pan=-.12, reflection=.035)
cue(0, 'Faint library air and original felt-piano phrase begin', end_seconds=9)


def piano_note(at, midi, gain=.017, duration=2.2, pan=0):
    u = time_local(duration)
    hz = 440 * 2 ** ((midi - 69) / 12)
    signal = np.zeros(len(u))
    # Slightly inharmonic string partials and felt hammer noise; no recorded piano.
    for partial, weight in [(1, 1), (2, .38), (3, .12), (4, .047), (5, .017)]:
        phase = 2 * np.pi * hz * partial * np.sqrt(1 + .00002 * partial ** 2) * u
        decay = np.exp(-u * (.95 + .23 * partial))
        signal += np.sin(phase) * weight * decay
        signal += np.sin(phase * 1.0009 + .03) * weight * .16 * decay
    signal += filtered_noise(duration, 600, 5500) * .02 * np.exp(-u * 95)
    signal *= envelope(u, .005, .18)
    place(signal, at, gain=gain, pan=pan, reflection=.028)


for at, chord in [(0, [48, 55, 59, 64]), (2.1, [45, 52, 55, 60]),
                  (4.2, [41, 48, 52, 57]), (6.3, [43, 50, 53, 59])]:
    for index, midi in enumerate(chord):
        piano_note(at + index * .11, midi, .015 if index else .020,
                   duration=min(2.1, 9 - at - index * .11), pan=(index - 1.5) * .14)
for at, midi in [(1.2, 67), (1.6, 64), (3.2, 64), (3.65, 60),
                 (5.3, 65), (5.7, 64), (7.4, 62), (7.8, 59)]:
    piano_note(at, midi, .010, duration=min(1.4, 9 - at), pan=.24)


def page_flip(at, gain=.032, pan=-.3):
    duration = .38
    u = time_local(duration)
    # A sheet rises, flutters, and lands: three delicate filtered noise pulses.
    motion = np.exp(-((u - .09) / .06) ** 2) + .7 * np.exp(-((u - .24) / .07) ** 2)
    signal = filtered_noise(duration, 700, 7000) * motion
    signal += .2 * filtered_noise(duration, 130, 750) * np.exp(-u * 16)
    signal *= envelope(u, .004, .035)
    place(signal, at, gain=gain, pan=pan)
    cue(at, 'Book page flip', end_seconds=round(at + duration, 3))


page_flip(1)
page_flip(2.6, .029, -.15)
u = time_local(1.28)
stroke = .35 + .65 * np.sin(2 * np.pi * 4.3 * u) ** 8
pencil = filtered_noise(1.28, 1700, 10500) * stroke * envelope(u, .009, .04)
place(pencil, 3, gain=.011, pan=.18)
cue(3, 'Pencil scribbles on paper', end_seconds=4.28)

for at in [5, 7]:
    u = time_local(.045)
    tick = filtered_noise(.045, 1200, 6000) * np.exp(-u * 150)
    tick += .30 * np.sin(2 * np.pi * 1620 * u) * np.exp(-u * 100)
    tick *= envelope(u, .0006, .005)
    place(tick, at, gain=.022, pan=-.55)
    cue(at, 'Quiet clock tick accent')

for index, frequency in enumerate([784, 1046.5, 1318.51]):
    u = time_local(.63)
    chime = (np.sin(2 * np.pi * frequency * u) + .17 * np.sin(2 * np.pi * frequency * 2.003 * u))
    chime *= np.exp(-u * 6.0) * envelope(u, .003, .08)
    place(chime, 8 + index * .07, gain=.029, pan=.10, reflection=.04)
cue(8, 'Subtle three-note success chime')

# The entire calm bed cuts at the exact hard picture edit, with no room tail.
AUDIO[9 * SR:] = 0
u = time_local(.43)
speed = 1.25 - 2.3 * u / .43 + .22 * np.sin(2 * np.pi * 14 * u)
phase = 2 * np.pi * np.cumsum(710 * speed) / SR
scratch = (.45 * np.sin(phase) + .22 * np.sin(phase * 2.3))
scratch += filtered_noise(.43, 850, 6900) * (.34 + .26 * np.sin(u * 105) ** 2)
scratch *= np.exp(-u * 2.2) * envelope(u, .001, .020)
place(scratch, 9, gain=.32, pan=0)
cue(9, 'Exact record scratch and abrupt modern-workstation cut', end_seconds=9.43)


def bass_hit(at, gain, duration=.62, pan=0):
    u = time_local(duration)
    pitch = 40 + 82 * np.exp(-u * 20)
    phase = 2 * np.pi * np.cumsum(pitch) / SR
    signal = np.sin(phase) * np.exp(-u * 6.5)
    signal += .21 * np.sin(phase * 1.99) * np.exp(-u * 15)
    signal += .16 * filtered_noise(duration, 45, 1400) * np.exp(-u * 33)
    signal = np.tanh(signal * 1.05) * envelope(u, .0014, .035)
    place(signal, at, gain=gain, pan=pan)


bass_hit(9, .27, .54)


def notification(at, index):
    duration = .35
    u = time_local(duration)
    variants = [(880, 1320), (1046.5, 1567.98), (1174.66, 1760), (987.77, 1481.66)]
    base, upper = variants[index % len(variants)]
    signal = np.sin(2 * np.pi * base * u) * np.exp(-u * 15)
    signal += .32 * np.sin(2 * np.pi * base * 2.001 * u) * np.exp(-u * 24)
    v = np.maximum(u - .052, 0)
    signal += .64 * np.sin(2 * np.pi * upper * v) * np.exp(-v * 14) * (u >= .052)
    signal *= envelope(u, .0018, .045)
    escalation = .062 + .077 * np.clip((at - 10) / 12, 0, 1)
    pan = [-.48, .48, -.18, .20][index % 4]
    place(signal, at, gain=escalation, pan=pan, reflection=.019)


notification_times = []
at, index = 10., 0
while at < 21.91:
    at = round(at * FPS) / FPS  # Popups and pings share native animation frames.
    notification_times.append(at)
    notification(at, index)
    cue(at, 'Notification ping', sequence=index + 1,
        intensity=round(.35 + .65 * (at - 10) / 12, 3))
    interval = max(.17, .88 * np.exp(-.19 * (at - 10)))
    at += interval
    index += 1


# Small phone motor bursts under the notification storm.
for at in [10, 12.5, 15.5, 18.75, 20.5]:
    u = time_local(.28)
    vibration = (np.sin(2 * np.pi * 142 * u) + .20 * np.sin(2 * np.pi * 286 * u))
    vibration *= (.4 + .6 * np.sin(2 * np.pi * 22 * u) ** 2) * envelope(u, .007, .030)
    place(vibration, at, gain=.023, pan=.30)
    cue(at, 'Phone vibration under notifications')


def keyboard_key(at, index, gain):
    duration = .065
    u = time_local(duration)
    body_hz = 280 + (index % 6) * 87
    key = filtered_noise(duration, 1600, 10000) * .53 * np.exp(-u * 110)
    key += np.sin(2 * np.pi * body_hz * u) * .50 * np.exp(-u * 70)
    key += .24 * np.sin(2 * np.pi * 2450 * u) * np.exp(-u * 155)
    key *= envelope(u, .0005, .008)
    place(key, at, gain=gain, pan=-.18 + .12 * (index % 4))


key_times = []
at, index = 13., 0
while at < 17:
    key_times.append(round(at, 6))
    keyboard_key(at, index, .036 + .024 * (at - 13) / 4)
    rate = 7 + 12 * (at - 13) / 4
    at += (1 / rate) * RNG.uniform(.72, 1.20)
    index += 1
cue(13, 'Frantic keyboard clatter starts and accelerates', end_seconds=17,
    keystroke_times_seconds=key_times)


# A restrained original electronic tension sting swells below the concrete foley.
u = time_local(9.7)
pitch = 105 * 2 ** (u / 9.7 * 1.4)
phase = 2 * np.pi * np.cumsum(pitch) / SR
tension = np.sin(phase) * .50 + np.sin(phase * 1.013) * .26
tension += .20 * np.sin(phase * 2) + .10 * np.sin(phase * 3.005)
pulse = .16 + .84 * (np.sin(2 * np.pi * (1.3 * u + .20 * u ** 2)) * .5 + .5) ** 3
tension *= pulse * (.10 + .90 * u / 9.7) * envelope(u, .3, .08)
place(tension, 12, gain=.026, pan=0)
cue(12, 'Original rising electronic tension sting', end_seconds=21.7)

bass_hit(18, .65, .72)
cue(18, 'Rabbit-hole impact bass hit')


def mouse_click(at, index, gain):
    duration = .028
    u = time_local(duration)
    click = filtered_noise(duration, 1400, 9000) * .58 * np.exp(-u * 190)
    click += .38 * np.sin(2 * np.pi * (1380 + index % 4 * 170) * u) * np.exp(-u * 140)
    click *= envelope(u, .0003, .003)
    place(click, at, gain=gain, pan=.20 + .12 * (index % 2))


click_times = []
at, index = 18., 0
while at < 21.91:
    click_times.append(round(at, 6))
    mouse_click(at, index, .050 + .025 * (at - 18) / 4)
    at += 1 / (10 + 11 * (at - 18) / 4) * RNG.uniform(.74, 1.23)
    index += 1
cue(18, 'Rapid mouse clicks build under overlapping notifications', end_seconds=22,
    click_times_seconds=click_times)

# Exact punchline silence removes all residual notification and tension tails.
AUDIO[22 * SR:23 * SR] = 0
cue(22, 'Complete digital silence for camera-facing source question', end_seconds=23)
bass_hit(23, .81, .50)
cue(23, 'Final information-overload bass hit')

# Loose papers vibrate before the full collapse; stop before the desk landing.
u = time_local(.53)
paper = filtered_noise(.53, 1000, 8300) * (.20 + .80 * np.sin(2 * np.pi * 29 * u) ** 6)
paper *= envelope(u, .012, .060)
place(paper, 23.13, gain=.053, pan=.18)
cue(23.13, 'Information-overload paper rattle', end_seconds=23.66)

u = time_local(.20)
pitch = 70 - 26 * u / .20
phase = 2 * np.pi * np.cumsum(pitch) / SR
desk_thump = np.sin(phase) * np.exp(-u * 23)
desk_thump += .25 * filtered_noise(.20, 110, 2400) * np.exp(-u * 37)
desk_thump *= envelope(u, .0012, .025)
place(desk_thump, 23.75, gain=.40, pan=-.08)
cue(23.75, 'Character collapse and rounded desk thump', end_seconds=23.95)

# Tiny descending two-tone error deliberately fits inside the 24-second video.
for at, hz, duration in [(23.87, 587.33, .048), (23.922, 391.995, .058)]:
    u = time_local(duration)
    beep = (np.sin(2 * np.pi * hz * u) + .12 * np.sin(2 * np.pi * hz * 3 * u))
    beep *= envelope(u, .002, .006)
    place(beep, at, gain=.065, pan=.06)
cue(23.87, 'Tiny sad descending keyboard error', end_seconds=23.98)
AUDIO[round(23.98 * SR):] = 0

# Normalize once for a -1 dBFS peak, retaining the quiet setup/loud reality contrast.
target_peak = 10 ** (-1 / 20)
scale = target_peak / np.max(np.abs(AUDIO))
AUDIO *= scale
pcm = np.rint(AUDIO * 32767).astype('<i2')
path = DEST / 'EP008_Original_Research_48k.wav'
with wave.open(str(path), 'wb') as stream:
    stream.setnchannels(2)
    stream.setsampwidth(2)
    stream.setframerate(SR)
    stream.writeframes(pcm.tobytes())


def rms_db(start, end):
    portion = pcm[round(start * SR):round(end * SR)].astype(np.float64) / 32767
    rms = np.sqrt(np.mean(portion ** 2))
    return float(20 * np.log10(max(rms, 1e-12)))


with wave.open(str(path), 'rb') as stream:
    assert stream.getnframes() == TOTAL
    assert stream.getframerate() == SR
    assert stream.getnchannels() == 2 and stream.getsampwidth() == 2
    assert stream.getnframes() / stream.getframerate() == DURATION
for start, end in [(22, 23), (23.98, 24)]:
    assert np.max(np.abs(pcm[round(start * SR):round(end * SR)])) == 0
assert np.max(np.abs(pcm.astype(np.int32))) < 32767

sheet = {
    'source': 'Entirely original deterministic synthesis. No copyrighted or downloaded samples.',
    'file': path.name, 'sample_rate_hz': SR, 'channels': 2, 'pcm_bits': 16,
    'duration_seconds': DURATION, 'sample_count': TOTAL,
    'fps': FPS, 'video_frames': DURATION * FPS,
    'peak_dbfs': float(20 * np.log10(np.max(np.abs(pcm.astype(np.int32))) / 32767)),
    'setup_rms_dbfs': rms_db(0, 9), 'reality_rms_dbfs': rms_db(9, 22),
    'frame_convention': 'Frame 1 is t=0. Event frame is nearest rendered frame: round(seconds*24)+1.',
    'cue_events': sorted(EVENTS, key=lambda event: event['seconds']),
    'notification_times_seconds': notification_times,
    'notification_frames': [round(at * FPS) + 1 for at in notification_times],
    'verified_silent_intervals_seconds': [[22, 23], [23.98, 24]],
    'collapse_time_seconds': 23.75, 'collapse_frame': 571,
    'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
}
sheet_path = DEST / 'audio_cue_sheet.json'
sheet_path.write_text(json.dumps(sheet, indent=2), encoding='utf-8')
print(json.dumps({'status': 'EP008_AUDIO_READY', 'wav': str(path), 'sheet': str(sheet_path),
                  'duration_seconds': DURATION, 'peak_dbfs': sheet['peak_dbfs'],
                  'setup_rms_dbfs': sheet['setup_rms_dbfs'], 'reality_rms_dbfs': sheet['reality_rms_dbfs'],
                  'notification_count': len(notification_times)}, indent=2))
