import { state }
from "./state.js";

import {
    RECOGNITION_LANGUAGE,
    MAX_ALTERNATIVES,
    RESTART_DELAY_MS
}
from "./config.js";

import {
    setListeningState
}
from "./ui.js";

import {
    log,
    logError
}
from "./logging.js";

import {
    handleTranscriptResult
}
from "./transcript.js";


let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let mediaStream = null;
let recognition = null;
let fallbackStopTimer = null;
const FALLBACK_RECORDING_MS = 5000;

export function safeStartRecognition() {
    clearTimeout(state.restartTimer);
    clearTimeout(fallbackStopTimer);

    if (!state.examActive || state.ttsActive) {
        return;
    }

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        startBrowserRecognition(SpeechRecognition);
        return;
    }

    startTranscriptionFallback();
}


function startBrowserRecognition(SpeechRecognition) {

    if (recognition && state.isListening) {
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = RECOGNITION_LANGUAGE;
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = MAX_ALTERNATIVES;

    recognition.onstart = () => {
        setListeningState(true);
        log("Listening started");
    };

    recognition.onresult = handleTranscriptResult;
    recognition.onend = handleRecognitionEnd;
    recognition.onerror = handleRecognitionError;

    try {
        recognition.start();
    } catch (err) {
        logError(`Recognition start failed: ${err}`);
        handleRecognitionEnd();
    }
}


function startTranscriptionFallback() {

    if (isRecording) {
        return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaStream = stream;
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                if (event.data && event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                isRecording = false;
                setListeningState(false);

                if (audioChunks.length > 0) {
                    const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
                    sendAudioForTranscription(audioBlob);
                }

                if (mediaStream) {
                    mediaStream.getTracks().forEach(track => track.stop());
                    mediaStream = null;
                }

                handleRecognitionEnd();
            };

            mediaRecorder.onstart = () => {
                setListeningState(true);
                isRecording = true;
                log('Recording started');
            };

            mediaRecorder.start();

            fallbackStopTimer = setTimeout(() => {
                if (mediaRecorder && mediaRecorder.state === "recording") {
                    mediaRecorder.stop();
                }
            }, FALLBACK_RECORDING_MS);
        })
        .catch(err => {
            logError(`Microphone access denied: ${err}`);
            alert('Microphone access is required for voice input.');
        });
}

async function sendAudioForTranscription(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    try {
        const response = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }

        // Create a fake event to pass to handleTranscriptResult
        const fakeEvent = {
            resultIndex: 0,
            results: [{
                0: { transcript: data.transcription },
                isFinal: true
            }]
        };

        handleTranscriptResult(fakeEvent);
    } catch (err) {
        logError(`Transcription failed: ${err}`);
    }
}

export function stopRecognition() {
    if (recognition) {
        recognition.onend = null;
        recognition.onerror = null;
        recognition.stop();
        recognition = null;
    }

    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
    }

    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }

    isRecording = false;
    setListeningState(false);
    clearTimeout(fallbackStopTimer);
}

function handleRecognitionEnd() {

    setListeningState(false);
    recognition = null;

    if (
        state.examActive &&
        !state.ttsActive
    ) {

        state.restartTimer =
            setTimeout(

                safeStartRecognition,

                RESTART_DELAY_MS
            );
    }
}


function handleRecognitionError(
    event
) {

    const ignorable = [

        "no-speech",
        "aborted"
    ];

    if (
        ignorable.includes(
            event.error
        )
    ) {

        log(
            "Mic idle — still listening..."
        );

        return;
    }

    logError(
        `Recognition error: ${event.error}`
    );

    if (
        event.error ===
        "not-allowed"
    ) {

        state.examActive = false;
    }
}
