"""Speech processing helpers for the voice-based examination system."""

import whisper
import tempfile
import os

# Load the model once
model = None

def get_whisper_model():
    global model
    if model is None:
        model = whisper.load_model("base")  # Use base model for efficiency
    return model

def transcribe_audio(audio_bytes):
    try:
        model = get_whisper_model()
        # Save audio bytes to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        # Transcribe
        result = model.transcribe(temp_file_path)
        
        # Clean up
        os.unlink(temp_file_path)
        
        return result['text'].strip()
    except Exception as e:
        return f'Transcription failed: {str(e)}'

def validate_audio_format(filename: str) -> bool:
    return filename.lower().endswith(('.wav', '.mp3', '.ogg', '.m4a'))
