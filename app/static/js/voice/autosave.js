import { state }
from "./state.js";

import {
    AUTOSAVE_INTERVAL_MS
}
from "./config.js";

import {
    saveAnswerAPI
}
from "./api.js";

import {
    log,
    logWarning
}
from "./logging.js";


const LOCAL_KEY =
    "voice_exam_draft";


export function initializeAutosave() {

    stopAutosave();

    state.autosaveTimer =
        setInterval(

            autosaveAnswers,

            AUTOSAVE_INTERVAL_MS
        );

    window.addEventListener(

        "beforeunload",

        handleBeforeUnload
    );

    log(
        "Autosave initialized"
    );
}


export function stopAutosave() {

    if (state.autosaveTimer) {

        clearInterval(
            state.autosaveTimer
        );
    }
}


export async function autosaveAnswers() {

    if (
        state.saveInProgress ||
        !state.examActive
    ) {

        return;
    }

    state.saveInProgress = true;

    try {

        const savePromises = [];

        for (
            let i = 0;
            i < state.answers.length;
            i++
        ) {

            const answer =
                state.answers[i];

            if (!answer) {
                continue;
            }

            const questionId =
                state.questionIds[i];

            savePromises.push(

                saveAnswerAPI(
                    questionId,
                    answer
                )
            );
        }

        await Promise.all(
            savePromises
        );

        state.lastSavedAt =
            new Date();

        persistDraftLocally();

        log(
            "Autosave completed"
        );

    } catch (err) {

        logWarning(
            `
            Autosave failed:
            ${err}
            `
        );

        persistDraftLocally();

    } finally {

        state.saveInProgress = false;
    }
}


export function persistDraftLocally() {

    const payload = {

        answers:
            state.answers,

        questionIds:
            state.questionIds,

        currentIndex:
            state.currentIndex,

        timestamp:
            Date.now()
    };

    localStorage.setItem(

        LOCAL_KEY,

        JSON.stringify(payload)
    );
}


export function restoreDraft() {

    const raw =
        localStorage.getItem(
            LOCAL_KEY
        );

    if (!raw) {
        return false;
    }

    try {

        const draft =
            JSON.parse(raw);

        if (
            !draft.answers ||
            !Array.isArray(
                draft.answers
            )
        ) {

            return false;
        }

        state.answers =
            draft.answers;

        state.currentIndex =
            draft.currentIndex || -1;

        log(
            "Recovered local draft"
        );

        return true;

    } catch (err) {

        logWarning(
            `
            Draft restore failed:
            ${err}
            `
        );

        return false;
    }
}


export function clearDraft() {

    localStorage.removeItem(
        LOCAL_KEY
    );
}


function handleBeforeUnload(
    event
) {

    if (!state.examActive) {
        return;
    }

    persistDraftLocally();

    event.preventDefault();

    event.returnValue =
        `
        Your exam is still active.
        Leaving may interrupt
        the examination.
        `;
}