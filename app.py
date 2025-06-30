import os
from flask import Flask, request
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

# Load env variables
load_dotenv()

# Assign env vars to constants
MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
BOARD_ID = os.getenv("BOARD_ID")

NAME_COLUMN_ID = os.getenv("NAME_COLUMN_ID")
PHONE_COLUMN_ID = os.getenv("PHONE_COLUMN_ID")
STATUS_COLUMN_ID = os.getenv("STATUS_COLUMN_ID")
TIME_COLUMN_ID = os.getenv("TIME_COLUMN_ID")
DURATION_COLUMN_ID = os.getenv("DURATION_COLUMN_ID")

app = Flask(__name__)


@app.route('/exotel-callback', methods=['POST'])
def handle_exotel_callback():
    # Extract data from webhook
    From = request.form.get('From')
    Status = request.form.get('Status')
    StartTime = request.form.get('StartTime')
    EndTime = request.form.get('EndTime')

    print("📞 Webhook Received:", From, Status, StartTime, EndTime)

    # Calculate duration
    duration_sec = None
    if StartTime and EndTime:
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            start_dt = datetime.strptime(StartTime, fmt)
            end_dt = datetime.strptime(EndTime, fmt)
            duration_sec = int((end_dt - start_dt).total_seconds())
        except Exception as e:
            print("⚠️ Time parsing error:", e)

    # Prepare column values dictionary
    column_values = {
        NAME_COLUMN_ID: f"Call from {From}",
        PHONE_COLUMN_ID: From,
        STATUS_COLUMN_ID: Status,
        TIME_COLUMN_ID: {
            "date": StartTime.split(" ")[0],
            "time": StartTime.split(" ")[1]
        },
        DURATION_COLUMN_ID: {
            "running": False,
            "duration": duration_sec
        }
    }

    # ✅ Safe and valid GraphQL query using variables
    graphql_query = {
        "query": """
        mutation ($boardId: Int!, $itemName: String!, $columnValues: JSON!) {
            create_item(
                board_id: $boardId,
                item_name: $itemName,
                column_values: $columnValues
            ) {
                id
            }
        }
        """,
        "variables": {
            "boardId": int(BOARD_ID),
            "itemName": f"Call from {From}",
            "columnValues": column_values
        }
    }

    headers = {
        "Authorization": f"Bearer {MONDAY_API_KEY}",
        "Content-Type": "application/json"
    }

    print("📤 Sending to Monday with data:")
    print(json.dumps(graphql_query, indent=2))

    try:
        response = requests.post(
            "https://api.monday.com/v2", json=graphql_query, headers=headers)
        print("✅ Monday response:", response.json())
        return {"status": "success", "monday_response": response.json()}
    except Exception as e:
        print("❌ Error sending to Monday:", e)
        return {"status": "error", "message": str(e)}, 500


if __name__ == "__main__":
    app.run(port=3000)
