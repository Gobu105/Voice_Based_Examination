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


const SpeechRecognition =

    window.SpeechRecognition ||

    window.webkitSpeechRecognition;


if (!SpeechRecognition) {

    alert(
        `
        Speech Recognition
        is not supported
        in this browser.
        `
    );
}


export const recognition =
    new SpeechRecognition();


recognition.lang =
    RECOGNITION_LANGUAGE;

recognition.continuous = true;

recognition.interimResults = true;

recognition.maxAlternatives =
    MAX_ALTERNATIVES;


recognition.onresult =
    handleTranscriptResult;

recognition.onerror =
    handleRecognitionError;

recognition.onend =
    handleRecognitionEnd;

recognition.onstart = () => {

    setListeningState(true);
};


export function safeStartRecognition() {

    clearTimeout(
        state.restartTimer
    );

    try {

        recognition.start();

    } catch (_) {

        // already running
    }
}


export function stopRecognition() {

    try {

        recognition.stop();

    } catch (_) {

        // ignore
    }
}


function handleRecognitionEnd() {

    setListeningState(false);

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