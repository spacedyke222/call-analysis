from ringcentral import SDK
from dotenv import load_dotenv
import os
import requests
import json
import time
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

_platform = None  # singleton cache


def get_platform():
    """
    Create and cache a single authenticated RingCentral platform instance.
    Prevents repeated login calls that cause 429 rate limits.
    """
    global _platform

    if _platform is None:
        try:
            _platform = rcsdk.platform()
            _platform.login(jwt=os.environ.get("RC_USER_JWT"))
            print("Log in successful.")
        except Exception as e:
            print(f"Login failed: {e}")
            raise e

    return _platform


# ----------------------------
# CALL FETCHING
# ----------------------------

def get_recent_calls(platform, retries=5):
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
            print(f"❌ RingCentral API Error: {e}")

            if hasattr(e, 'response'):
                print(f"Details: {e.response.text}")

            wait = 2 ** i
            print(f"Retry {i+1}/{retries} in {wait}s...")
            time.sleep(wait)

    return None


# ----------------------------
# MAIN DOWNLOAD PIPELINE
# ----------------------------

def run_download_cycle():
    os.makedirs("input_calls", exist_ok=True)
    os.makedirs("call_metadata", exist_ok=True)

    platform = get_platform()

    response = get_recent_calls(platform)
    if not response:
        print("Could not fetch logs from RingCentral.")
        return

    calls = response.json().records
    token = platform.auth().data()["access_token"]

    new_downloads = 0

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

            # Skip already processed calls
            if os.path.exists(file_path):
                continue

            # ----------------------------
            # METADATA
            # ----------------------------
            metadata = {
                "recording_id": recording_id,
                "direction": getattr(call, "direction", "Unknown"),
                "start_time": getattr(call, "startTime", None),
                "from": getattr(call, "from", {}),
                "to": getattr(call, "to", {}),
                "duration": getattr(call, "duration", None)
            }

            with open(meta_path, "w") as mf:
                json.dump(metadata, mf, indent=2, default=str)

            # ----------------------------
            # DOWNLOAD RECORDING
            # ----------------------------
            r = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )

            if r.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(r.content)

                print(f"✅ Downloaded: {recording_id} ({metadata['direction']})")
                new_downloads += 1

            elif r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", 60))
                print(f"⚠️ Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                break

        except Exception as e:
            print(f"❌ Error processing record {getattr(call, 'id', 'unknown')}: {e}")

    if new_downloads == 0:
        print("No new recordings found since last check.")
    else:
        print(f"Finished. Total new calls downloaded: {new_downloads}")


# ----------------------------
# ENTRYPOINT
# ----------------------------

if __name__ == "__main__":
    run_download_cycle()
