import os
import time
import threading
import schedule
from tkinter import *
from tkinter import filedialog
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyDrive:
    def __init__(self, output_text, selected_folder_id=None):
        self.output_text = output_text
        self.selected_folder_id = selected_folder_id
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
        if self.selected_folder_id is None:
            print("Error: Selected folder ID is not set.")
            return

        media = MediaFileUpload(os.path.join(path, filename), mimetype='image/jpg')

        response = self.service.files().list(q=f"name='{filename}' and parents='{self.selected_folder_id}'",
                                             spaces='drive', fields='nextPageToken, files(id, name)',
                                             pageToken=None).execute()
        if len(response['files']) == 0:
            file_metadata = {
                'name': filename,
                'parents': [self.selected_folder_id]
            }
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"A new file was created {file.get('id')}")
            self.output_text.insert(END, f"A new file was created {file.get('id')}\n")
        else:
            for file in response.get('files', []):
                update_file = self.service.files().update(fileId=file.get('id'), media_body=media).execute()
                print(f'Updated file')
                self.output_text.insert(END, f'Updated file\n')

class Watcher:
    def __init__(self, directory, output_text):
        self.output_text = output_text
        self.directory = directory
        self.event_handler = MyHandler(output_text)
        self.observer = Observer()

    def start(self):
        self.observer.schedule(self.event_handler, self.directory, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

class MyHandler(FileSystemEventHandler):

    def __init__(self, output_text):
        self.output_text = output_text

    def on_any_event(self, event):
        if event.is_directory:
            return None
        elif event.event_type == 'created':
            print(f"New file created: {event.src_path}")
            self.output_text.insert(END, f"New file created: {event.src_path}\n")
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
            self.output_text.insert(END, f"File modified: {event.src_path}\n")
            # Wait for the file to be accessible
            time.sleep(1)
            # Perform update here if needed
            filename = os.path.basename(event.src_path)
            try:
                my_drive.upload_file(filename, os.path.dirname(event.src_path))
            except PermissionError:
                print(f"Permission denied: {event.src_path}. Skipping upload.")

class FolderDialog:
    def __init__(self, parent):
        self.parent = parent
        self.drive = MyDrive(output_text)  # MyDrive sınıfınızı burada oluşturun veya geçirin
        self.folders = self.get_folders()

        self.dialog = Toplevel(parent)
        self.dialog.title("Select a Folder")
        self.dialog.geometry("300x400")

        self.listbox = Listbox(self.dialog, selectmode=SINGLE)
        self.listbox.pack(expand=True, fill=BOTH)

        for folder_name, folder_id in self.folders.items():
            self.listbox.insert(END, folder_name)

        self.select_button = Button(self.dialog, text="Select", command=self.select_folder)
        self.select_button.pack()

    def get_folders(self):
        folders = {}
        response = self.drive.service.files().list(q="mimeType='application/vnd.google-apps.folder'",
                                                   spaces='drive',
                                                   fields='files(id, name)').execute()
        for file in response.get('files', []):
            folders[file['name']] = file['id']
        return folders

    def show(self):
        self.parent.wait_window(self.dialog)
        if self.selected_folder_id:
            return self.selected_folder_id
        else:
            return None

    def select_folder(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_folder_name = self.listbox.get(selected_index)
            self.selected_folder_id = self.folders[selected_folder_name]
            self.dialog.destroy()

def cloud_browse():
    global my_drive, selected_folder_id
    folder_dialog = FolderDialog(root)
    selected_folder_id = folder_dialog.show()
    if selected_folder_id:
        print("Selected folder ID:", selected_folder_id)
        my_drive = MyDrive(output_text, selected_folder_id)  # MyDrive sınıfını seçilen klasör ID'si ile oluştur
    else:
        print("No folder selected.")

def local_browse():
    global folder_path
    filename = filedialog.askdirectory()
    folder_path.set(filename)

def start_backup():
    global watcher
    directory = folder_path.get()
    watcher = Watcher(directory, output_text)
    watcher.start()

def manual_backup():
    directory = folder_path.get()
    if not directory:  # Eğer dosya seçilmediyse
        print("Dosya seçilmedi.")
        return
    if os.path.isdir(directory):  # Eğer seçilen bir klasör ise
        files = os.listdir(directory)
        for item in files:
            my_drive.upload_file(item, directory)
    else:  # Eğer seçilen bir dosya ise
        filename = os.path.basename(directory)
        my_drive.upload_file(filename, os.path.dirname(directory))

def backup_thread():
    t = threading.Thread(target=start_backup)
    t.daemon = True
    t.start()

def stop_watch():
    watcher.stop()

def set_auto_backup(hour):
    schedule.every().day.at(hour).do(manual_backup)

def auto_backup_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    root = Tk()
    root.title("CLOUD-SCHEDULED BACKUP APPLICATION")
    root.geometry("1000x600")
    root.resizable(False, False)

    folder_path = StringVar()

    manual = Label(root, text="Get Manual Backup")
    manual.place(x=110, y=490)

    auto = Label(root, text="BACKUP OPTIONS:", font=25)
    auto.place(x=90, y=30)

    label = Label(root, text="Select Directory from Local for Backup:", font=25)
    label.place(x=600, y=30)

    label = Label(root, text="Choose Google-Drive Folder", font=25)
    label.place(x=650, y=150)

    entry = Entry(root, textvariable=folder_path, width=60)
    entry.place(x=595, y=85)

    cloud_browse_button = Button(root, text="Browse on Drive", fg="black", bg="yellow", command=cloud_browse).place(x=740, y=180)

    local_browse_button = Button(root, text='Browse on Local', fg="black", bg="yellow", command=local_browse).place(x=740, y=60)

    start_backup_button = Button(root, text="Auto Backup", bg="white", command=backup_thread, font=5)
    start_backup_button.place(x=100, y=100)
    watch = Label(root, text="Watch Directory")
    watch.place(x=250, y=110)

    manual_backup_button = Button(root, text="Manual Backup", bg="white", command=manual_backup, font=5)
    manual_backup_button.place(x=90, y=520)

    stop_watch_button = Button(root, text="Stop Watching", bg="white", command=stop_watch, font=5)
    stop_watch_button.place(x=95, y=170)
    stop = Label(root, text="Stop Watching Directory")
    stop.place(x=255, y=180)

    auto_backup_label = Label(root, text="Set Automatic Backup Time (HH:MM)")
    auto_backup_label.place(x=75, y=320)

    auto_backup_entry = Entry(root)
    auto_backup_entry.place(x=100, y=350)

    auto_backup_button = Button(root, text="Set A Task", fg="black", bg="yellow", command=lambda: set_auto_backup(auto_backup_entry.get()))
    auto_backup_button.place(x=130, y=375)

    output_text = Text(root, wrap=WORD, width=40, height=10)
    output_text.place(x=620, y=265)

    my_drive = None

    auto_backup_thread = threading.Thread(target=auto_backup_thread)
    auto_backup_thread.daemon = True
    auto_backup_thread.start()

    root.mainloop()
