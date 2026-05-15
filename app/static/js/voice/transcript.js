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
    COMMANDS,
    cmdGoToQuestion
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
    const commandText =
        text
            .toLowerCase()
            .replace(/[^\w\s]/g, "")
            .trim();

    const goToMatch =
        commandText.match(
            /^(?:go to|show|display|open)?\s*question\s+(\d+)$/
        ) ||
        commandText.match(
            /^go to question number\s+(\d+)$/
        );

    if (goToMatch) {

        cmdGoToQuestion(
            Number(goToMatch[1])
        );

        return;
    }

    const cmd =
        matchCommand(
            commandText,
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

        const existingAnswer =
            state.answers[
                state.currentIndex
            ];

        const combinedAnswer =
            existingAnswer
                ? `${existingAnswer} ${text}`.trim()
                : text;

        state.answers[
            state.currentIndex
        ] = combinedAnswer;

        updateAnswerDisplay();

        const questionId =
            state.questionIds[
                state.currentIndex
            ];

        try {

            const result =
                await saveAnswerAPI(
                    questionId,
                    combinedAnswer
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

            const answerKey =
                `${state.examSessionId}|${questionId}`;

            if (
                result.status === "saved" ||
                result.status === "unchanged"
            ) {
                state.syncedAnswers[answerKey] =
                    combinedAnswer;
                delete state.pendingAnswers[answerKey];
            }

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
