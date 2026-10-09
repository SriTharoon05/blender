"""Key rotation, cooldown and secret-safe error behavior without API calls."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from speech_api import HTTPFailure, KeyPool, SpeechAPIError, load_key_pools, retry_after_seconds
from ep009_audio import authoritative_words


class FakeTime:
    def __init__(self):
        self.now, self.waits = 0.0, []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.now += seconds


class SpeechAPIKeyPoolTests(unittest.TestCase):
    def make_pool(self):
        timer = FakeTime()
        return KeyPool(["first-placeholder", "second-placeholder"], start_index=0,
                       clock=timer.clock, sleeper=timer.sleep), timer

    def test_starting_key_rotates_between_successful_requests(self):
        pool, _ = self.make_pool()
        calls = []
        def success(key):
            calls.append(key)
            return "audio"
        for _ in range(3):
            self.assertEqual(pool.call(success), "audio")
        self.assertEqual(calls, ["first-placeholder", "second-placeholder", "first-placeholder"])

    def test_auth_failure_disables_only_invalid_key(self):
        pool, _ = self.make_pool()
        calls = []
        def operation(key):
            calls.append(key)
            if key == "first-placeholder":
                raise HTTPFailure(401)
            return "audio"
        self.assertEqual(pool.call(operation), "audio")
        self.assertEqual(pool.call(operation), "audio")
        self.assertEqual(calls, ["first-placeholder", "second-placeholder", "second-placeholder"])

    def test_rate_limit_waits_provider_wide_before_another_key(self):
        pool, timer = self.make_pool()
        calls = []
        def operation(key):
            calls.append((key, timer.now))
            if len(calls) == 1:
                raise HTTPFailure(429, retry_after=13)
            return "audio"
        self.assertEqual(pool.call(operation), "audio")
        self.assertEqual(timer.waits, [13])
        self.assertEqual(calls[1], ("second-placeholder", 13))

    def test_cooldown_larger_than_budget_stops_without_rotating(self):
        pool, timer = self.make_pool()
        calls = []
        def operation(key):
            calls.append(key)
            raise HTTPFailure(429, 3600)
        with self.assertRaisesRegex(SpeechAPIError, "cooldown"):
            pool.call(operation, max_wait=60)
        self.assertEqual(len(calls), 1)
        self.assertEqual(timer.waits, [])

    def test_daily_quota_does_not_retry_other_accounts(self):
        pool, _ = self.make_pool()
        calls = []
        def operation(key):
            calls.append(key)
            raise HTTPFailure(429, 86400, "DAILY_QUOTA_EXCEEDED")
        with self.assertRaisesRegex(SpeechAPIError, "quota exhausted"):
            pool.call(operation)
        self.assertEqual(len(calls), 1)

    def test_transient_failure_retries_available_key(self):
        pool, timer = self.make_pool()
        calls = []
        def operation(key):
            calls.append(key)
            if len(calls) == 1:
                raise HTTPFailure(503)
            return "audio"
        self.assertEqual(pool.call(operation), "audio")
        self.assertEqual(calls, ["first-placeholder", "second-placeholder"])
        self.assertEqual(timer.waits, [])

    def test_credentials_never_appear_in_repr_or_auth_errors(self):
        pool, _ = self.make_pool()
        with self.assertRaises(SpeechAPIError) as caught:
            pool.call(lambda key: (_ for _ in ()).throw(HTTPFailure(403)))
        for credential in ("first-placeholder", "second-placeholder"):
            self.assertNotIn(credential, repr(pool))
            self.assertNotIn(credential, str(caught.exception))

    def test_only_named_pools_are_loaded_without_executing_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text('GEMINI_API_KEYS="one,two,one"\nGROQ_API_KEYS=three,four\nUNRELATED=ignore\n')
            with patch.dict("os.environ", {}, clear=True):
                pools = load_key_pools(path)
            self.assertEqual(pools, {"GEMINI_API_KEYS": ["one", "two"], "GROQ_API_KEYS": ["three", "four"]})

    def test_environment_pool_overrides_dotenv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("GEMINI_API_KEYS=file-key\n")
            with patch.dict("os.environ", {"GEMINI_API_KEYS": "environment-key"}, clear=True):
                pools = load_key_pools(path)
            self.assertEqual(pools["GEMINI_API_KEYS"], ["environment-key"])

    def test_retry_after_numeric_and_http_date(self):
        self.assertEqual(retry_after_seconds("12"), 12)
        self.assertEqual(retry_after_seconds("Thu, 01 Jan 1970 00:01:00 GMT", now=10), 50)
        self.assertEqual(retry_after_seconds("unparseable"), 0)

    def test_unrecognized_provider_error_code_cannot_leak_credentials(self):
        error = HTTPFailure(403, code="PRIVATE-CREDENTIAL-VALUE")
        self.assertEqual(error.code, "")
        self.assertEqual(str(error), "Speech provider HTTP 403")

    def test_asr_boundary_padding_clamps_to_real_audio_end(self):
        rows = authoritative_words("Hi there!", {"words": [
            {"word": "Hi", "start": .05, "end": .2},
            {"word": "there!", "start": .2, "end": 1.3}]}, 2, .9)
        self.assertEqual(rows[-1]["word"], "there!")
        self.assertEqual(rows[-1]["end"], 2.9)
        self.assertTrue(rows[-1]["end_clamped_to_audio"])

    def test_changed_spoken_script_stops_instead_of_fabricating_word_timings(self):
        with self.assertRaisesRegex(ValueError, "ASR transcript differs"):
            authoritative_words("Hi there!", {"words": [
                {"word": "Goodbye", "start": .05, "end": .2}]}, 0, .9)


if __name__ == "__main__":
    unittest.main()
