# YouTube Music Analyzer

This simple Flask application extracts the BPM, chord progression, and lyrics from a YouTube URL containing a music track. Only the first track is analyzed if the video contains multiple songs.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   python app.py
   ```
3. Open `http://localhost:5000` in your browser and enter a YouTube URL.

Note: Whisper models will be downloaded on first run for lyric transcription.

### Troubleshooting

If the server fails to start with an error similar to `RuntimeError: Numpy is not available`,
install a compatible NumPy wheel manually:

```bash
pip install -U numpy
```
Some environments do not provide prebuilt NumPy packages, which can lead to this
error when importing `librosa` or `whisper`.
