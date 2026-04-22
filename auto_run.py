import subprocess
import time
import sys
import os

def run_service(script_name):
    """
    Returns True if the script finished successfully, False otherwise.
    """
    print(f"\n🚀 Starting: {script_name}...")
    try:
        # We use subprocess.run without check=True here so we can capture the exit code manually
        result = subprocess.run([sys.executable, script_name])
        
        if result.returncode == 0:
            print(f"✅ {script_name} finished successfully.")
            return True
        else:
            print(f"⚠️ {script_name} failed with exit code {result.returncode}.")
            return False
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

# --- THE MASTER LOOP ---
if __name__ == "__main__":
    print("🔔 Clean Market AI Pipeline Initialized")
    
    while True:
        # 1. Download new calls
        # If this fails, we stop the cycle and wait for the next hour
        if run_service("download_calls.py"):
            
            # 2. Transcribe and Score
            run_service("process_calls.py")
            
            # 3. Purge files older than 30 days
            run_service("cleanup.py")
            
        else:
            print("🛑 Skipping Processing/Cleanup because Download failed. Check RingCentral connection.")

        # 4. Wait logic 
        print(f"\n[{time.strftime('%H:%M:%S')}] Cycle complete.")
        print("😴 System idling... (Keep this window open)")
        
        time.sleep(60) # 60 seconds = 1 minute
