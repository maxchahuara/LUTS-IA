import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, redirect, url_for, abort
import openai
import requests
import uuid

app = Flask(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route("/")
def index():
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
    return jsonify({"response": response.choices[0].message["content"].strip()})

if __name__ == "__main__":
    app.run(debug=True)
