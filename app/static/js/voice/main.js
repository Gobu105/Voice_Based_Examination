import {
    initializeUI
}
from "./ui.js";

import {
    initializeLogger
}
from "./logging.js";

import {
    initializeVoices
}
from "./tts.js";

import {
    startExam
}
from "./lifecycle.js";


document.addEventListener(
    "DOMContentLoaded",

    () => {

        initializeUI();

        initializeLogger();

        initializeVoices();

        const startBtn =
            document.getElementById(
                "start-exam-btn"
            );

        if (startBtn) {

            startBtn.addEventListener(

                "click",

                startExam
            );
        }
    }
);