import {
    apiPost
}
from "../common/api.js";

import {
    showSuccess,
    showError
}
from "../common/alerts.js";


export async function publishResults(
    examId
) {

    const ok =
        confirm(
            `
            Publish results
            for this exam?
            `
        );

    if (!ok) {
        return;
    }

    try {

        const result =
            await apiPost(
                "/examiner/publish_results",
                {
                    exam_id:
                        examId
                }
            );

        showSuccess(
            result.message ||
            "Results published"
        );

    } catch (err) {

        showError(
            err.message
        );
    }
}


export function viewStudentResult(
    studentId
) {

    window.location.href =
        `/examiner/student_result/${studentId}`;
}