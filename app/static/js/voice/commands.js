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
    submitExamSafely
}
from "./submission.js";


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

    skip: {

        synonyms: [

            "skip question",
            "skip this question",
            "leave this question"
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
    },

    help: {

        synonyms: [

            "help me",
            "voice commands",
            "show commands"
        ],

        action: cmdHelp
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


export function cmdGoToQuestion(questionNumber) {

    const targetIndex =
        questionNumber - 1;

    if (
        !Number.isInteger(questionNumber) ||
        targetIndex < 0 ||
        targetIndex >= state.questions.length
    ) {

        speak(
            "That question number is not available."
        );

        return;
    }

    state.currentIndex =
        targetIndex;

    showQuestion(
        questionNumber,
        state.questions[targetIndex]
    );

    speak(
        `Question ${questionNumber}. ${state.questions[targetIndex]}`
    );

    log(
        `Question ${questionNumber} presented`
    );
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

    speak(
        "Submitting your exam now."
    );

    await submitExamSafely();
}


export function cmdHelp() {

    speak(
        `
        You can say next question,
        skip question,
        go to question followed by a number,
        repeat question,
        read my answer,
        clear answer,
        time left,
        or submit exam.
        `
    );

    log(
        "Voice command help announced"
    );
}
