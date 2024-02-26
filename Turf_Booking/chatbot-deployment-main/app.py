from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from chat import get_response
import json
app = Flask(__name__)
CORS(app, origins='http://localhost:3000', supports_credentials=True)


@app.post("/predict")
def predict():
    text = request.get_json().get("message")
    with open('latlong.json','r') as file:
        data = json.load(file)
    lat = data.get('lat')
    long = data.get('long')
    response= get_response(text, lat, long)

    message = {"answer": response}


    return jsonify(message)

if __name__ == "__main__":
    app.run(debug=True)