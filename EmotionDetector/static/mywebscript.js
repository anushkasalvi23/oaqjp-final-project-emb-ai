// Sends the entered text to the Flask backend and shows the response.
function RunSentimentAnalysis() {
    const textToAnalyze = document.getElementById("textToAnalyze").value;
    const output = document.getElementById("system_response");

    // Client-side check; the server validates again.
    if (textToAnalyze.trim() === "") {
        output.className = "error";
        output.textContent = "Invalid text! Please try again!";
        return;
    }

    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState === 4) {
            output.className = this.status === 200 ? "ok" : "error";
            output.textContent = this.status === 0
                ? "Could not reach the server. Please try again later."
                : this.responseText;
        }
    };
    xhttp.open("GET", "emotionDetector?textToAnalyze=" + encodeURIComponent(textToAnalyze), true);
    xhttp.send();
}
