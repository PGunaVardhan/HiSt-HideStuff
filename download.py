# Contains the functions that manages the workflow when the user wants to download their data (Ctrl+D keybinding)

import os
import boto3
from botocore.exceptions import NoCredentialsError
from secret import aws_access_key_id as aws_access_key_id
from secret import aws_secret_access_key as aws_secret_access_key
from tqdm import tqdm
import json
import tkinter as tk
from tkinter import filedialog
from safefile import *
import shutil
from AES import *


# To download a file.
def downloadfile(username, filename, downpath, s3):
    bucket_name = username
    key = s3.get_object(Bucket=username, Key='voicefeatures')['Body'].read().decode('utf-8')

    local_file_path = downpath + "//" + filename
    s3_key = "files/" + filename

    # Callback for tqdm progress bar
    class TqdmCallback(tqdm):
        def update_to(self, bytes_amount):
            self.update(bytes_amount)

    try:
        # Get the file size for the progress bar
        response = s3.head_object(Bucket=bucket_name, Key=s3_key)
        file_size = response['ContentLength']

        # Download file with tqdm progress bar
        with TqdmCallback(total=file_size, unit='B', unit_scale=True, desc="Downloading file") as progress:
            s3.download_file(bucket_name, s3_key, local_file_path, Callback=progress.update_to)

        # Decrypt the file
        oldfile = decfile(local_file_path, key)
        print("Download successful\n")
        os.remove(oldfile)

    except Exception as e:
        print(f"Error Downloading file: {e}\n")


# To download a folder.
def downloadfolder(username, folder_prefix, local_folder_path, s3):
    bucket_name = username
    key = s3.get_object(Bucket=username, Key='voicefeatures')['Body'].read().decode('utf-8')

    local_folder_path = os.path.join(local_folder_path, folder_prefix)
    os.makedirs(local_folder_path, exist_ok=True)

    try:
        # List all objects in the folder
        objects = s3.list_objects_v2(Bucket=bucket_name, Prefix="folders/" + folder_prefix).get('Contents', [])
        if objects:
            print("Downloading...")

            # Calculate total size of all files
            total_size = sum(obj['Size'] for obj in objects)

            # Progress bar initialization
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading Folder") as progress:

                for obj in objects:
                    s3_key = obj['Key']
                    rel_path = os.path.relpath(s3_key, "folders/" + folder_prefix)
                    local_file_path = os.path.join(local_folder_path, rel_path)

                    # Create necessary directories for nested folders
                    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

                    # Download file with progress updates
                    def progress_callback(bytes_amount):
                        progress.update(bytes_amount)

                    s3.download_file(bucket_name, s3_key, local_file_path, Callback=progress_callback)

            print("Download successful\n")

            oldfold = decfolder(local_folder_path, key)
            shutil.rmtree(oldfold)

        else:
            print("Folder is empty\n")

    except Exception as e:
        print(f"Error downloading folder: {e}\n")


# For downloading and displaying saved passwords.
def downloadpass(username, webname, s3):

    key = s3.get_object(Bucket=username, Key='voicefeatures')['Body'].read().decode('utf-8')

    try:
        response = s3.get_object(Bucket=username, Key="passwords/"+webname)
        content = response['Body'].read().decode('utf-8')
        data = json.loads(content)[0]
        uname = data.get("username")
        pword = data.get("password")
        pword = dec(pword, key)

        print(f"Credentials for the website {webname} : ")
        print(f"username/ email-id/ mobile number : {uname}")
        print(f"Password : {pword}\n")

        return content

    except FileNotFoundError:
        print(f"The website '{webname}' does not exist '{username}'.")
    except NoCredentialsError:
        print("Credentials not available or incorrect.")


# User chooses what to download and then enters the name of the content. Above functions are called accordingly.
def download(username, s3):
    print("\nAvaialble options to DOWNLOAD : \n 1. Files\n 2. Folders\n 3. Passwords\n")
    oper = input("Enter the index of the type of data you want to Download : ")
    if oper == "1":
        root = tk.Tk()
        root.withdraw()
        filename = input("Enter the name of the file you want to download : ")
        file_path = filedialog.askdirectory(title="Select a location to save the file")
        print("Decrypting and Downloading the file...")
        downloadfile(username, filename, file_path, s3)
    elif oper == "2":
        root = tk.Tk()
        root.withdraw()
        foldername = input("Enter the name of the folder you want to download : ")
        folder_path = filedialog.askdirectory(title="Select a location to save the folder")
        print("Decrypting and Downloading the folder...")
        downloadfolder(username, foldername, folder_path, s3)
    elif oper == "3":
        webname = input("Enter the name of the site : ")
        downloadpass(username, webname, s3)
    else:
        print("Invalid data type (index) selected. Please enter a valid index.")
