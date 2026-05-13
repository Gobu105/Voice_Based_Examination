import {
    apiPost
}
from "../common/api.js";

import {
    showSuccess,
    showError
}
from "../common/alerts.js";


export function logAdminEvent(
    message
) {

    console.log(
        `[ADMIN] ${message}`
    );
}


export async function toggleStudentStatus(
    studentId,
    active
) {

    const confirmMsg =
        active
            ? "Activate this student?"
            : "Deactivate this student?";

    const ok =
        confirm(confirmMsg);

    if (!ok) {
        return;
    }

    try {

        const result =
            await apiPost(
                "/admin/toggle_student",
                {
                    student_id:
                        studentId,

                    active
                }
            );

        showSuccess(
            result.message ||
            "Student updated"
        );

        window.location.reload();

    } catch (err) {

        showError(
            err.message
        );
    }
}


export async function deleteStudent(
    studentId
) {

    const ok =
        confirm(
            `
            Delete this student?
            This cannot be undone.
            `
        );

    if (!ok) {
        return;
    }

    try {

        const result =
            await apiPost(
                "/admin/delete_student",
                {
                    student_id:
                        studentId
                }
            );

        showSuccess(
            result.message ||
            "Student deleted"
        );

        window.location.reload();

    } catch (err) {

        showError(
            err.message
        );
    }
}