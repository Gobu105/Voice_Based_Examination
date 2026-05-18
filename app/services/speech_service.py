"""Speech processing helpers for the voice-based examination system."""

import whisper
import tempfile
import os
from pathlib import Path

# Load the model once
model = None

def get_whisper_model():
    global model
    if model is None:
        model = whisper.load_model("base")  # Use base model for efficiency
    return model

def transcribe_audio(audio_bytes, filename='recording.webm'):
    temp_file_path = None
    try:
        model = get_whisper_model()
        suffix = Path(filename or 'recording.webm').suffix or '.webm'

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name

        result = model.transcribe(
            temp_file_path,
            language='en',
            task='transcribe',
            fp16=False,
            condition_on_previous_text=False,
            no_speech_threshold=0.55,
            logprob_threshold=-1.0,
            initial_prompt=(
                "Indian English academic examination answer. "
                "Short voice commands may include next question, previous question, "
                "repeat question, clear answer, submit exam, yes, or no."
            ),
        )

        segments = result.get('segments') or []
        if segments:
            avg_logprob = sum(s.get('avg_logprob', -1.0) for s in segments) / len(segments)
            no_speech_prob = sum(s.get('no_speech_prob', 0.0) for s in segments) / len(segments)
            confidence = max(0.0, min(1.0, (avg_logprob + 1.0) * (1.0 - no_speech_prob)))
        else:
            confidence = 0.0

        return {
            'text': result.get('text', '').strip(),
            'confidence': round(confidence, 3),
            'language': result.get('language', 'en'),
            'segments': len(segments),
        }
    except Exception as e:
        raise RuntimeError(f'Transcription failed: {str(e)}') from e
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

def validate_audio_format(filename: str) -> bool:
    return filename.lower().endswith(('.wav', '.mp3', '.ogg', '.m4a', '.webm'))
