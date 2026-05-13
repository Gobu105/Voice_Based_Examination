"""Speech processing helpers for the voice-based examination system."""


def transcribe_audio(audio_bytes):
    return 'Transcription unavailable. Speech service is not configured.'


def validate_audio_format(filename: str) -> bool:
    return filename.lower().endswith(('.wav', '.mp3', '.ogg', '.m4a'))
