import os
import time

def purge_old_files():
    now = time.time()
import os
import time

# Folders to keep lean
FOLDERS_TO_CLEAN = ["input_calls", "call_metadata"]
DAYS_TO_KEEP = 7
SECONDS_IN_DAY = 86400

def purge_old_files():
    now = time.time()
    cutoff = now - (DAYS_TO_KEEP * SECONDS_IN_DAY)

    for folder in FOLDERS_TO_CLEAN:
        if not os.path.exists(folder): continue
        
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            # Check if the file is older than the cutoff
            if os.path.getmtime(file_path) < cutoff:
                os.remove(file_path)
                print(f"🧹 Purged old file: {filename}")

if __name__ == "__main__":
    purge_old_files()
