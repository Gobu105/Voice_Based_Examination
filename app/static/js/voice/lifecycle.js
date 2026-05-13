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
    speak
}
from "./tts.js";

import {
    log
}
from "./logging.js";

import {
    safeStartRecognition
}
from "./recognition.js";


export async function startExam() {

    if (state.examActive) {
        return;
    }

    state.examActive = true;

    state.currentIndex = -1;

    state.answers = [];

    state.questions = [];

    state.questionIds = [];

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
                startData.duration_minutes
            );
        }

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

        log(
            `
            Loaded
            ${state.questions.length}
            questions
            `
        );

        safeStartRecognition();

        speak(
            `
            Exam started.
            Say next question
            to begin.
            `
        );

    } catch (err) {

        state.examActive = false;

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