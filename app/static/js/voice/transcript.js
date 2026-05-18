import { state }
from "./state.js";

import {
    normalize
}
from "./normalization.js";

import {
    normalizeCommandLanguage
}
from "./language.js";

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

import {
    COMMAND_CONFIRMATION_THRESHOLD,
    SPEECH_CONFIDENCE_THRESHOLD,
    COMMAND_CONFIRMATION_TIMEOUT_MS
}
from "./config.js";


export function handleTranscriptResult(
    event
) {

    let interim = "";

    let finalTranscript = "";

    let finalConfidence = 1;

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

            if (
                typeof event.results[i][0].confidence ===
                "number"
            ) {
                finalConfidence =
                    event.results[i][0].confidence;
            }
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
            normalized,
            finalConfidence
        );
    }
}


export async function processTranscript(
    text,
    confidence = 1
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

    const confirmationHandled =
        handlePendingConfirmation(
            text
        );

    if (confirmationHandled) {
        return;
    }

    // command matching
    const commandText =
        normalizeCommandLanguage(text)
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

        if (
            confidence > 0 &&
            confidence < SPEECH_CONFIDENCE_THRESHOLD &&
            cmd.score < 1
        ) {

            speak(
                "I am not sure I heard that command. Please repeat it."
            );

            log(
                `Low confidence command ignored: ${cmd.name}`
            );

            return;
        }

        log(
            `
            Command recognized:
            ${cmd.name}
            `
        );

        if (cmd.destructive) {

            state.pendingCommand =
                cmd;

            state.pendingCommandUntil =
                Date.now() +
                COMMAND_CONFIRMATION_TIMEOUT_MS;

            speak(
                cmd.confirmationPrompt ||
                "Say yes to confirm or no to cancel."
            );

            return;
        }

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


function handlePendingConfirmation(
    text
) {

    if (!state.pendingCommand) {
        return false;
    }

    if (
        Date.now() >
        state.pendingCommandUntil
    ) {

        state.pendingCommand = null;
        state.pendingCommandUntil = 0;
        speak(
            "Confirmation expired."
        );
        return true;
    }

    const commandText =
        text
            .toLowerCase()
            .replace(/[^\w\s]/g, "")
            .trim();

    const yesWords =
        ["yes", "confirm", "confirm it", "do it", "submit", "clear"];

    const noWords =
        ["no", "cancel", "stop", "do not", "dont"];

    if (
        yesWords.some(word => commandText === word || commandText.includes(word))
    ) {

        const command =
            state.pendingCommand;

        state.pendingCommand = null;
        state.pendingCommandUntil = 0;

        command.action();

        return true;
    }

    if (
        noWords.some(word => commandText === word || commandText.includes(word))
    ) {

        state.pendingCommand = null;
        state.pendingCommandUntil = 0;

        speak(
            "Cancelled."
        );

        return true;
    }

    speak(
        "Please say yes to confirm or no to cancel."
    );

    return true;
}
