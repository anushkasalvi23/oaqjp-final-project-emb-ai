"""Unit tests for the emotion detector.

All tests here use MOCKED HTTP responses, so they are deterministic and do
not contact the Watson service. They verify our parsing/error-handling logic,
NOT the live API. For live verification see the README ("Live API check").
"""

import unittest
from unittest.mock import MagicMock, patch

import requests

from EmotionDetection.emotion_detection import emotion_detector
from server import app

MODULE = "EmotionDetection.emotion_detection.requests.post"
NONE_RESULT = {
    "anger": None, "disgust": None, "fear": None, "joy": None,
    "sadness": None, "dominant_emotion": None,
}


def fake_response(status_code=200, emotions=None, json_error=False):
    """Create a fake requests.Response."""
    response = MagicMock()
    response.status_code = status_code
    if json_error:
        response.json.side_effect = ValueError("bad json")
    else:
        response.json.return_value = {"emotionPredictions": [{"emotion": emotions}]}
    return response


def scores(dominant):
    """Return a score dict where `dominant` has the highest value."""
    base = {"anger": 0.01, "disgust": 0.02, "fear": 0.03, "joy": 0.04, "sadness": 0.05}
    base[dominant] = 0.9
    return base


class TestEmotionDetector(unittest.TestCase):
    """Tests for EmotionDetection.emotion_detector (HTTP mocked)."""

    def check_dominant(self, text, dominant):
        """Run the detector against a mocked response for one emotion."""
        with patch(MODULE, return_value=fake_response(emotions=scores(dominant))):
            result = emotion_detector(text)
        self.assertEqual(result["dominant_emotion"], dominant)
        self.assertEqual(result[dominant], 0.9)

    def test_joy(self):
        """Joy example."""
        self.check_dominant("I am glad this happened", "joy")

    def test_anger(self):
        """Anger example."""
        self.check_dominant("I am really mad about this", "anger")

    def test_disgust(self):
        """Disgust example."""
        self.check_dominant("I feel disgusted just hearing about this", "disgust")

    def test_sadness(self):
        """Sadness example."""
        self.check_dominant("I am so sad about this", "sadness")

    def test_fear(self):
        """Fear example."""
        self.check_dominant("I am really afraid that this will happen", "fear")

    def test_status_400(self):
        """Status 400 gives None for every field."""
        with patch(MODULE, return_value=fake_response(status_code=400)):
            result = emotion_detector("some text")
        for key, value in NONE_RESULT.items():
            self.assertEqual(result[key], value)
        self.assertIn("error", result)

    def test_malformed_json(self):
        """Unparseable JSON does not fabricate scores."""
        with patch(MODULE, return_value=fake_response(json_error=True)):
            result = emotion_detector("some text")
        self.assertIsNone(result["dominant_emotion"])
        self.assertIn("error", result)

    def test_missing_keys(self):
        """A response without the expected structure is handled safely."""
        with patch(MODULE, return_value=fake_response(emotions={"joy": 0.5})):
            result = emotion_detector("some text")
        self.assertIsNone(result["dominant_emotion"])

    def test_server_error_status(self):
        """Non-200, non-400 status is reported as a failure."""
        with patch(MODULE, return_value=fake_response(status_code=500)):
            result = emotion_detector("some text")
        self.assertIsNone(result["dominant_emotion"])

    def test_empty_input_makes_no_request(self):
        """Empty and whitespace-only input never reaches the API."""
        with patch(MODULE) as post:
            for text in ("", "   ", None):
                result = emotion_detector(text)
                self.assertIsNone(result["dominant_emotion"])
                self.assertIn("error", result)
            post.assert_not_called()

    def test_request_failure(self):
        """Network errors and timeouts return a safe error result."""
        for exc in (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            with patch(MODULE, side_effect=exc("boom")):
                result = emotion_detector("some text")
            self.assertIsNone(result["dominant_emotion"])
            self.assertIn("error", result)


class TestServer(unittest.TestCase):
    """Tests for the Flask routes (emotion_detector mocked)."""

    def setUp(self):
        self.client = app.test_client()

    def test_home_page(self):
        """Home page renders."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Emotion Detector", response.data)

    def test_success(self):
        """A valid result is formatted as a readable sentence."""
        fake = dict(scores("joy"), dominant_emotion="joy")
        with patch("server.emotion_detector", return_value=fake):
            response = self.client.get("/emotionDetector?textToAnalyze=hello")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"The dominant emotion is joy.", response.data)

    def test_blank_input(self):
        """Blank/whitespace input gives 400 and a clear message."""
        for query in ("", "?textToAnalyze=", "?textToAnalyze=%20%20"):
            response = self.client.get("/emotionDetector" + query)
            self.assertEqual(response.status_code, 400)
            self.assertIn(b"Invalid text", response.data)

    def test_service_unavailable(self):
        """A service failure is shown as 503 with a friendly message."""
        failed = dict(NONE_RESULT, error="The emotion detection service is unavailable.")
        with patch("server.emotion_detector", return_value=failed):
            response = self.client.get("/emotionDetector?textToAnalyze=hello")
        self.assertEqual(response.status_code, 503)
        self.assertIn(b"unavailable", response.data)

    def test_unexpected_exception_hides_details(self):
        """Unexpected exceptions return 500 without leaking the message."""
        with patch("server.emotion_detector", side_effect=RuntimeError("secret-key-123")),                 self.assertLogs("server", level="ERROR"):
            response = self.client.get("/emotionDetector?textToAnalyze=hello")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(b"secret-key-123", response.data)
        self.assertNotIn(b"Traceback", response.data)


if __name__ == "__main__":
    unittest.main()
