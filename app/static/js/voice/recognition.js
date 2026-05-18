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
let audioContext = null;
let analyser = null;
let vadFrame = null;
let silenceStartedAt = null;
let speechStarted = false;
const FALLBACK_MAX_RECORDING_MS = 8000;
const FALLBACK_MIN_RECORDING_MS = 1200;
const SILENCE_STOP_MS = 900;
const VOLUME_THRESHOLD = 0.025;

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
            const mimeType =
                MediaRecorder.isTypeSupported("audio/webm")
                    ? "audio/webm"
                    : "";
            mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
            audioChunks = [];
            speechStarted = false;
            silenceStartedAt = null;

            mediaRecorder.ondataavailable = event => {
                if (event.data && event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                isRecording = false;
                setListeningState(false);

                if (audioChunks.length > 0) {
                    const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || "audio/webm" });
                    sendAudioForTranscription(audioBlob);
                }

                cleanupAudioAnalysis();

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
                startVoiceActivityDetection(stream);
            };

            mediaRecorder.start();

            fallbackStopTimer = setTimeout(() => {
                if (mediaRecorder && mediaRecorder.state === "recording") {
                    mediaRecorder.stop();
                }
            }, FALLBACK_MAX_RECORDING_MS);
        })
        .catch(err => {
            logError(`Microphone access denied: ${err}`);
            alert('Microphone access is required for voice input.');
        });
}


function startVoiceActivityDetection(stream) {

    try {
        audioContext =
            new (window.AudioContext || window.webkitAudioContext)();
        analyser =
            audioContext.createAnalyser();
        analyser.fftSize = 1024;

        const source =
            audioContext.createMediaStreamSource(stream);
        source.connect(analyser);

        const samples =
            new Uint8Array(analyser.fftSize);

        const startedAt =
            Date.now();

        const tick = () => {
            if (!analyser || !mediaRecorder || mediaRecorder.state !== "recording") {
                return;
            }

            analyser.getByteTimeDomainData(samples);

            let total = 0;
            for (const sample of samples) {
                const centered =
                    (sample - 128) / 128;
                total += centered * centered;
            }

            const volume =
                Math.sqrt(total / samples.length);

            if (volume > VOLUME_THRESHOLD) {
                speechStarted = true;
                silenceStartedAt = null;
            }

            else if (speechStarted) {
                if (!silenceStartedAt) {
                    silenceStartedAt = Date.now();
                }

                if (
                    Date.now() - startedAt > FALLBACK_MIN_RECORDING_MS &&
                    Date.now() - silenceStartedAt > SILENCE_STOP_MS
                ) {
                    mediaRecorder.stop();
                    return;
                }
            }

            vadFrame =
                requestAnimationFrame(tick);
        };

        vadFrame =
            requestAnimationFrame(tick);
    } catch (err) {
        logError(`Voice activity detection unavailable: ${err}`);
    }
}


function cleanupAudioAnalysis() {

    if (vadFrame) {
        cancelAnimationFrame(vadFrame);
        vadFrame = null;
    }

    if (audioContext) {
        audioContext.close().catch(() => {});
        audioContext = null;
    }

    analyser = null;
    silenceStartedAt = null;
    speechStarted = false;
}

async function sendAudioForTranscription(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

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
                0: {
                    transcript: data.transcription,
                    confidence: data.confidence || 0.7
                },
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
    cleanupAudioAnalysis();
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
