import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, redirect, url_for, abort
import openai
import requests
import uuid

app = Flask(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')

from gtts import gTTS

class TTS():
    def process(self, text):
        tts = gTTS(text=text, lang='es')
        file_name = f"response_{uuid.uuid4()}.mp3"
        file_path = os.path.join(app.root_path, "static", file_name)
        tts.save(file_path)
        return file_name

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/chat")
def chat_page():
    return render_template("chat.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    if not request.is_json:
        abort(415, description="Unsupported Media Type. Expected application/json.")
    
    messages = request.json["messages"]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    assistant_response = response.choices[0].message["content"].strip()
    
    tts = TTS()
    audio_file = tts.process(assistant_response)

    return jsonify({"response": assistant_response, "audio_file": audio_file})

@app.route("/api/transcribe", methods=["POST"])
def transcribe_audio():
    audio_file = request.files.get('audio')
    if not audio_file:
        return jsonify({"error": "No audio file provided"}), 400
    
    # Save the audio to a file with a unique UUID
    audio_filename = f"question_{uuid.uuid4()}.wav"
    audio_path = os.path.join("static", audio_filename)
    audio_file.save(audio_path)
    
    try:
        with open(audio_path, "rb") as file:
            transcript = openai.Audio.transcribe("whisper-1", file)
        return jsonify({"transcript": transcript.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
