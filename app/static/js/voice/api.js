import { log } from "./logging.js";

const REQUEST_TIMEOUT_MS = 15000;

async function fetchWithTimeout(url, options = {}) {
    if (!navigator.onLine) {
        throw new Error('offline');
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
        const response = await fetch(url, { ...options, signal: controller.signal });
        if (!response.ok) {
            let body = {};
            try {
                body = await response.json();
            } catch (_) {}
            const message = body.error || response.statusText || 'Request failed';
            throw new Error(message);
        }
        return await response.json();
    } catch (err) {
        if (err.name === 'AbortError') {
            throw new Error('timeout');
        }
        throw err;
    } finally {
        clearTimeout(timeoutId);
    }
}

export async function startExamAPI() {
    try {
        return await fetchWithTimeout('/api/start_exam', { credentials: 'same-origin' });
    } catch (err) {
        log(`Start exam API error: ${err}`);
        throw err;
    }
}

export async function getQuestionsAPI() {
    try {
        return await fetchWithTimeout('/api/questions', { credentials: 'same-origin' });
    } catch (err) {
        log(`Questions API error: ${err}`);
        throw err;
    }
}

export async function saveAnswerAPI(questionId, answer) {
    try {
        return await fetchWithTimeout('/api/save_answer', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question_id: questionId, answer: answer }),
        });
    } catch (err) {
        log(`Save answer API error: ${err}`);
        throw err;
    }
}

export async function submitExamAPI() {
    try {
        return await fetchWithTimeout('/api/submit_exam', {
            method: 'POST',
            credentials: 'same-origin',
        });
    } catch (err) {
        log(`Submit exam API error: ${err}`);
        throw err;
    }
}
