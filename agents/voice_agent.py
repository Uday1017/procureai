"""
Voice Agent — agents/voice_agent.py
======================================
What this does:
  - Records audio from the user's microphone
  - Sends the audio to Gemini for Speech-to-Text (STT)
  - After getting an answer, converts it to speech using gTTS
  - Returns both the transcribed text and the audio file

Why Gemini for STT?
  Gemini 1.5 Flash can directly process audio files — no separate
  Whisper setup needed. Just upload the audio and ask "transcribe this".

  For TTS (text → speech), we use gTTS (Google Text-to-Speech) which
  is free and produces natural-sounding voice output.

In a production system (what Supervity uses):
  - STT: Google Cloud Speech-to-Text API (more accurate, real-time streaming)
  - TTS: Google Cloud Text-to-Speech (better voices, SSML support)
  But for a portfolio project, this approach shows you understand the concept.
"""

from google import genai
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
import numpy as np
from gtts import gTTS
import tempfile
import os
from pathlib import Path


class VoiceAgent:
    """
    Handles voice input (microphone → text) and voice output (text → speech).
    """
    
    def __init__(self, api_key: str):
        """
        Args:
            api_key: Gemini API key
        """
        self.client = genai.Client(api_key=api_key)
        
        # Audio recording settings
        self.sample_rate = 16000  # 16kHz — standard for speech
        self.channels = 1         # Mono — sufficient for speech
    
    def record_audio(self, duration_seconds: int = 5) -> str:
        """
        Records audio from the default microphone.
        
        Args:
            duration_seconds: how long to record (default 5 seconds)
        
        Returns:
            Path to the saved .wav file
        """
        print(f"[Voice] 🎤 Recording for {duration_seconds} seconds...")
        
        # Record audio as numpy array
        audio_data = sd.rec(
            frames=int(duration_seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.int16  # 16-bit audio
        )
        sd.wait()  # Block until recording is done
        
        # Save to a temp WAV file
        tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wav_write(tmp_wav.name, self.sample_rate, audio_data)
        
        print(f"[Voice] ✓ Recorded audio saved to {tmp_wav.name}")
        return tmp_wav.name
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        Sends audio to Gemini for speech-to-text transcription.
        
        Gemini 1.5 Flash can directly process .wav, .mp3, .m4a files.
        It understands accents and technical procurement terminology well.
        
        Args:
            audio_path: path to the audio file
        
        Returns:
            Transcribed text string
        """
        print(f"[Voice] Transcribing audio with Gemini...")
        
        audio_file = self.client.files.upload(file=audio_path, config={"mime_type": "audio/wav"})
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                audio_file,
                "Transcribe this audio exactly as spoken. Return only the transcribed text, nothing else."
            ]
        )
        transcribed = response.text.strip()
        print(f"[Voice] ✓ Transcribed: '{transcribed}'")
        self.client.files.delete(name=audio_file.name)
        
        return transcribed
    
    def text_to_speech(self, text: str, output_path: str = None) -> str:
        """
        Converts answer text to speech using gTTS.
        
        Args:
            text: the answer to speak
            output_path: where to save the MP3 (auto-generates temp file if None)
        
        Returns:
            Path to the generated MP3 file
        """
        print(f"[Voice] Converting answer to speech...")
        
        if not output_path:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            output_path = tmp.name
        
        # gTTS generates speech in MP3 format
        # lang="en" with tld="co.in" gives Indian English accent (nice touch for Supervity!)
        tts = gTTS(text=text, lang="en", tld="co.in", slow=False)
        tts.save(output_path)
        
        print(f"[Voice] ✓ Speech saved to {output_path}")
        return output_path
    
    def record_and_transcribe(self, duration_seconds: int = 5) -> str:
        """
        Convenience method — records and transcribes in one call.
        
        Returns:
            Transcribed text from microphone input
        """
        audio_path = self.record_audio(duration_seconds)
        
        try:
            text = self.transcribe_audio(audio_path)
        finally:
            # Clean up local temp file
            if os.path.exists(audio_path):
                os.unlink(audio_path)
        
        return text