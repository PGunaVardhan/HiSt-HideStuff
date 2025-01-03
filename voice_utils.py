# Manages Phase 1 : Voice based authentication.

import sounddevice as sd
import librosa
import numpy as np
import tempfile
from scipy.io import wavfile
from tqdm import tqdm
import time
import os
from scipy.signal import spectrogram
import whisper
import soundfile as sf
import re
import warnings


# Uses spectral subtraction method for voice isolation and reduces noises.
def spectral_subtraction(audio, sample_rate, noise_start=0, noise_duration=1):
    """
    Apply spectral subtraction to isolate voice and reduce noise.

    :param audio: Input audio signal (numpy array)
    :param sample_rate: The sample rate of the audio
    :param noise_start: The start time of the noise segment in seconds (default is the first second)
    :param noise_duration: Duration of noise segment in seconds (default is 1 second)

    :return: Audio signal with reduced noise.
    """
    try:
        # Define window size and overlap for STFT
        window_size = 1024
        overlap = 512

        # Compute the spectrogram (STFT)
        f, t, Zxx = spectrogram(audio, sample_rate, nperseg=window_size, noverlap=overlap, nfft=window_size)

        # Estimate the noise spectrum from the initial period of silence/noise
        noise_start_sample = int(noise_start * sample_rate)
        noise_end_sample = int((noise_start + noise_duration) * sample_rate)

        # Slice out the noise segment (this assumes the noise is at the beginning)
        noise_segment = audio[noise_start_sample:noise_end_sample]
        _, _, Zxx_noise = spectrogram(noise_segment, sample_rate, nperseg=window_size, noverlap=overlap, nfft=window_size)

        # Calculate the average noise spectrum
        noise_spectrum = np.mean(np.abs(Zxx_noise), axis=1)

        # Apply spectral subtraction
        magnitude = np.abs(Zxx)
        phase = np.angle(Zxx)

        # Subtract the noise spectrum from the audio's spectrum
        magnitude -= noise_spectrum[:, None]
        magnitude = np.maximum(magnitude, 0)  # Avoid negative magnitudes

        # Reconstruct the signal with the subtracted magnitude and original phase
        Zxx_clean = magnitude * np.exp(1j * phase)

        # Inverse STFT to get the cleaned audio signal
        clean_audio = librosa.istft(Zxx_clean, win_length=window_size, hop_length=overlap)

        return clean_audio
    except Exception as e:
        print(f"Error in spectral subtraction: {e}")
        return None


# To avoid warning messages from getting printed. Avoids confusion from user end.
def suppress_warnings():
    # Suppress specific warnings
    warnings.filterwarnings("ignore", category=UserWarning, message=".*inference on CPU when CUDA is available.*")
    warnings.filterwarnings("ignore", category=UserWarning, message=".*FP16 is not supported on CPU; using FP32 instead.*")
    warnings.filterwarnings("ignore", category=FutureWarning, message=".*torch.load.*")


# When ran, Records voice from the microphone when pressed enter for the next five seconds with a progress bar indicating the timer
# and returns a numpy array containing the features of the voice that is recorded and a string containing the text that is extracted from the audio.
def extract_voice_features_and_text():
    """
    Records audio from the microphone, extracts voice features with spectral subtraction for voice isolation,
    and transcribes the audio using the Whisper model.

    :return: A tuple containing a numpy array of extracted voice features and the transcribed text as a string.
    """
    try:
        # Suppress the warnings
        suppress_warnings()

        print("Recording will start now. Speak into the microphone.")
        duration = 5  # Record for 5 seconds
        sample_rate = 16000  # Sample rate for recording

        # Initialize the recording
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')

        # Countdown progress bar for the recording duration
        for _ in tqdm(range(duration), desc="Recording", unit="s"):
            time.sleep(1)

        sd.wait()  # Wait for the recording to finish
        print("Recording complete.")

        # Apply spectral subtraction to isolate voice
        audio_data_clean = spectral_subtraction(audio_data.flatten(), sample_rate)
        if audio_data_clean is None:
            print("Error isolating voice. Aborting feature extraction.")
            return None, None

        # Extract voice features (MFCCs)
        mfccs = librosa.feature.mfcc(y=audio_data_clean, sr=sample_rate, n_mfcc=13)
        voice_features = np.mean(mfccs.T, axis=0)  # Return the average MFCCs

        # Save the audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            temp_audio_path = temp_audio_file.name
            sf.write(temp_audio_path, audio_data, sample_rate)

        # Load the Whisper model (using 'tiny' model for efficiency)
        model = whisper.load_model("tiny", device="cpu")

        # Transcribe the recorded audio
        result = model.transcribe(temp_audio_path, language="en")

        # Cleanup: Remove the temporary audio file
        os.remove(temp_audio_path)

        # Return the transcribed text and voice features
        # Ensure proper encoding when printing or returning the result
        return voice_features, result.get("text", "")

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None


# Used for voice authentication to be granted only when the voice is owner's.
# Compares stored features and new features and returns true if the similarity is 98%.
def match_voice_features(stored_features, new_features, threshold=0.98):
    """
    Compares stored and new voice features to check if they match.

    :param stored_features: Stored voice features (numpy array).
    :param new_features: New voice features (numpy array).
    :param threshold: Cosine similarity threshold for a match.
    :return: True if features match, otherwise False.
    """
    try:
        # Normalize the feature vectors (this ensures the vectors are on the same scale)
        stored_features = stored_features / np.linalg.norm(stored_features)
        new_features = new_features / np.linalg.norm(new_features)

        # Compute the cosine similarity
        similarity = np.dot(stored_features, new_features)

        # Return True if similarity is above the threshold, else False
        return similarity >= threshold
    except Exception as e:
        print(f"Error matching features: {e}")
        return False


# Compares strings str1 and str 2, and based on a simple algorithm.
# Returns true if the similarity between strings is atleast 90%.
def compare_strings(str1, str2):
    # Function to clean and retain only numbers from a string
    def retain_numbers_only(s):
        return ''.join(filter(str.isdigit, s))

    # Check if extracted text contains only numbers, white spaces, commas, question marks, or exclamation marks
    if re.fullmatch(r'[\d\s,?.!]*', str1):
        # Convert str1 to retain only numbers
        str1_cleaned = retain_numbers_only(str1)
        str2_cleaned = retain_numbers_only(str2)
    else:
        # Perform the existing cleaning logic
        str1 = str1.lstrip().lower()
        str2 = str2.lstrip().lower()
        str1_cleaned = re.sub(r'[^\w\s]', '', str1)  # Remove all non-alphanumeric characters except spaces
        str2_cleaned = re.sub(r'[^\w\s]', '', str2)  # Same for the second string

    # Calculate the number of matching characters between the two cleaned strings
    matching_chars = sum(1 for a, b in zip(str1_cleaned, str2_cleaned) if a == b)

    # Calculate the percentage of matching characters
    match_percentage = matching_chars / max(len(str1_cleaned), len(str2_cleaned)) * 100

    # Check if the match percentage is 90% or more
    return match_percentage >= 90
