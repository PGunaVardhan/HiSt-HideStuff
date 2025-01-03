# Account Manager file
# Includes functions that creates a user (sign up), logs a user in (sign in) and deletes a user and his/her data.

from upload import *
from getlist import *
from AES import *
from voice_utils import *
import sys
import time
import random
import numpy as np
import string
from gesture_auth import *


# For easily printing coloured text.
def print_colored(text, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m',
        'end': '\033[0m',
    }
    return colors[color] + text + colors['end']


# Generate a custom OTP (One-Time Password).
# Returns a 6-digit OTP as a string.
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


# Creates a user, Uploads his/her username, features of his noise seperated voice to the s3 bucket corresponding to the user.
def createuser(s3):
    print("")
    print("\nDo NOT use any UPPERCASE letters in the username !!! \n")
    username = input("\nUsername: ")
    success = False

    # Creates an s3 bucket in aws if the voice features of the user are successfully extracted.
    while not success:
        success = createbucket(username, s3)
        if not success:
            print("Username " + username + " not available. Please try again.")
            username = input("Username: ")

    try:
        print("\nSpeak the following phrase clearly: Hello HiSt. I want to Hide Stuff.")
        input("Press Enter when you are ready to record your voice:")

        # Extract voice features for authentication
        voice_features, text_spoken = extract_voice_features_and_text()
        voice_features = np.array2string(voice_features, separator=',')

        # Creates folders to store user data and uploads to cloud along with the voice features.
        s3.put_object(Bucket=username, Key='files/', Body='')
        s3.put_object(Bucket=username, Key='folders/', Body='')
        s3.put_object(Bucket=username, Key='passwords/', Body='')
        s3.put_object(Bucket=username, Key='voicefeatures', Body=voice_features)

        print(print_colored("\nRegistration successful! Your voice has been saved.", "magenta"))
        login = True

    except Exception as e:
        print(f"Error in Signing you up: {e}")
        login = False

    return username, login


# For a user to log in; Processes the authentication in 2 phases.
# Phase 1 : Voice Authentication; User will be prompted with an OTP.
# If the features of the noise isolated voice in which the OTP is spoken matches with the voice features of the owner corresponding to the username
# in which they tried to login AND the text that is extracted from the voice matches with the OTP, User is granted with Phase 1 Authentication.
# Phase 2 : Gesture Authentication; User will be required to draw a star symbol with the LMB of the mouse clicked, If the content the user has drawn
# matches the pre defined template with reasonable tolerence (25 percent), User is granted Phase 2 Authentication.
def signin(s3):
    login = False
    while not login:
        print(print_colored("\nStarting Sign-In Process...", "blue"))
        username = input("Username: ")

        # Phase 1: Voice Authentication
        random_phrase = generate_otp()
        print(print_colored("Phase 1: Voice Authentication...", "blue"))
        print(f"\nSpeak the following phrase clearly: '{random_phrase}'")
        input("Press Enter when you are ready to record your voice:")

        # Extract voice features for verification
        user_voice_features, text_spoken = extract_voice_features_and_text()
        try:
            stored_voice_features = s3.get_object(Bucket=username, Key='voicefeatures')['Body'].read()
            stored_voice_features = np.array(eval(stored_voice_features))

            if match_voice_features(user_voice_features, stored_voice_features) and compare_strings(text_spoken, random_phrase):
                print(print_colored("Phase 1: Voice Authentication Successful!", "magenta"))

                # Phase 2: Gesture Authentication
                print(print_colored("\nProceeding to Phase 2: Gesture Authentication...", "blue"))
                gesture_success = gesture_auth()

                if gesture_success:
                    print(print_colored("Login Successful! Both phases completed.", "green"))
                    login = True
                else:
                    print(print_colored("Phase 2 : Gesture Authentication failed. Retry from the beginning.", "red"))

            else:
                print("\nPrompt given: " + random_phrase)
                print("Text recorded: " + text_spoken + "\n")
                if not match_voice_features(user_voice_features, stored_voice_features):
                    print(print_colored("Voice authentication failed. Your voice does not match the owner's account.", "red"))
                else:
                    print(print_colored("Voice authentication failed. Try again and pronounce the OTP clearly.", "red"))

        except Exception as e:
            print(f"Error during login: {e}")

    return username, login


# Deletes a user and all their data after Processing Phase 1 authentication with a fixed default string and Phase 2 authentication.
def deleteuser(username, s3):
    print(print_colored("\nStarting Account Deletion Process...", "blue"))

    # Phase 1: Voice Authentication
    print("\nSpeak the following phrase to confirm deletion: 'Delete my account now.'")
    input("Press Enter when you are ready to record your voice:")

    # Extract voice features for deletion confirmation
    user_voice_features, text_spoken = extract_voice_features_and_text()

    try:
        stored_voice_features = s3.get_object(Bucket=username, Key='voicefeatures')['Body'].read()
        stored_voice_features = np.array(eval(stored_voice_features))

        if match_voice_features(user_voice_features, stored_voice_features) and compare_strings(text_spoken, "Delete my account now."):
            print(print_colored("Phase 1: Voice Authentication Successful!", "magenta"))

            # Phase 2: Gesture Authentication
            print(print_colored("\nProceeding to Phase 2: Gesture Authentication...", "blue"))
            gesture_success = gesture_auth()

            if gesture_success:
                print(print_colored("Phase 2: Gesture Authentication Successful!", "green"))
                objects = s3.list_objects_v2(Bucket=username).get('Contents', [])
                for obj in objects:
                    s3.delete_object(Bucket=username, Key=obj['Key'])

                s3.delete_bucket(Bucket=username)
                print(f"\nUser '{username}' deleted successfully.")
                print(print_colored("\n--------------- RESTART HIST! ---------------\n", "red"))
            else:
                print(print_colored("Phase 2: Gesture Authentication failed. Deletion aborted. Use keybindings to try again", "red"))

        else:
            print("\nPrompt given: Delete my account now")
            print("Text recorded: " + text_spoken + "\n")
            print(print_colored("Voice authentication failed. Deletion aborted. Use keybindings to try again", "red"))

    except Exception as e:
        print(f"Error during deletion: {e}")
