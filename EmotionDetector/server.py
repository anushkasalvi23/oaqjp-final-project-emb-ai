"""Flask web application for the Emotion Detector."""

import logging

from flask import Flask, jsonify, render_template, request

from EmotionDetection.emotion_detection import (
    ERROR_BAD_REQUEST,
    ERROR_EMPTY,
    emotion_detector,
)

app = Flask(__name__)
logger = logging.getLogger(__name__)

INVALID_TEXT_MESSAGE = "Invalid text! Please try again!"
SERVICE_ERROR_MESSAGE = (
    "The emotion detection service is currently unavailable. Please try again later."
)
UNEXPECTED_ERROR_MESSAGE = "Something went wrong. Please try again later."


def format_result(result):
    """Turn a result dictionary into the sentence required by the assignment."""
    return (
        "For the given statement, the system response is "
        f"'anger': {result['anger']}, 'disgust': {result['disgust']}, "
        f"'fear': {result['fear']}, 'joy': {result['joy']} and "
        f"'sadness': {result['sadness']}. "
        f"The dominant emotion is {result['dominant_emotion']}."
    )


@app.route("/")
def index():
    """Render the home page."""
    return render_template("index.html")


@app.route("/emotionDetector")
def emotion_detector_route():
    """Analyze the text in the 'textToAnalyze' query parameter."""
    text = request.args.get("textToAnalyze", "")

    # Blank or whitespace-only input is rejected before calling the service.
    if not text.strip():
        return INVALID_TEXT_MESSAGE, 400

    try:
        result = emotion_detector(text)
    except Exception:  # pylint: disable=broad-exception-caught
        # Log details server-side only; never expose them to the user.
        logger.exception("Unexpected error while detecting emotion")
        return UNEXPECTED_ERROR_MESSAGE, 500

    if result["dominant_emotion"] is None:
        if result.get("error") in (ERROR_BAD_REQUEST, ERROR_EMPTY):
            return INVALID_TEXT_MESSAGE, 400
        return SERVICE_ERROR_MESSAGE, 503

    return format_result(result)


@app.route("/health")
def health():
    """Simple liveness check that does not call the external service."""
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
