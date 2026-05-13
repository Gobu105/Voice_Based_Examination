import {
    apiPost
}
from "../common/api.js";

import {
    showSuccess,
    showError
}
from "../common/alerts.js";


export async function assignExaminer(
    sessionId,
    examinerId
) {

    try {

        const result =
            await apiPost(
                "/admin/assign_examiner",
                {
                    session_id:
                        sessionId,

                    examiner_id:
                        examinerId
                }
            );

        showSuccess(
            result.message ||
            "Examiner assigned"
        );

    } catch (err) {

        showError(
            err.message
        );
    }
}


export async function removeAssignment(
    assignmentId
) {

    const ok =
        confirm(
            `
            Remove this assignment?
            `
        );

    if (!ok) {
        return;
    }

    try {

        const result =
            await apiPost(
                "/admin/remove_assignment",
                {
                    assignment_id:
                        assignmentId
                }
            );

        showSuccess(
            result.message ||
            "Assignment removed"
        );

        window.location.reload();

    } catch (err) {

        showError(
            err.message
        );
    }
}