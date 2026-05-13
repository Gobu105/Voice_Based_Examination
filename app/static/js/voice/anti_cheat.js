import { state }
from "./state.js";

import {
    log,
    logWarning
}
from "./logging.js";

import {
    speak
}
from "./tts.js";


export const violations = {

    tabSwitches: 0,

    fullscreenExit: 0,

    copyAttempts: 0,

    rightClickAttempts: 0
};


export function initializeAntiCheat() {

    initializeTabMonitoring();

    initializeFullscreenMonitoring();

    initializeCopyProtection();

    initializeRightClickProtection();

    log(
        "Anti-cheat initialized"
    );
}


function initializeTabMonitoring() {

    document.addEventListener(

        "visibilitychange",

        () => {

            if (
                !state.examActive
            ) {

                return;
            }

            if (
                document.hidden
            ) {

                violations.tabSwitches++;

                logWarning(
                    `
                    Tab switch detected
                    (${violations.tabSwitches})
                    `
                );

                speak(
                    `
                    Warning.
                    Tab switching is not allowed.
                    `
                );
            }
        }
    );
}


function initializeFullscreenMonitoring() {

    document.addEventListener(

        "fullscreenchange",

        () => {

            if (
                !state.examActive
            ) {

                return;
            }

            if (
                !document.fullscreenElement
            ) {

                violations.fullscreenExit++;

                logWarning(
                    `
                    Fullscreen exited
                    (${violations.fullscreenExit})
                    `
                );

                speak(
                    `
                    Warning.
                    Fullscreen mode exited.
                    `
                );
            }
        }
    );
}


function initializeCopyProtection() {

    document.addEventListener(

        "copy",

        event => {

            if (
                !state.examActive
            ) {

                return;
            }

            violations.copyAttempts++;

            event.preventDefault();

            logWarning(
                `
                Copy attempt blocked
                (${violations.copyAttempts})
                `
            );

            speak(
                `
                Copying is disabled
                during examination.
                `
            );
        }
    );
}


function initializeRightClickProtection() {

    document.addEventListener(

        "contextmenu",

        event => {

            if (
                !state.examActive
            ) {

                return;
            }

            violations.rightClickAttempts++;

            event.preventDefault();

            logWarning(
                `
                Right click blocked
                (${violations.rightClickAttempts})
                `
            );
        }
    );
}


export async function enterExamFullscreen() {

    const el =
        document.documentElement;

    try {

        if (
            el.requestFullscreen
        ) {

            await el.requestFullscreen();
        }

    } catch (err) {

        logWarning(
            `
            Fullscreen failed:
            ${err}
            `
        );
    }
}