"""Server-side Gemini TTS and Groq STT with redacted, rate-aware key pools.

Credentials come only from the environment or an explicitly supplied ignored .env.
No SDK or Blender dependency. A 429 cools the entire provider pool, since providers
enforce project/organization limits rather than separate per-key quotas.
"""
from __future__ import annotations

import base64
import email.utils
import io
import json
import os
from pathlib import Path
import random
import re
import time
import urllib.error
import urllib.request
import uuid
import wave


class SpeechAPIError(RuntimeError):
    """A safe error containing no URL, headers, response body or credential."""


class HTTPFailure(SpeechAPIError):
    def __init__(self, status: int, retry_after: float = 0, code: str = ""):
        self.status = status
        self.retry_after = max(0.0, retry_after)
        code = code.upper()
        known_codes = {"DAILY_QUOTA_EXCEEDED", "BILLING_DISABLED", "INSUFFICIENT_QUOTA",
                       "INVALID_API_KEY", "PERMISSION_DENIED", "RESOURCE_EXHAUSTED",
                       "RATE_LIMIT_EXCEEDED", "INVALID_ARGUMENT", "NOT_FOUND",
                       "INTERNAL", "UNAVAILABLE", "UNAUTHENTICATED"}
        self.code = code if code in known_codes else ""
        super().__init__(f"Speech provider HTTP {status}" + (f" ({self.code})" if self.code else ""))


def load_key_pools(env_file: str | Path | None = None) -> dict[str, list[str]]:
    """Read only the two named pools, without executing shell/.env contents."""
    values = {}
    if env_file and Path(env_file).is_file():
        for line in Path(env_file).read_text(encoding="utf-8-sig").splitlines():
            match = re.match(r"^\s*(?:export\s+)?(GEMINI_API_KEYS|GROQ_API_KEYS)\s*=\s*(.*?)\s*$", line)
            if match:
                value = match.group(2)
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                values[match.group(1)] = value
    result = {}
    for name in ("GEMINI_API_KEYS", "GROQ_API_KEYS"):
        value = os.environ.get(name) or values.get(name, "")
        result[name] = list(dict.fromkeys(key.strip() for key in value.split(",") if key.strip()))
    return result


def retry_after_seconds(value: str | None, *, now: float | None = None) -> float:
    if not value:
        return 0.0
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            date = email.utils.parsedate_to_datetime(value)
            return max(0.0, date.timestamp() - (time.time() if now is None else now))
        except (TypeError, ValueError, OverflowError):
            return 0.0


class KeyPool:
    def __init__(self, keys, *, start_index=None, clock=time.monotonic, sleeper=time.sleep):
        self._keys = tuple(dict.fromkeys(k.strip() for k in keys if k.strip()))
        if not self._keys:
            raise SpeechAPIError("No configured keys for this speech provider")
        self._cursor = (random.SystemRandom().randrange(len(self._keys)) if start_index is None
                        else start_index % len(self._keys))
        self._cooldowns = [0.0] * len(self._keys)
        self._disabled = set()
        self._provider_cooldown = 0.0
        self._clock, self._sleep = clock, sleeper

    def __repr__(self):
        return f"KeyPool(configured={len(self._keys)}, disabled={len(self._disabled)})"

    def call(self, operation, *, max_attempts=8, max_wait=180.0):
        """Rotate each request's starting key, retry transient failures safely.

        Auth failures disable that key. 5xx/transport errors cool that key.
        Rate limits cool every key before retrying; long daily quotas stop rather
        than cycling accounts. Runtime wait budget is separate from HTTP timeout.
        """
        deadline = self._clock() + max_wait
        last_status = None
        for attempt in range(max_attempts):
            active = [i for i in range(len(self._keys)) if i not in self._disabled]
            if not active:
                raise SpeechAPIError("All configured speech keys failed authentication")
            now = self._clock()
            ready = [i for i in active if max(self._cooldowns[i], self._provider_cooldown) <= now]
            if not ready:
                wait = min(max(self._cooldowns[i], self._provider_cooldown) for i in active) - now
                if now + wait > deadline:
                    raise SpeechAPIError(f"Speech provider cooldown exceeds retry budget ({wait:.0f}s remaining)")
                self._sleep(wait)
                now = self._clock()
                ready = [i for i in active if max(self._cooldowns[i], self._provider_cooldown) <= now]
            index = next((i for offset in range(len(self._keys))
                          if (i := (self._cursor + offset) % len(self._keys)) in ready), ready[0])
            self._cursor = (index + 1) % len(self._keys)
            try:
                return operation(self._keys[index])
            except HTTPFailure as exc:
                last_status = exc.status
                if exc.status in (401, 403):
                    self._disabled.add(index)
                elif exc.status == 429:
                    delay = max(exc.retry_after, min(60.0, 2.0 ** (attempt + 1)))
                    self._provider_cooldown = self._clock() + delay
                    # Explicit daily/billing quota exhaustion is not a transient failure.
                    if exc.code in ("DAILY_QUOTA_EXCEEDED", "BILLING_DISABLED", "INSUFFICIENT_QUOTA"):
                        raise SpeechAPIError("Speech provider account quota exhausted; wait for its reset") from None
                elif exc.status >= 500 or exc.status in (408, 409):
                    self._cooldowns[index] = self._clock() + min(30.0, 2.0 ** (attempt + 1))
                else:
                    raise SpeechAPIError(str(exc)) from None
            except (TimeoutError, ConnectionError, urllib.error.URLError):
                last_status = "transport"
                self._cooldowns[index] = self._clock() + min(30.0, 2.0 ** (attempt + 1))
        raise SpeechAPIError(f"Speech provider failed after {max_attempts} attempts (last status {last_status})")


def request_json(url: str, *, headers: dict, body: bytes | None = None, timeout=120.0):
    request = urllib.request.Request(url, data=body, headers={"User-Agent": "BlenderProductionSpeech/1.0", **headers},
                                     method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        delay = retry_after_seconds(exc.headers.get("Retry-After"))
        code = ""
        try:
            payload = json.loads(exc.read(65536))
            error = payload.get("error", {})
            code = error.get("code", "") if isinstance(error.get("code"), str) else error.get("status", "")
            for detail in error.get("details", []):
                if "RetryInfo" in detail.get("@type", ""):
                    delay = max(delay, float(str(detail.get("retryDelay", "0s")).rstrip("s")))
        except (ValueError, TypeError, AttributeError):
            pass
        raise HTTPFailure(exc.code, delay, code) from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise SpeechAPIError("Speech provider returned invalid JSON") from None


def gemini_models(pool: KeyPool) -> list[str]:
    payload = pool.call(lambda key: request_json(
        "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000",
        headers={"x-goog-api-key": key}))
    return [model["name"].removeprefix("models/") for model in payload.get("models", [])]


def gemini_tts(pool: KeyPool, text: str, voice: str, style: str,
               model="gemini-3.8-flash-tts") -> bytes:
    if model.startswith("gemini-3.8-"):
        url = "https://generativelanguage.googleapis.com/v1beta/interactions"
        payload = {"model": model, "input": [{"type": "user_input", "content": [{
            "type": "text", "text": text,
            "annotations": [{"type": "speech_metadata", "style": style}]}]}],
            "response_format": {"type": "audio", "mime_type": "audio/wav"},
            "generation_config": {"speech_config": [{"voice": voice}]}}
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {"contents": [{"parts": [{"text": f"Speak exactly the following sentence, no added words. {style}\n\n{text}"}]}],
                   "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {
                       "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    response = pool.call(lambda key: request_json(url, headers={
        "x-goog-api-key": key, "Content-Type": "application/json"}, body=json.dumps(payload).encode()))
    blocks = [content for step in response.get("steps", []) for content in step.get("content", [])
              if content.get("type") == "audio"]
    if not blocks:
        blocks = [part["inlineData"] for candidate in response.get("candidates", [])
                  for part in candidate.get("content", {}).get("parts", []) if "inlineData" in part]
    if not blocks or not blocks[-1].get("data"):
        raise SpeechAPIError("Gemini returned no speech audio")
    raw = base64.b64decode(blocks[-1]["data"])
    if raw[:4] == b"RIFF":
        return raw
    mime = blocks[-1].get("mime_type", blocks[-1].get("mimeType", "audio/L16;rate=24000"))
    match = re.search(r"rate=(\d+)", mime)
    sample_rate = int(match.group(1)) if match else 24000
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(raw)
    return buffer.getvalue()


def groq_transcribe(pool: KeyPool, wav_path: str | Path, *, prompt="", model="whisper-large-v3") -> dict:
    path = Path(wav_path)
    boundary = f"----BlenderSpeech{uuid.uuid4().hex}"
    chunks = []
    fields = [("model", model), ("language", "en"), ("response_format", "verbose_json"),
              ("temperature", "0"), ("timestamp_granularities[]", "word"),
              ("timestamp_granularities[]", "segment"), ("prompt", prompt)]
    for name, value in fields:
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="dialogue.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode())
    chunks.extend([path.read_bytes(), f"\r\n--{boundary}--\r\n".encode()])
    body = b"".join(chunks)
    return pool.call(lambda key: request_json("https://api.groq.com/openai/v1/audio/transcriptions",
         headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}"}, body=body))
