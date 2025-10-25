from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello from Flask backend!"})

@app.route("/api/data", methods=["GET", "POST"])
def data():
    if request.method == "GET":
        # Example data
        return jsonify({"data": ["alpha", "beta", "gamma"]})

    # POST: echo JSON body
    payload = request.get_json(silent=True) or {}
    return jsonify({"received": payload}), 201

if __name__ == "__main__":
    # Debug mode for development; bind to all interfaces for convenience
    app.run(host="0.0.0.0", port=5000, debug=True)
