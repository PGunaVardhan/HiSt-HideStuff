# HiSt - Hide Stuff
 HiSt-HideStuff is a Python-based command-line application designed for user authentication and data management with advanced security protocols. It utilizes voice-based and gesture-based authentication to ensure secure access and provides seamless integration with AWS S3 for cloud storage. The platform encrypts all user data before uploading it to the cloud, ensuring privacy and security.

<br>

# Usage

Download Hist.exe from the google drive link in "app_link" or Open the content as a folder in your compiler and run HiSt.py in the terminal.

![icon](https://github.com/user-attachments/assets/98f1d7fa-bd8f-4c84-b36a-021ac67c5326)

## Features

1. **User Registration:**
   - Users choose a unique username.
   - Voice recording of a predefined sentence: "Hello HiSt, I want to hide stuff."
   - Noise reduction is applied to the recorded voice.
   - Features of the processed voice are extracted and saved in a file named `voice_features`.
   - An Amazon S3 bucket is created for the user with three predefined folders:
     - `Files`
     - `Folders`
     - `Passwords`

2. **Two-Phase Authentication:**

   - **Phase 1: Voice-Based Authentication**
     - User inputs their username to log in.
     - A random OTP is generated and displayed.
     - User records the OTP in their voice.
     - The recorded audio undergoes:
       1. Feature matching with the stored `voice_features`.
       2. Speech-to-text conversion using the Whisper model to verify the OTP.
     - Both feature matching and OTP verification must succeed to pass Phase 1.

   - **Phase 2: Gesture-Based Authentication**
     - User is shown a predefined star template.
     - Using the mouse, the user draws the star on a computer vision-based whiteboard.
     - The drawn shape is compared with the template. Similarity must exceed 75% to pass Phase 2.

   - If either phase fails, the user is redirected to the sign-in page.

3. **Data Management Platform:**
   - **Upload Data:**
     - Files, folders, and passwords can be uploaded.
     - Data is encrypted using AES encryption with the user's voice features as the key.
     - Encrypted data is uploaded to the corresponding folder in the user’s S3 bucket.
   - **View Data:**
     - Users can view the contents of their S3 bucket.
   - **Download Data:**
     - Encrypted data is downloaded and decrypted using the same AES encryption key.
   - **Delete Data:**
     - Users can remove specific data from their S3 bucket.
   - **Delete Account:**
     - Users can delete their account and all associated data after passing the two-phase authentication.

---

## Workflow

1. **Signup:**
   - Choose a username.
   - Record the predefined sentence.
   - Process the audio for noise reduction and save features.
   - Create an S3 bucket and initialize folders.

2. **Login:**
   - Enter the username.
   - **Phase 1:** Record the OTP and pass voice-based authentication.
   - **Phase 2:** Draw the star shape and pass gesture-based authentication.

3. **Post-Login Actions:**
   - Upload data (files/folders/passwords).
   - View data in the cloud.
   - Download and decrypt data.
   - Remove specific data or delete the account.

---

## Technical Details

### a. Voice Isolation/Noise Reduction Technique:
   - **Method:** Spectral Subtraction.
   - **Reason:** Effective for removing stationary noise, such as background hum, while retaining the integrity of the voice signal. Although, other efficient methods like using a pre-trained models like EaseUS, Spectral subtraction is chosen to ensure computational efficiency and faster functioning of the application. 

### b. Speech-to-Text Method:
   - **Model:** OpenAI’s Whisper model.
   - **Reason:** High accuracy for extracting text from audio with robust handling of diverse accents and noise levels. "Tiny" model from available models has been chosen keeping the desired computational efficiency in mind.

### c. Gesture Recognition Approach:
   - **Feature:** Shape similarity comparison.
   - **Method:** Template matching with a predefined star shape, using cv2 contours.
   - **Metric:** Similarity score threshold of 75% to ensure robust and reliable recognition.

### d. Encryption Approach:
   - **Algorithm:** AES (Advanced Encryption Standard).
   - **Key Management:** The user’s voice features are utilized as the encryption key for both encryption and decryption processes.

### e. Cloud Storage Solution:
   - **Platform:** Amazon S3.
   - **Integration Steps:**
     1. AWS credentials configured using `boto3`.
     2. Buckets created dynamically based on usernames.
     3. Encrypted data stored in predefined folders within each user’s bucket.
     4. Data retrieval and deletion facilitated via S3 API.

---

HiSt-HideStuff ensures a secure, user-friendly, and efficient platform for managing sensitive data, combining cutting-edge authentication methods and encryption techniques with scalable cloud storage.


