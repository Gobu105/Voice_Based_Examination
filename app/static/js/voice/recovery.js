import { state } from "./state.js";
import { AUTOSAVE_INTERVAL_MS } from "./config.js";
import { saveAnswerAPI } from "./api.js";
import { log, logWarning } from "./logging.js";
import { setSaveStatus, showDraftBanner } from "./ui.js";

const LOCAL_KEY = "voice_exam_draft";
const RECOVERY_KEY = "voice_exam_recovery_state";
const DRAFT_MAX_AGE_MS = 24 * 60 * 60 * 1000;

export function initializeAutosave() {
    stopAutosave();

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    window.addEventListener("beforeunload", handleBeforeUnload);

    if (!navigator.onLine) {
        setSaveStatus('offline', 'Offline — Answers saved locally');
        showDraftBanner(true, 'You are offline. Answers are saved locally.');
        state.networkOnline = false;
    }

    state.autosaveTimer = setInterval(
        autosaveAnswersWithRetry,
        AUTOSAVE_INTERVAL_MS
    );

    log("Autosave initialized with offline support");
}


export function stopAutosave() {
    if (state.autosaveTimer) {
        clearInterval(state.autosaveTimer);
        state.autosaveTimer = null;
    }

    window.removeEventListener("online", handleOnline);
    window.removeEventListener("offline", handleOffline);
    window.removeEventListener("beforeunload", handleBeforeUnload);
}


function handleOnline() {
    state.networkOnline = true;
    setSaveStatus('saving', 'Connection restored. Syncing...');
    log("Network connection restored");
    syncPendingAnswersImmediately();
}


function handleOffline() {
    state.networkOnline = false;
    setSaveStatus('offline', 'Offline — Local saves active');
    showDraftBanner(true, 'No internet connection. Work is saved locally.');
    logWarning("Network connection lost");
}


export async function autosaveAnswersWithRetry() {
    if (
        state.saveInProgress ||
        !state.examActive ||
        !navigator.onLine
    ) {
        if (!navigator.onLine && state.examActive) {
            persistDraftLocally();
        }
        return;
    }

    state.saveInProgress = true;
    setSaveStatus('saving', 'Saving...');

    try {
        let allSaved = true;

        for (let i = 0; i < state.answers.length; i++) {
            const answer = state.answers[i];
            if (!answer) continue;

            const questionId = state.questionIds[i];
            const answerKey = `${state.examSessionId}|${questionId}`;

            if (state.syncedAnswers[answerKey] === answer) {
                continue;
            }

            try {
                const result = await saveAnswerAPI(questionId, answer);

                if (result.status === 'saved' || result.status === 'unchanged') {
                    state.syncedAnswers[answerKey] = answer;
                    delete state.pendingAnswers[answerKey];
                } else {
                    allSaved = false;
                    state.pendingAnswers[answerKey] = answer;
                }
            } catch (err) {
                allSaved = false;
                state.pendingAnswers[answerKey] = answer;

                if (err.message === 'timeout') {
                    logWarning(`Timeout saving Q${i + 1}. Will retry.`);
                } else if (err.message === 'offline') {
                    state.networkOnline = false;
                    throw err;
                } else {
                    logWarning(`Save error for Q${i + 1}: ${err.message}`);
                }
            }
        }

        if (allSaved && Object.keys(state.pendingAnswers).length === 0) {
            state.lastSavedAt = new Date();
            setSaveStatus('saved', 'All saved ✓');
            log("Autosave completed successfully");
        } else {
            setSaveStatus('saving', 'Saving pending answers...');
        }

        persistDraftLocally();
    } catch (err) {
        if (err.message === 'offline') {
            state.networkOnline = false;
            setSaveStatus('offline', 'Offline — Saving locally');
        } else {
            setSaveStatus('error', 'Save error — retrying');
            logWarning(`Autosave failed: ${err.message}`);
        }
        persistDraftLocally();
    } finally {
        state.saveInProgress = false;
    }
}


export async function syncPendingAnswersImmediately() {
    const pending = Object.keys(state.pendingAnswers);
    if (pending.length === 0) {
        setSaveStatus('saved', 'All saved ✓');
        return;
    }

    for (const answerKey of pending) {
        const answer = state.pendingAnswers[answerKey];
        const [sessionId, questionIdStr] = answerKey.split('|');
        const questionId = parseInt(questionIdStr);

        try {
            await saveAnswerAPI(questionId, answer);
            state.syncedAnswers[answerKey] = answer;
            delete state.pendingAnswers[answerKey];
            log(`Synced pending Q${questionId}`);
        } catch (err) {
            logWarning(`Failed to sync Q${questionId}: ${err.message}`);
        }
    }

    persistDraftLocally();

    if (Object.keys(state.pendingAnswers).length === 0) {
        setSaveStatus('saved', 'All saved ✓');
        showDraftBanner(false);
    }
}


export function persistDraftLocally() {
    const payload = {
        answers: state.answers,
        questionIds: state.questionIds,
        examSessionId: state.examSessionId,
        currentIndex: state.currentIndex,
        syncedAnswers: state.syncedAnswers,
        pendingAnswers: state.pendingAnswers,
        timestamp: Date.now(),
        examActive: state.examActive,
    };

    const recoveryPayload = {
        examSessionId: state.examSessionId,
        examActive: state.examActive,
        remainingSeconds: state.remainingSeconds,
        timestamp: Date.now(),
    };

    try {
        localStorage.setItem(LOCAL_KEY, JSON.stringify(payload));
        localStorage.setItem(RECOVERY_KEY, JSON.stringify(recoveryPayload));
    } catch (err) {
        logWarning(`Failed to persist draft: ${err.message}`);
    }
}


export function restoreDraft(expectedQuestionIds = [], expectedSessionId = null) {
    const raw = localStorage.getItem(LOCAL_KEY);
    if (!raw) {
        return { restored: false, pendingCount: 0 };
    }

    try {
        const draft = JSON.parse(raw);

        if (!Array.isArray(draft.answers)) {
            return { restored: false, pendingCount: 0 };
        }

        if (
            draft.timestamp &&
            Date.now() - draft.timestamp > DRAFT_MAX_AGE_MS
        ) {
            clearDraft();
            return { restored: false, pendingCount: 0 };
        }

        if (
            expectedQuestionIds.length > 0 &&
            Array.isArray(draft.questionIds) &&
            draft.questionIds.join("|") !== expectedQuestionIds.join("|")
        ) {
            clearDraft();
            return { restored: false, pendingCount: 0 };
        }

        state.answers = draft.answers;
        state.questionIds = draft.questionIds || [];
        state.currentIndex = draft.currentIndex || -1;
        state.syncedAnswers = draft.syncedAnswers || {};
        state.pendingAnswers = draft.pendingAnswers || {};
        state.examSessionId = expectedSessionId || draft.examSessionId || state.examSessionId;

        const pendingCount = Object.keys(state.pendingAnswers).length;

        if (pendingCount > 0) {
            log(`Recovered draft with ${pendingCount} pending answers`);
            setSaveStatus('saving', `Syncing ${pendingCount} pending answer(s)...`);
            showDraftBanner(true, `Recovered ${draft.answers.filter(a => a).length} answers. Syncing...`);
        } else {
            log("Recovered local draft");
        }

        return { restored: true, pendingCount };
    } catch (err) {
        logWarning(`Draft restore failed: ${err.message}`);
        return { restored: false, pendingCount: 0 };
    }
}


export function getRecoveryState() {
    const raw = localStorage.getItem(RECOVERY_KEY);
    if (!raw) return null;

    try {
        return JSON.parse(raw);
    } catch (_) {
        return null;
    }
}


export function clearDraft() {
    try {
        localStorage.removeItem(LOCAL_KEY);
        localStorage.removeItem(RECOVERY_KEY);
    } catch (_) {}
}


export function isDraftAvailable() {
    return localStorage.getItem(LOCAL_KEY) !== null;
}


function handleBeforeUnload(event) {
    if (!state.examActive) {
        return;
    }

    const pending = Object.keys(state.pendingAnswers).length;
    const answered = state.answers.filter(Boolean).length;

    if (pending > 0 || answered > 0) {
        persistDraftLocally();

        event.preventDefault();
        event.returnValue =
            pending > 0
                ? `You have ${pending} unsaved answer(s). Leaving may lose them.`
                : "Your exam is still active. Leaving may interrupt the examination.";
    }
}
