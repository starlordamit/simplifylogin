# File: src/api/server.py, Component Start: Line 1
from flask import Flask, request, jsonify
from flask_cors import CORS  # Added for CORS support
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS

EXTERNAL_API_URL = "https://abes.platform.simplifii.com/api/v1/admin/authenticate"
HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://abes.web.simplifii.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "device_id": "device_id_here",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"'
}

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    payload = {"username": username, "password": password}
    try:
        resp = requests.post(EXTERNAL_API_URL, headers=HEADERS, data=payload)
        return (resp.text, resp.status_code, {'Content-Type': 'application/json'})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/trending', methods=['GET'])
def trending():
    url = "https://api.thumbnailpreview.com/api/youtube/trending"
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "if-none-match": "\"1357opnwisk2ipk-df\"",
        "priority": "u=1, i",
        "referer": "https://api.thumbnailpreview.com/v1",
        "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }
   
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return (resp.text, resp.status_code, {'Content-Type': 'application/json'})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
