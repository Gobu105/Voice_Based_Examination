import { state } from "./state.js";

let els = {};


export function initializeUI() {

    els = {

        statusDot:
            document.getElementById("status-dot"),

        statusText:
            document.getElementById("status-text"),

        interimBox:
            document.getElementById("interim-transcript"),

        finalBox:
            document.getElementById("final-transcript"),

        questionBox:
            document.getElementById("current-question"),

        answerList:
            document.getElementById("answer-list"),

        timerBox:
            document.getElementById("exam-timer")
    };
}


export function setStatus(type, message) {

    if (!els.statusDot || !els.statusText) return;

    els.statusDot.className =
        "status-dot " + type;

    els.statusText.textContent = message;
}


export function setListeningState(listening) {

    state.isListening = listening;

    if (listening) {
        setStatus("listening", "Listening...");
    }
    else if (state.examActive) {
        setStatus("processing", "Restarting mic...");
    }
}


export function showInterim(text) {

    if (!els.interimBox) return;

    els.interimBox.textContent = text;
}


export function showFinal(text) {

    if (els.interimBox) {
        els.interimBox.textContent = "";
    }

    if (els.finalBox) {
        els.finalBox.textContent = text;
    }
}


export function showQuestion(num, text) {

    if (!els.questionBox) return;

    els.questionBox.innerHTML = `
        <span class="q-number">
            Q${num}.
        </span>
        ${text}
    `;
}


export function updateAnswerDisplay() {

    if (!els.answerList) return;

    els.answerList.innerHTML = "";

    state.answers.forEach((ans, idx) => {

        if (!ans) return;

        const li = document.createElement("li");

        li.innerHTML = `
            <strong>Q${idx + 1}:</strong>
            ${ans}
        `;

        els.answerList.appendChild(li);
    });
}


export function updateTimerDisplay(timeString) {

    if (!els.timerBox) return;

    els.timerBox.textContent = timeString;
}


export function getUIElements() {

    return els;
}