import traceback
from flask import Flask,request, jsonify
from flask_cors import CORS
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import fitz
from dotenv import load_dotenv
import os
import re


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)
# CORS(app,origins=["http://localhost:3000"])

def get_summary(prompt):
    response = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes text."},
            {"role": "user", "content": prompt}
        ],
        # temperature=0.7,
        max_tokens=300,
    )
    return response.choices[0].message.content


@app.route('/summarize/text', methods=['POST'])
def summarize_text():
    data = request.json
    text = data.get('text', '')
    summary = get_summary(f"Summarize the following text:\n\n{text}")
    return jsonify({'summary': summary})

@app.route('/summarize/pdf', methods=['POST'])
def summarize_pdf():
    file = request.files['file']
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    summary = get_summary(f"Summarize the following text:\n\n{text}")
    return jsonify({'summary': summary})

@app.route('/summarize/youtube', methods=['POST'])
def summarize_youtube():
    data = request.json
    video_url = data.get('url', '').strip()
    print("Received URL:", video_url)

    # Validate input
    if not video_url:
        return jsonify({'error': 'YouTube URL is required.'}), 400

    # Extract video ID from URL
    video_id_match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', video_url)
    if not video_id_match:
        return jsonify({'error': 'Invalid YouTube URL. Could not extract video ID.'}), 400
    video_id = video_id_match.group(1)
    print("Extracted Video ID:", video_id)  # Debugging log

    try:
        # Fetch transcript using the correct method
        yt_api = YouTubeTranscriptApi()
        transcript_snippet = yt_api.fetch(video_id)

        # Extract transcript text from the `snippets` attribute
        transcript = " ".join([snippet.text for snippet in transcript_snippet.snippets])

        print("Transcript length:", len(transcript))  # Debug

        # Generate summary using your get_summary() function
        summary = get_summary(f"Summarize this YouTube video transcript:\n\n{transcript}")
        return jsonify({'summary': summary})
    except TranscriptsDisabled:
        return jsonify({'error': 'Subtitles are disabled for this video.'}), 400
    except NoTranscriptFound:
        return jsonify({'error': 'Transcript not available for this video.'}), 400
    except Exception as e:
        print("Error:", str(e))  # Debugging log
        return jsonify({'error': str(e)}), 500  

if __name__ == '__main__':
    # app.run(debug=True)
     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)