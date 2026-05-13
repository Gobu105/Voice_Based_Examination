import { state }
from "./state.js";

import {
    normalize
}
from "./normalization.js";

import {
    showInterim,
    showFinal,
    updateAnswerDisplay
}
from "./ui.js";

import {
    log
}
from "./logging.js";

import {
    matchCommand
}
from "./command_matcher.js";

import {
    COMMANDS
}
from "./commands.js";

import {
    saveAnswerAPI
}
from "./api.js";

import {
    speak
}
from "./tts.js";


export function handleTranscriptResult(
    event
) {

    let interim = "";

    let finalTranscript = "";

    for (
        let i = event.resultIndex;
        i < event.results.length;
        i++
    ) {

        const transcript =
            event.results[i][0]
                .transcript;

        if (
            event.results[i]
                .isFinal
        ) {

            finalTranscript +=
                transcript;
        }

        else {

            interim += transcript;
        }
    }

    if (interim) {

        showInterim(interim);
    }

    if (finalTranscript) {

        const normalized =
            normalize(
                finalTranscript
            );

        showFinal(normalized);

        processTranscript(
            normalized
        );
    }
}


export async function processTranscript(
    text
) {

    if (
        Date.now() <
        state.cooldownUntil
    ) {

        log(
            `
            Ignored during cooldown
            `
        );

        return;
    }

    // command matching
    const cmd =
        matchCommand(
            text,
            COMMANDS
        );

    if (cmd) {

        log(
            `
            Command recognized:
            ${cmd.name}
            `
        );

        cmd.action();

        return;
    }

    // save answer
    if (
        state.currentIndex >= 0 &&
        state.currentIndex <
        state.questions.length
    ) {

        state.answers[
            state.currentIndex
        ] = text;

        updateAnswerDisplay();

        const questionId =
            state.questionIds[
                state.currentIndex
            ];

        try {

            const result =
                await saveAnswerAPI(
                    questionId,
                    text
                );

            if (result.error) {

                log(
                    `
                    Save error:
                    ${result.error}
                    `
                );

                speak(
                    `
                    Error saving answer.
                    Please repeat.
                    `
                );

                return;
            }

            state.lastSavedAt =
                new Date();

            log(
                `
                Answer saved for
                question ${
                    state.currentIndex + 1
                }
                `
            );

            speak(
                `
                Answer recorded.
                `
            );

        } catch (err) {

            log(
                `
                Network save error:
                ${err}
                `
            );

            speak(
                `
                Network issue.
                Answer saved locally.
                `
            );
        }
    }

    else {

        speak(
            `
            Say next question
            to begin.
            `
        );
    }
}