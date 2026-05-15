import { state }
from "./state.js";

import {
    startExamAPI,
    getQuestionsAPI
}
from "./api.js";

import {
    startTimer
}
from "./timer.js";

import {
    showQuestion,
    updateAnswerDisplay
}
from "./ui.js";

import {
    speak
}
from "./tts.js";

import {
    log
}
from "./logging.js";

import {
    initializeAutosave,
    restoreDraft,
    syncPendingAnswersImmediately
}
from "./recovery.js";

import {
    submitExamSafely
}
from "./submission.js";

export async function startExam() {

    if (state.examActive) {
        return;
    }

    window._examAutoStarted = true;
    window._examInProgress = true;

    state.examActive = true;

    state.currentIndex = -1;

    state.answers = [];

    state.questions = [];

    state.questionIds = [];

    state.syncedAnswers = {};

    state.pendingAnswers = {};

    state.pendingSubmission = false;

    try {

        const startData =
            await startExamAPI();

        if (startData.error) {

            throw new Error(
                startData.error
            );
        }

        if (
            startData.duration_minutes
        ) {

            startTimer(
                startData.duration_minutes,
                submitExamSafely
            );
        }

        state.examSessionId =
            startData.session_id;

        const questions =
            await getQuestionsAPI();

        if (questions.error) {

            throw new Error(
                questions.error
            );
        }

        state.questions =
            questions.map(
                q => q.text
            );

        state.questionIds =
            questions.map(
                q => q.id
            );

        state.answers =
            new Array(
                state.questions.length
            );

        const restored =
            restoreDraft(
                state.questionIds,
                state.examSessionId
            );

        if (!restored.restored) {
            state.answers =
                new Array(
                    state.questions.length
                );
        }

        updateAnswerDisplay();

        initializeAutosave();

        if (restored.pendingCount > 0 && navigator.onLine) {
            syncPendingAnswersImmediately();
        }

        log(
            `
            Loaded
            ${state.questions.length}
            questions
            `
        );

        if (state.questions.length > 0) {

            if (
                state.currentIndex < 0 ||
                state.currentIndex >= state.questions.length
            ) {
                state.currentIndex = 0;
            }

            showQuestion(
                state.currentIndex + 1,
                state.questions[state.currentIndex]
            );

            speak(
                `
                Exam started.
                Question ${state.currentIndex + 1}.
                ${state.questions[state.currentIndex]}
                `
            );
        }

        else {

            speak(
                `
                Exam started,
                but no questions are available.
                `
            );
        }

    } catch (err) {

        state.examActive = false;
        window._examAutoStarted = false;
        window._examInProgress = false;

        log(
            `
            Exam start failed:
            ${err}
            `
        );

        speak(
            `
            Failed to start exam.
            Please try again.
            `
        );
    }
}
