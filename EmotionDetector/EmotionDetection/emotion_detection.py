"""Emotion detection using the Watson NLP EmotionPredict service."""

import os

import requests

# Default endpoint used by the Coursera / Skills Network lab environment.
# It can be overridden with the WATSON_EMOTION_URL environment variable.
DEFAULT_URL = (
    "https://sn-watson-emotion.labs.skills.network"
    "/v1/watson.runtime.nlp.v1/NlpService/EmotionPredict"
)
MODEL_ID = "emotion_aggregated-workflow_lang_en_stock"
REQUEST_TIMEOUT = 10  # seconds
EMOTIONS = ("anger", "disgust", "fear", "joy", "sadness")

# Messages stored under the "error" key when no result is available.
ERROR_EMPTY = "Input text is empty."
ERROR_BAD_REQUEST = "The service rejected the request (status code 400)."
ERROR_SERVICE = (
    "The emotion detection service is unavailable or returned an unusable response."
)


def _empty_result(message):
    """Build the 'no result' dictionary: all values None plus an error message."""
    result = {emotion: None for emotion in EMOTIONS}
    result["dominant_emotion"] = None
    result["error"] = message
    return result


def _parse_scores(response_json):
    """Extract the five emotion scores from a Watson response.

    Raises KeyError, IndexError, TypeError or ValueError if the structure
    is not what we expect.
    """
    emotions = response_json["emotionPredictions"][0]["emotion"]
    return {name: float(emotions[name]) for name in EMOTIONS}


def emotion_detector(text_to_analyze):
    """Analyze text and return the emotion scores and the dominant emotion.

    On success the dictionary has the keys anger, disgust, fear, joy, sadness
    and dominant_emotion. If no analysis could be made, every one of those
    values is None and an extra "error" key explains why. Scores are never
    invented when the service fails.
    """
    if not isinstance(text_to_analyze, str) or not text_to_analyze.strip():
        return _empty_result(ERROR_EMPTY)

    url = os.environ.get("WATSON_EMOTION_URL", DEFAULT_URL)
    headers = {"grpc-metadata-mm-model-id": MODEL_ID}
    payload = {"raw_document": {"text": text_to_analyze}}

    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.RequestException:
        return _empty_result(ERROR_SERVICE)

    # Required by the assignment: status 400 means blank/invalid input.
    if response.status_code == 400:
        return _empty_result(ERROR_BAD_REQUEST)
    if response.status_code != 200:
        return _empty_result(ERROR_SERVICE)

    try:
        scores = _parse_scores(response.json())
    except (KeyError, IndexError, TypeError, ValueError):
        return _empty_result(ERROR_SERVICE)

    result = dict(scores)
    result["dominant_emotion"] = max(scores, key=scores.get)
    return result
