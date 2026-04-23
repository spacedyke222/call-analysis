from ringcentral import SDK
from dotenv import load_dotenv
import os
import requests
import json
import time
import random
from datetime import datetime, timedelta, timezone

load_dotenv()

print("ENV TEST:", os.getenv("RC_APP_CLIENT_ID"))

# ----------------------------
# AUTH SETUP
# ----------------------------

rcsdk = SDK(
    os.environ.get("RC_APP_CLIENT_ID"),
    os.environ.get("RC_APP_CLIENT_SECRET"),
    os.environ.get("RC_SERVER_URL")
)

_platform = None


def get_platform():
    global _platform

    if _platform is None:
        _platform = rcsdk.platform()
        _platform.login(jwt=os.environ.get("RC_USER_JWT"))
        print("Login successful.")

    return _platform


# ----------------------------
# STATE (CURSOR TRACKING)
# ----------------------------

STATE_FILE = "state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_sync": None}

    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ----------------------------
# CALL FETCHING (DELTA SAFE)
# ----------------------------

def get_recent_calls(platform, last_sync=None, retries=5):
    """
    Only fetch calls since last successful run.
    Prevents unnecessary API load.
    """

    if last_sync:
        date_from = last_sync
    else:
        now = datetime.now(timezone.utc)
        date_from = (now - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')

    print(f"DEBUG: Requesting calls since {date_from}")

    for i in range(retries):
        try:
            response = platform.get(
                "/restapi/v1.0/account/~/call-log",
                {
                    "view": "Simple",
                    "withRecording": True,
                    "dateFrom": date_from,
                    "perPage": 100
                }
            )
            return response

        except Exception as e:
            wait = (2 ** i) + random.uniform(0, 1)

            print(f"❌ API error: {e}")
            print(f"Retrying in {wait:.1f}s...")

            time.sleep(wait)

    return None


# ----------------------------
# MAIN PIPELINE
# ----------------------------

def run_download_cycle():
    os.makedirs("input_calls", exist_ok=True)
    os.makedirs("call_metadata", exist_ok=True)

    state = load_state()
    platform = get_platform()

    response = get_recent_calls(platform, state.get("last_sync"))

    if not response:
        print("Failed to fetch calls.")
        return

    calls = response.json().records
    token = platform.auth().data()["access_token"]

    new_downloads = 0
    newest_timestamp = state.get("last_sync")

    for call in calls:
        try:
            recording = getattr(call, "recording", None)
            if not recording:
                continue

            recording_id = getattr(recording, "id", None)
            url = getattr(recording, "contentUri", None)

            if not recording_id or not url:
                continue

            file_path = os.path.join("input_calls", f"{recording_id}.mp3")
            meta_path = os.path.join("call_metadata", f"{recording_id}.json")

            # Skip if already exists
            if os.path.exists(file_path):
                continue

            start_time = getattr(call, "startTime", None)

            # Track newest timestamp
            if start_time:
                newest_timestamp = max(
                    newest_timestamp or start_time,
                    start_time
                )

            metadata = {
                "recording_id": recording_id,
                "direction": getattr(call, "direction", "Unknown"),
                "start_time": start_time,
                "from": getattr(call, "from", {}),
                "to": getattr(call, "to", {}),
                "duration": getattr(call, "duration", None)
            }

            with open(meta_path, "w") as mf:
                json.dump(metadata, mf, indent=2, default=str)

            r = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )

            if r.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(r.content)

                print(f"Downloaded: {recording_id}")
                new_downloads += 1

            elif r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", 60))
                retry_after += random.uniform(0, 3)

                print(f"Rate limited. Sleeping {retry_after:.1f}s")
                time.sleep(retry_after)
                break

        except Exception as e:
            print(f"Error: {e}")

    # ----------------------------
    # UPDATE STATE
    # ----------------------------

    if newest_timestamp:
        state["last_sync"] = newest_timestamp
        save_state(state)

    print(f"Done. New downloads: {new_downloads}")


# ----------------------------
# ENTRY
# ----------------------------

if __name__ == "__main__":
    run_download_cycle()
