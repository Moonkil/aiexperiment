import os
import tempfile
from flask import Flask, request, render_template_string
import yt_dlp

try:
    import numpy as np
except Exception as e:
    raise RuntimeError(
        "NumPy is required. Install it with 'pip install numpy'.") from e

try:
    import librosa
except Exception as e:
    raise RuntimeError(
        "librosa failed to import. Ensure NumPy is installed: 'pip install numpy'."
    ) from e

whisper_import_error = None
try:
    import whisper
except Exception as e:
    whisper = None
    whisper_import_error = e

app = Flask(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Music Analyzer</title>
</head>
<body>
    <h1>YouTube Music Analyzer</h1>
    <form action="/analyze" method="post">
        <input type="text" name="url" placeholder="Enter YouTube URL" size="50" />
        <button type="submit">Analyze</button>
    </form>
    <p>Only the first track is analyzed if multiple tracks are present.</p>
</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Analysis Result</title>
</head>
<body>
    <h1>Analysis Result</h1>
    <p><strong>BPM:</strong> {{ bpm }}</p>
    <p><strong>Chords:</strong> {{ chords }}</p>
    <p><strong>Lyrics:</strong></p>
    <pre>{{ lyrics }}</pre>
    <p><a href="/">Analyze another</a></p>
</body>
</html>
"""

def download_audio(url, out_file):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_file,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def analyze_bpm(audio_file):
    y, sr = librosa.load(audio_file)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return round(float(tempo), 2)


def analyze_chords(audio_file):
    # Simple chroma-based chord estimation using major/minor templates
    y, sr = librosa.load(audio_file)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    # Template for major/minor chords
    maj_profile = np.array([1,0,0,0,1,0,0,1,0,0,0,0])
    min_profile = np.array([1,0,0,1,0,0,0,1,0,0,0,0])
    chords = []
    for frame in chroma.T:
        corr = []
        for root in range(12):
            corr.append(np.correlate(np.roll(maj_profile, root), frame))
            corr.append(np.correlate(np.roll(min_profile, root), frame))
        chord_idx = int(np.argmax(corr))
        root = chord_idx // 2
        quality = 'maj' if chord_idx % 2 == 0 else 'min'
        note = librosa.midi_to_note(root + 60)[:-1]
        chords.append(f"{note}{quality}")
    # Return the most common chord progression as a simple summary
    from collections import Counter
    counter = Counter(chords)
    most_common = ', '.join([f"{c} ({n})" for c, n in counter.most_common(5)])
    return most_common


def transcribe_audio(audio_file):
    if whisper is None:
        return f"Whisper not available: {whisper_import_error}"
    model = whisper.load_model("base")
    result = model.transcribe(audio_file)
    return result.get('text', '').strip()


@ app.route('/', methods=['GET'])
def index():
    return render_template_string(INDEX_HTML)


@ app.route('/analyze', methods=['POST'])
def analyze():
    url = request.form.get('url')
    if not url:
        return "No URL provided", 400
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_audio = os.path.join(tmpdir, 'audio.%(ext)s')
        download_audio(url, tmp_audio)
        audio_wav = tmp_audio.replace('%(ext)s', 'wav')
        bpm = analyze_bpm(audio_wav)
        chords = analyze_chords(audio_wav)
        lyrics = transcribe_audio(audio_wav)
    return render_template_string(RESULT_HTML, bpm=bpm, chords=chords, lyrics=lyrics)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
