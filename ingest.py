import os, fitz, re, requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

# --- CONFIG ---
MASTER_PDF_PATH = "CM_Knowledge_Base.pdf" 
LAKE_DIR = "content_lake"
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

if not os.path.exists(LAKE_DIR): os.makedirs(LAKE_DIR)

def get_gdrive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token: token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def get_file_metadata(service, file_id):
    try:
        # Added supportsAllDrives=True for corporate Shared Drives
        file = service.files().get(fileId=file_id, fields='name', supportsAllDrives=True).execute()
        return file.get('name', 'unknown_file')
    except HttpError as e:
        if e.resp.status == 404:
            return None # Signal that the file is inaccessible
        raise

def download_doc(service, file_id, name):
    try:
        print(f"📥 Downloading Doc: {name}")
        request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        with open(os.path.join(LAKE_DIR, f"{name}.txt"), "wb") as f:
            f.write(request.execute())
    except Exception as e:
        print(f"⚠️ Could not download {name}: {e}")

def download_sheet(service, file_id, name):
    try:
        print(f"📊 Exporting Sheet: {name}")
        request = service.files().export_media(fileId=file_id, mimeType='text/csv')
        with open(os.path.join(LAKE_DIR, f"{name}.csv"), "wb") as f:
            f.write(request.execute())
    except Exception as e:
        print(f"⚠️ Could not download sheet {name}: {e}")

def scrape_website(url, index):
    print(f"🌐 Scraping Web: {url}")
    try:
        response = requests.get(f"https://r.jina.ai/{url}", timeout=10)
        if response.status_code == 200:
            # Try to sanitize the filename from the URL
            clean_name = re.sub(r'\W+', '_', url.split('//')[-1])[:50]
            with open(os.path.join(LAKE_DIR, f"web_{clean_name}.md"), "w") as f:
                f.write(response.text)
    except:
        print(f"❌ Failed to scrape {url}")

if __name__ == "__main__":
    service = get_gdrive_service()
    doc = fitz.open(MASTER_PDF_PATH)
    links = list(set([l['uri'] for p in doc for l in p.get_links() if 'uri' in l]))
    
    print(f"Found {len(links)} links. Populating Lake...")
    
    for i, link in enumerate(links):
        file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', link)
        
        if file_id_match and "docs.google.com" in link:
            fid = file_id_match.group(1)
            name = get_file_metadata(service, fid)
            
            if name: # Only proceed if we actually found/have access to the file
                if "document" in link:
                    download_doc(service, fid, name)
                elif "spreadsheets" in link:
                    download_sheet(service, fid, name)
            else:
                print(f"🚫 Access Denied or File Missing: {link}")
        
        elif link.startswith("http"):
            # Skip common non-content links
            if "google.com/maps" in link or "asana.com" in link:
                print(f"⏭️ Skipping utility link: {link}")
                continue
            scrape_website(link, i)

    print("\n✅ Ingestion complete. Check your 'content_lake' folder!")
