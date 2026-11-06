import os
import cv2
import pathlib
import requests
from datetime import datetime
import time


class ChangeDetection:
    HOST = "http://127.0.0.1:8000"

    def __init__(self, names):
        self.result_prev = [0 for _ in names]
        self.token = None
        self.last_upload_time = float("-inf")
        self.upload_interval = 30

    def get_token(self):
        username = os.environ.get("DJANGO_USERNAME")
        password = os.environ.get("DJANGO_PASSWORD")

        if not username or not password:
            raise RuntimeError("Django credentials are not configured")

        response = requests.post(
            self.HOST + "/api-token-auth/",
            data={"username": username, "password": password},
            timeout=10
        )
        response.raise_for_status()
        self.token = response.json()["token"]
        return self.token

    
    def add(self, names, detected_current, save_dir, image):
        self.title = ""
        self.text = ""
        change_flag = False

        for i in range(len(self.result_prev)):
            if self.result_prev[i] == 0 and detected_current[i] == 1:
                change_flag = True
                self.title = names[i]
                self.text += names[i] + ", "

        self.result_prev = detected_current[:]

        
        if change_flag and time.monotonic() - self.last_upload_time >= self.upload_interval:
            self.send(save_dir, image)
            self.last_upload_time = time.monotonic()


    
    def send(self, save_dir, image):
        if self.token is None:
            self.get_token()

        image_path = pathlib.Path(save_dir) / "detected.jpg"
        cv2.imwrite(str(image_path), image)

        headers = {
            "Authorization": f"Token {self.token}"
        }

        data = {
            "title": self.title,
            "text": self.text,
        }

        with open(image_path, "rb") as img_file:
            files = {
                "image": ("detected.jpg", img_file, "image/jpeg")
            }

            response = requests.post(
                self.HOST + "/api_root/Post/",
                headers=headers,
                data=data,
                files=files,
                timeout=30
            )

        response.raise_for_status()
        print("Uploaded successfully:", response.status_code)



