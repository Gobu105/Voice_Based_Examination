import { state }
from "./state.js";

import {
    speak
}
from "./tts.js";

import {
    log
}
from "./logging.js";

import {
    showQuestion,
    updateAnswerDisplay
}
from "./ui.js";

import {
    formatTimeAnnouncement,
    getRemainingTime
}
from "./timer.js";

import {
    submitExamAPI
}
from "./api.js";


export const COMMANDS = {

    next: {

        synonyms: [

            "next question",
            "go next",
            "move on",
            "next one"
        ],

        action: cmdNextQuestion
    },

    repeat: {

        synonyms: [

            "repeat question",
            "say again",
            "repeat that"
        ],

        action: cmdRepeatQuestion
    },

    readAnswer: {

        synonyms: [

            "read my answer",
            "my answer",
            "read answer"
        ],

        action: cmdReadAnswer
    },

    clear: {

        synonyms: [

            "clear answer",
            "delete answer",
            "redo answer"
        ],

        action: cmdClearAnswer
    },

    timeLeft: {

        synonyms: [

            "time left",
            "remaining time"
        ],

        action: cmdTimeLeft
    },

    submit: {

        synonyms: [

            "submit exam",
            "finish exam",
            "end exam"
        ],

        action: cmdSubmitExam
    }
};


export function cmdNextQuestion() {

    state.currentIndex++;

    if (
        state.currentIndex <
        state.questions.length
    ) {

        const qNum =
            state.currentIndex + 1;

        const qText =
            state.questions[
                state.currentIndex
            ];

        showQuestion(
            qNum,
            qText
        );

        speak(
            `Question ${qNum}. ${qText}`
        );

        log(
            `Question ${qNum} presented`
        );
    }

    else {

        state.currentIndex =
            state.questions.length;

        speak(
            `
            You have reached the end
            of the exam.
            Say submit exam to finish.
            `
        );

        log(
            "All questions completed"
        );
    }
}


export function cmdRepeatQuestion() {

    if (
        state.currentIndex >= 0 &&
        state.currentIndex <
        state.questions.length
    ) {

        speak(
            state.questions[
                state.currentIndex
            ]
        );

        log(
            "Question repeated"
        );
    }

    else {

        speak(
            `
            No question selected.
            Say next question to begin.
            `
        );
    }
}


export function cmdReadAnswer() {

    if (
        state.currentIndex < 0 ||
        state.currentIndex >=
        state.questions.length
    ) {

        speak(
            "No question selected."
        );

        return;
    }

    const qNum =
        state.currentIndex + 1;

    const answer =
        state.answers[
            state.currentIndex
        ];

    if (!answer) {

        speak(
            `
            You have not answered
            question ${qNum} yet.
            `
        );
    }

    else {

        speak(
            `
            Your answer for question
            ${qNum} is:
            ${answer}
            `
        );
    }
}


export function cmdClearAnswer() {

    if (
        state.currentIndex < 0 ||
        state.currentIndex >=
        state.questions.length
    ) {

        speak(
            "No question selected."
        );

        return;
    }

    state.answers[
        state.currentIndex
    ] = undefined;

    updateAnswerDisplay();

    speak(
        "Answer cleared."
    );

    log(
        `
        Answer cleared for
        question ${
            state.currentIndex + 1
        }
        `
    );
}


export function cmdTimeLeft() {

    speak(
        formatTimeAnnouncement(
            getRemainingTime()
        )
    );

    log(
        "Time remaining announced"
    );
}


export async function cmdSubmitExam() {

    state.examActive = false;

    try {

        await submitExamAPI();

        speak(
            `
            Your exam has been
            submitted successfully.
            `
        );

        log(
            "Exam submitted"
        );

        setTimeout(() => {

            window.location.href =
                "/exam/submitted";

        }, 4000);

    } catch (err) {

        speak(
            `
            There was an error
            submitting your exam.
            `
        );

        log(
            `Submission error: ${err}`
        );
    }
}