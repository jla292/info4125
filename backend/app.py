from flask import Flask, jsonify, request
import json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json(filename):
    with open(os.path.join(BASE_DIR, filename), "r") as f:
        return json.load(f)

@app.route("/")
def home():
    return jsonify({"message": "API is running!"})

@app.route("/mealplans")
def mealplans():
    return jsonify(load_json("cornell_mealplans_2025.json"))

@app.route("/events")
def events():
    return jsonify(load_json("event_list.json"))

@app.route("/financial_aid")
def financial_aid():
    return jsonify(load_json("financial_aid_facts.json"))

@app.route("/feedback", methods=["POST"])
def feedback():
    feedback = request.json
    return jsonify({"message": "Feedback received!", "data": feedback}), 201

if __name__ == "__main__":
    app.run(debug=True)
