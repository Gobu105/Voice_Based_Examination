import { state } from "./state.js";
import { submitExamAPI } from "./api.js";
import { stopTimer } from "./timer.js";
import { setSaveStatus } from "./ui.js";
import {
    syncPendingAnswersImmediately,
    clearDraft,
    stopAutosave
}
from "./recovery.js";
import { log } from "./logging.js";


export async function submitExamSafely() {

    if (state.pendingSubmission) {
        return;
    }

    state.pendingSubmission = true;
    state.examActive = false;

    try {
        await syncPendingAnswersImmediately();
        if (Object.keys(state.pendingAnswers).length > 0) {
            throw new Error("Pending answers could not be synced.");
        }
        await submitExamAPI();
        stopTimer();
        clearDraft();
        stopAutosave();
        setSaveStatus("saved", "Exam submitted");
        log("Exam submitted");

        setTimeout(() => {
            window.location.href =
                "/exam/submitted";
        }, 1200);

    } catch (err) {
        state.examActive = true;
        state.pendingSubmission = false;
        setSaveStatus("error", "Submit failed. Retry.");
        log(`Submission error: ${err}`);
    }
}
