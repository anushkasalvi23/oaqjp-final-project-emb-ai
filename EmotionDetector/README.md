# Final Project

## Emotion Detector Application

This project uses the Watson NLP library to detect emotions in text.
# Emotion Detector

A small Flask web application that analyzes the emotions in a piece of text
(anger, disgust, fear, joy, sadness) and reports the dominant emotion. It
calls the Watson NLP `EmotionPredict` service and was built for the Coursera
final assignment.

> **Deployment status:** this repository does not claim a public deployment.
> The app runs locally (see below).

## Project structure

```text
EmotionDetector/
├── EmotionDetection/
│   ├── __init__.py             # exposes emotion_detector
│   └── emotion_detection.py    # Watson NLP client + parsing + error handling
├── static/mywebscript.js       # front-end logic
├── templates/index.html        # web page
├── server.py                   # Flask app
├── test_emotion_detection.py   # unit tests (mocked HTTP)
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Watson endpoint / credentials

The code uses the Skills Network lab endpoint used in the Coursera course:

```
https://sn-watson-emotion.labs.skills.network/v1/watson.runtime.nlp.v1/NlpService/EmotionPredict
```

with header `grpc-metadata-mm-model-id: emotion_aggregated-workflow_lang_en_stock`
and body `{"raw_document": {"text": "..."}}`. This endpoint is normally only
reachable from the Coursera / Skills Network lab environment. To use a
different endpoint, set the `WATSON_EMOTION_URL` environment variable
(no keys are stored in the code or repository):

```bash
# PowerShell
$env:WATSON_EMOTION_URL = "https://your-endpoint/.../EmotionPredict"
```

## Usage

```python
from EmotionDetection.emotion_detection import emotion_detector
emotion_detector("I love this new technology.")
# {'anger': ..., 'disgust': ..., 'fear': ..., 'joy': ..., 'sadness': ..., 'dominant_emotion': 'joy'}
```

Verify the import:

```bash
python -c "from EmotionDetection.emotion_detection import emotion_detector; print('Import successful')"
```

## Run the Flask app

```bash
python server.py
```

Open <http://127.0.0.1:5000/>. The app starts even if the Watson service is
unreachable; analysis requests then show a friendly error message.

## Tests

```bash
python -m unittest test_emotion_detection.py
```

These tests use **mocked** HTTP responses: they check parsing, status 400,
malformed JSON, empty input, request failures and the Flask routes. They do
**not** verify the live API.

### Live API check (manual)

From an environment that can reach the endpoint:

```bash
python -c "from EmotionDetection import emotion_detector; print(emotion_detector('I am glad this happened'))"
```

## Error handling

| Situation | Behaviour |
|-----------|-----------|
| Empty/whitespace text | `emotion_detector` returns all `None` plus an `error` message without calling the API; the server answers `400` "Invalid text! Please try again!" |
| Watson status 400 | All values `None` (assignment format) plus `error`; server answers `400` |
| Network error, timeout, other status, malformed JSON | All values `None` plus `error`; server answers `503` with a friendly message |
| Unexpected exception | Logged server-side; user sees a generic `500` message, no stack trace |

## Static analysis

```bash
pylint server.py
```
