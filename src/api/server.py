# File: src/api/server.py, Component Start: Line 1
import requests
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

# Utility functions for parsing timetable data

def remove_html_tags(text):
    return re.sub(r'<[^>]+>', '', text).strip()

def parse_single_time(slot_str):
    times = slot_str.split("-")
    if len(times) == 2:
        return [times[0].strip(), times[1].strip()]
    return [slot_str.strip()]

def parse_time_slots(cell):
    slots = re.findall(r'<div[^>]*>(.*?)</div>', cell)
    if slots:
        return [parse_single_time(slot.strip()) for slot in slots if slot.strip()]
    clean = remove_html_tags(cell)
    return [parse_single_time(clean)] if clean else []

def parse_course_details(course_str):
    parts = [p.strip() for p in course_str.split("/") if p.strip()]
    if len(parts) < 5:
        return {"raw": course_str}
    batch_year = parts[0]
    branch = parts[1]
    subject_info = parts[2]
    subject_parts = subject_info.split()
    subject_code = subject_parts[0] if subject_parts else ""
    subject_name = " ".join(subject_parts[1:]) if len(subject_parts) > 1 else ""
    section = parts[3]
    if section.lower().startswith("sec"):
        sec_parts = re.split('[- ]', section)
        section = "Section " + sec_parts[-1]
    faculty_name = parts[-1].lower().capitalize()
    return {
        "batch_year": batch_year,
        "branch": branch,
        "subject_code": subject_code,
        "subject_name": subject_name,
        "section": section,
        "faculty_name": faculty_name
    }

def parse_timetable(data):
    timetable = {}
    header = data[0]
    # Extract month and year from header's "name" field (e.g., "March-2025")
    header_name = remove_html_tags(header.get("name", ""))
    month_year_parts = header_name.split("-")
    if len(month_year_parts) == 2:
        month_name = month_year_parts[0]
        year = month_year_parts[1]
    else:
        month_name = ""
        year = ""
    # Map month name to month number
    month_map = {
        "January": "01",
        "February": "02",
        "March": "03",
        "April": "04",
        "May": "05",
        "June": "06",
        "July": "07",
        "August": "08",
        "September": "09",
        "October": "10",
        "November": "11",
        "December": "12"
    }
    month_number = month_map.get(month_name, "")
    
    for day in range(1, 32):
        key = f'c{day}'
        weekday = remove_html_tags(header.get(key, ""))
        date_str = ""
        if year and month_number:
            date_str = f"{year}-{month_number}-{day:02d}"
        timetable[str(day)] = {
            "weekday": weekday,
            "date": date_str,
            "classes": []
        }
    for course in data[1:]:
        course_raw = course.get('name_text', '')
        course_clean = remove_html_tags(course_raw)
        course_details = parse_course_details(course_clean)
        for day in range(1, 32):
            key = f'c{day}'
            cell = course.get(key)
            if cell:
                if isinstance(cell, list):
                    cell = " ".join(cell)
                cell = cell.strip()
                if cell:
                    time_slots = parse_time_slots(cell)
                    if time_slots:
                        timetable[str(day)]["classes"].append({
                            "course": course_clean,
                            "course_details": course_details,
                            "time": time_slots
                        })
    return timetable

def format_timetable(api_data):
    data = api_data.get('response', {}).get('data', [])
    timetable = parse_timetable(data)
    return json.dumps(timetable, indent=2)

def get_student_schedule(bearer_token):
    """
    Fetches and formats the student schedule from ABES API.
    
    Args:
        bearer_token (str): Bearer token for authentication.
        
    Returns:
        str: Formatted timetable as JSON or an error message.
    """
    url = "https://abes.platform.simplifii.com/api/v1/custom/getMyScheduleStudent"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if not data.get('response', {}).get('data'):
            return "No schedule data found in the response."
        return format_timetable(data)
    except requests.exceptions.RequestException as e:
        return f"Error fetching schedule: {str(e)}"
    except ValueError as e:
        return f"Error parsing response: {str(e)}"

# Flask app initialization
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
        resp.raise_for_status()
        login_response = resp.json()
        if login_response.get("status") != 1:
            return jsonify({"error": login_response.get("msg", "Login failed")}), 400
        response_data = login_response.get("response", {})
        result = {
            "token": login_response.get("token", ""),
            "email": response_data.get("email", ""),
            "mobile": response_data.get("mobile", ""),
            "name": response_data.get("name", ""),
            "role": response_data.get("role", ""),
            "roll_number": response_data.get("string4", ""),
            "section": response_data.get("string5", ""),
            "pin": response_data.get("string10", ""),
            "year": response_data.get("int3", ""),
            "semester": response_data.get("int4", ""),
            "username": response_data.get("username", ""),
            "batch": response_data.get("int6", "")
        }
        return jsonify(result), resp.status_code
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

@app.route('/timetable', methods=['POST'])
def timetable_route():
    """
    Expects a JSON body with a "token" field.
    Returns the formatted timetable as JSON.
    """
    data = request.get_json() if request.is_json else request.form
    token = data.get('token')
    if not token:
        return jsonify({"error": "Missing token"}), 400

    timetable_result = get_student_schedule(token)
    try:
        timetable_json = json.loads(timetable_result)
        return jsonify(timetable_json)
    except json.JSONDecodeError:
        return jsonify({"error": timetable_result}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
