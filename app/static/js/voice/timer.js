import { state }
from "./state.js";

import {
    TIMER_WARNING_5_MIN,
    TIMER_WARNING_1_MIN
}
from "./config.js";

import {
    updateTimerDisplay
}
from "./ui.js";

import {
    formatTime
}
from "../common/helpers.js";

import {
    speak
}
from "./tts.js";

import {
    log
}
from "./logging.js";


export function startTimer(
    durationMinutes,
    onTimeUp
) {

    state.remainingSeconds =
        durationMinutes * 60;

    state.lastAnnouncedQuarter = -1;

    renderTimer();

    state.timerInterval =
        setInterval(() => {

            state.remainingSeconds--;

            if (
                state.remainingSeconds <= 0
            ) {

                state.remainingSeconds = 0;

                clearInterval(
                    state.timerInterval
                );

                speak(
                    "Time is up. Your exam is being submitted automatically."
                );

                if (onTimeUp) {

                    setTimeout(() => {

                        onTimeUp();

                    }, 3000);
                }
            }

            renderTimer();

            checkTimerAnnouncements();

        }, 1000);
}


export function stopTimer() {

    if (state.timerInterval) {

        clearInterval(
            state.timerInterval
        );
    }
}


function renderTimer() {

    const timeString =
        formatTime(
            state.remainingSeconds
        );

    updateTimerDisplay(
        timeString
    );
}


function checkTimerAnnouncements() {

    const mins =
        Math.floor(
            state.remainingSeconds / 60
        );

    const currentQuarter =
        Math.floor(mins / 15);

    if (
        state.remainingSeconds ===
        TIMER_WARNING_5_MIN
    ) {

        speak("5 minutes remaining.");

        log(
            "Timer warning: 5 minutes remaining"
        );
    }

    else if (
        state.remainingSeconds ===
        TIMER_WARNING_1_MIN
    ) {

        speak(
            "1 minute remaining. Please wrap up."
        );

        log(
            "Timer warning: 1 minute remaining"
        );
    }

    else if (
        mins > 0 &&
        mins % 15 === 0 &&
        state.remainingSeconds % 60 === 0 &&
        currentQuarter !==
        state.lastAnnouncedQuarter
    ) {

        state.lastAnnouncedQuarter =
            currentQuarter;

        speak(
            `${mins} minutes remaining.`
        );

        log(
            `Timer update: ${mins} minutes remaining`
        );
    }
}


export function getRemainingTime() {

    return state.remainingSeconds;
}


export function formatTimeAnnouncement(
    totalSeconds
) {

    const mins =
        Math.floor(totalSeconds / 60);

    const secs =
        totalSeconds % 60;

    if (mins > 0 && secs > 0) {

        return `
            ${mins} minutes and
            ${secs} seconds remaining.
        `;
    }

    if (mins > 0) {

        return `
            ${mins} minutes remaining.
        `;
    }

    return `
        ${secs} seconds remaining.
    `;
}