import {
    apiPost
}
from "../common/api.js";

import {
    showSuccess,
    showError
}
from "../common/alerts.js";


export async function aiGrade(
    answerId
) {

    try {

        const result =
            await apiPost(
                "/examiner/ai_grade",
                {
                    answer_id:
                        answerId
                }
            );

        showSuccess(
            `
            AI grade:
            ${result.marks}/10
            `
        );

        updateAIMarks(
            answerId,
            result.marks
        );

    } catch (err) {

        showError(
            err.message
        );
    }
}


export async function aiGradeAll(
    sessionId
) {

    const ok =
        confirm(
            `
            Run AI grading for all
            pending answers?
            `
        );

    if (!ok) {
        return;
    }

    try {

        const result =
            await apiPost(
                "/examiner/ai_grade_all",
                {
                    session_id:
                        sessionId
                }
            );

        showSuccess(
            result.message ||
            "AI grading completed"
        );

    } catch (err) {

        showError(
            err.message
        );
    }
}


function updateAIMarks(
    answerId,
    marks
) {

    const input =
        document.getElementById(
            `marks-${answerId}`
        );

    if (!input) {
        return;
    }

    input.value = marks;
}
