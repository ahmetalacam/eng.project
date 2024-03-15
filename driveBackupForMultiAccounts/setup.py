import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from apiclient.http import MediaFileUpload


class MyDrive():
    def __init__(self, credentials_file, token_file, scopes):
        self.SCOPES = scopes
        creds = None
        
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_file, "w") as token:
                token.write(creds.to_json())

        self.service = build("drive", "v3", credentials=creds)

    def list_files(self, page_size=10):
        results = self.service.files().list(pageSize=page_size, fields="nextPageToken, files(id, name)").execute()
            
        items = results.get("files", [])

        if not items:
            print("No files found.")
        else:
            print("Files:")
            for item in items:
                print(f"{item['name']} ({item['id']})")


    def upload_file(self, filename, path):
        folder_id = "1Df1yPb-gek0DoMBLY0iG4bfzcEOBJAE4"
        media = MediaFileUpload(f"{path}{filename}", mimetype='image/jpg')

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
                update_file = self.service.files().update(fileId=file.get('id'), media_body=media,).execute()
                print(f'updated File')
        

def main():
    path = "C:/Users/ahmet/Desktop/yedek/"
    files = os.listdir(path)
    
    # Örnekleri oluşturmak için gerekli bilgileri tanımlayın
    credentials_files = ["credentials2.json", "credentials1.json"]  # farklı OAuth istemcileri için credentials dosyaları
    token_files = ["token2.json", "token1.json"]  # farklı OAuth istemcileri için token dosyaları
    scopes_list = [
        ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file"],  # ilk istemci için kapsamlar
        ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file"]   # ikinci istemci için kapsamlar 
    ]

    # Her bir örneği oluşturun ve işlem yapın
    for i, (credentials_file, token_file, scopes) in enumerate(zip(credentials_files, token_files, scopes_list), 1):
        print(f"Processing client {i}")
        my_drive = MyDrive(credentials_file, token_file, scopes)
        # my_drive.list_files()

        for item in files:
            my_drive.upload_file(item, path)


if __name__ == "__main__":
    main()
