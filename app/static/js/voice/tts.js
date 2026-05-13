import { state }
from "./state.js";

import {
    COOLDOWN_AFTER_TTS_MS
}
from "./config.js";

import {
    safeStartRecognition
}
from "./recognition.js";


export function initializeVoices() {

    if (!window.speechSynthesis) {
        return;
    }

    window.speechSynthesis.getVoices();

    window.speechSynthesis.onvoiceschanged =
        () => {

            window.speechSynthesis
                .getVoices();
        };
}


export function speak(text) {

    window.speechSynthesis.cancel();

    state.ttsActive = true;

    const utterance =
        new SpeechSynthesisUtterance(text);

    utterance.lang = "en-IN";

    utterance.rate = 0.92;

    utterance.pitch = 1.0;

    const voices =
        window.speechSynthesis.getVoices();

    const indianVoice =
        voices.find(
            v =>
                v.lang === "en-IN" ||
                v.lang.startsWith("en-IN")
        );

    if (indianVoice) {
        utterance.voice = indianVoice;
    }

    if (state.examActive) {

        utterance.onend = () => {

            state.cooldownUntil =
                Date.now() +
                COOLDOWN_AFTER_TTS_MS;

            setTimeout(() => {

                speakCue(
                    "You may speak now."
                );

            }, COOLDOWN_AFTER_TTS_MS);
        };
    }

    window.speechSynthesis
        .speak(utterance);
}


export function speakCue(text) {

    window.speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(text);

    utterance.lang = "en-IN";

    utterance.rate = 1.1;

    const voices =
        window.speechSynthesis.getVoices();

    const indianVoice =
        voices.find(
            v =>
                v.lang === "en-IN" ||
                v.lang.startsWith("en-IN")
        );

    if (indianVoice) {
        utterance.voice = indianVoice;
    }

    utterance.onend = () => {

        state.ttsActive = false;

        state.cooldownUntil =
            Date.now() + 400;

        setTimeout(() => {

            safeStartRecognition();

        }, 400);
    };

    window.speechSynthesis
        .speak(utterance);
}