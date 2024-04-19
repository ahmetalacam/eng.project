import os
import time
import threading
from tkinter import *
from tkinter import filedialog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class MyDrive:
    def __init__(self):
        SCOPES = ["https://www.googleapis.com/auth/drive"]
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        self.service = build("drive", "v3", credentials=creds)

    def upload_file(self, filename, path):
        folder_id = "1TGkwMBizK-a6lytbTM0iivEcn69mfBOi"
        media = MediaFileUpload(os.path.join(path, filename), mimetype='image/jpg')

        response = self.service.files().list(q=f"name='{filename}' and parents='{folder_id}'",
                                             spaces='drive', fields='nextPageToken, files(id, name)',
                                             pageToken=None).execute()
        if len(response['files']) == 0:
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"A new file was created {file.get('id')}")
        else:
            for file in response.get('files', []):
                update_file = self.service.files().update(fileId=file.get('id'), media_body=media).execute()
                print(f'Updated file')

class Watcher:
    def __init__(self, directory):
        self.directory = directory
        self.event_handler = MyHandler()
        self.observer = Observer()

    def start(self):
        self.observer.schedule(self.event_handler, self.directory, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            return None
        elif event.event_type == 'created':
            print(f"New file created: {event.src_path}")
            # Wait for the file to be accessible
            time.sleep(1)
            # Perform upload or update here
            filename = os.path.basename(event.src_path)
            try:
                my_drive.upload_file(filename, os.path.dirname(event.src_path))
            except PermissionError:
                print(f"Permission denied: {event.src_path}. Skipping upload.")
        elif event.event_type == 'modified':
            print(f"File modified: {event.src_path}")
            # Wait for the file to be accessible
            time.sleep(1)
            # Perform update here if needed
            filename = os.path.basename(event.src_path)
            try:
                my_drive.upload_file(filename, os.path.dirname(event.src_path))
            except PermissionError:
                print(f"Permission denied: {event.src_path}. Skipping upload.")


def browse_button():
    global folder_path
    filename = filedialog.askdirectory()
    folder_path.set(filename)

def start_backup():
    directory = folder_path.get()
    watcher = Watcher(directory)
    watcher.start()

def manual_backup():
    directory = folder_path.get()
    files = os.listdir(directory)
    for item in files:
        my_drive.upload_file(item, directory)

def backup_thread():
    t = threading.Thread(target=start_backup)
    t.daemon = True
    t.start()

def stop_watch():
    directory = folder_path.get()
    watcher = Watcher(directory)
    watcher.stop()

if __name__ == "__main__":
    root = Tk()
    root.title("Backup Application")

    folder_path = StringVar()

    label = Label(root, text="Select directory to monitor:")
    label.pack()

    entry = Entry(root, textvariable=folder_path, width=50)
    entry.pack()

    browse_button = Button(root, text="Browse", command=browse_button)
    browse_button.pack()

    start_backup_button = Button(root, text="Start Backup", command=backup_thread)
    start_backup_button.pack()

    manual_backup_button = Button(root, text="Manual Backup", command=manual_backup)
    manual_backup_button.pack()

    stop_watch_button = Button(root, text="Stop Watching", command=stop_watch)
    stop_watch_button.pack()

    my_drive = MyDrive()

    root.mainloop()
