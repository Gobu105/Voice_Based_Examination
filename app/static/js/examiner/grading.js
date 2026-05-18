import {
    apiPost,
    apiGet
}
from "../common/api.js";

import {
    showSuccess,
    showError
}
from "../common/alerts.js";

import {
    aiGrade,
    aiGradeAll
}
from "./ai_grading.js";


export async function loadPendingAnswers() {

    const container =
        document.getElementById(
            "pending-answers"
        );

    if (!container) {
        return;
    }

    try {

        const data =
            await apiGet(
                "/examiner/pending_answers"
            );

        container.innerHTML = "";

        if (
            !data.answers ||
            data.answers.length === 0
        ) {

            container.innerHTML = `
                <p>
                    No pending answers.
                </p>
            `;

            return;
        }

        data.answers.forEach(answer => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "answer-card";

            card.innerHTML = `

                <h3>
                    ${answer.student_name}
                </h3>

                <p>
                    <strong>Question:</strong>
                    ${answer.question}
                </p>

                <p>
                    <strong>Answer:</strong>
                    ${answer.answer}
                </p>

                <input
                    type="number"
                    min="0"
                    max="10"
                    id="marks-${answer.id}"
                    placeholder="Marks"
                />

                <button
                    data-id="${answer.id}"
                    class="save-grade-btn">

                    Save Grade

                </button>
            `;

            container.appendChild(card);
        });

        bindSaveButtons();

    } catch (err) {

        showError(
            err.message
        );
    }
}


function bindSaveButtons() {

    const buttons =
        document.querySelectorAll(
            ".save-grade-btn"
        );

    buttons.forEach(btn => {

        btn.addEventListener(

            "click",

            async () => {

                const answerId =
                    btn.dataset.id;

                const input =
                    document.getElementById(
                        `marks-${answerId}`
                    );

                const marks =
                    Number(input.value);

                await saveGrade(
                    answerId,
                    marks
                );
            }
        );
    });
}


export async function saveGrade(
    answerId,
    marks
) {

    if (
        Number.isNaN(marks) ||
        marks < 0 ||
        marks > 10
    ) {

        showError(
            "Invalid marks"
        );

        return;
    }

    try {

        const result =
            await apiPost(
                "/examiner/save_grade",
                {
                    answer_id:
                        answerId,

                    marks
                }
            );

        showSuccess(
            result.message ||
            "Grade saved"
        );

    } catch (err) {

        showError(
            err.message
        );
    }
}


export async function loadStudentAnswers(
    sessionId
) {

    const answerArea =
        document.getElementById(
            "answerArea"
        );

    if (!answerArea) {
        return;
    }

    try {

        const result =
            await apiGet(
                `/examiner/get_student_answers/${sessionId}`
            );

        const answers =
            Array.isArray(result)
                ? result
                : result.answers || [];

        const evaluation =
            Array.isArray(result)
                ? { locked: false, reopen_count: 0 }
                : result.evaluation || { locked: false, reopen_count: 0 };

        let html = `
            <div class="section-title">Answer Review and Grading</div>
            <div style="margin-bottom: 15px;">
                ${evaluation.locked
                    ? '<span class="badge badge-manual">Evaluation Locked</span>'
                    : '<span class="badge badge-tampered">Evaluation Open</span>'}
                ${evaluation.reopen_count
                    ? `<span class="badge badge-manual">Re-opened ${evaluation.reopen_count} time(s)</span>`
                    : ''}
            </div>
        `;

        if (
            !answers ||
            answers.length === 0
        ) {

            html += `
                <p>No answers found.</p>
            `;

            answerArea.innerHTML = html;
            return;
        }

        answers.forEach(answer => {

            const gradingStatus =
                answer.grading_method ?
                    `<p><strong>Graded:</strong> ${answer.grading_method} (${answer.marks || 0} marks)</p>` :
                    `<p style="color: orange;"><strong>Pending Grading</strong></p>`;

            const disabled =
                evaluation.locked ? 'disabled' : '';

            const tamperWarning =
                answer.tampered ?
                    `<p style="color: red;"><strong>⚠️ WARNING: This answer may have been tampered with!</strong></p>` :
                    '';

            html += `
                <div class="answer-card" style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <h4>${answer.question}</h4>
                    ${tamperWarning}
                    <p><strong>Student Answer:</strong></p>
                    <p style="background: #f5f5f5; padding: 10px; border-radius: 3px;">${answer.answer}</p>
                    <p><strong>Model Answer:</strong></p>
                    <p style="background: #f5f5f5; padding: 10px; border-radius: 3px;">${answer.model_answer || 'N/A'}</p>
                    ${gradingStatus}
                    <div style="margin-top: 10px;">
                        <input type="number" min="0" max="10" id="marks-${answer.answer_id}" placeholder="Marks" value="${answer.marks || ''}" style="margin-right: 10px; padding: 8px; border: 1px solid #ddd;" ${disabled} />
                        <button onclick="saveGradeHandler(${answer.answer_id})" class="btn" style="margin-right: 5px;" ${disabled}>Save Marks</button>
                        <button onclick="aiGradeHandler(${answer.answer_id})" class="btn" style="background: #4CAF50;" ${disabled}>AI Grade</button>
                    </div>
                </div>
            `;
        });

        html += `
            <div style="margin-top: 15px;">
                ${evaluation.locked
                    ? `<button onclick="reopenEvaluationHandler(${sessionId})" class="btn btn-danger" style="width: 100%;">Re-open Evaluation</button>`
                    : `
                        <button onclick="aiGradeAllHandler(${sessionId})" class="btn" style="background: #4CAF50; width: 100%; margin-bottom: 8px;">AI Grade All</button>
                        <button onclick="lockEvaluationHandler(${sessionId})" class="btn btn-success" style="width: 100%;">Lock Evaluation</button>
                    `}
            </div>
        `;

        answerArea.innerHTML = html;

    } catch (err) {

        showError(
            err.message
        );
        const answerArea =
            document.getElementById(
                "answerArea"
            );
        answerArea.innerHTML = `
            <div class="section-title">Answer Review and Grading</div>
            <p style="color: red;">Error loading answers: ${err.message}</p>
        `;
    }
}


export async function lockEvaluation(
    sessionId
) {

    const ok =
        confirm(
            "Lock this evaluation? Marks cannot be changed until it is re-opened."
        );

    if (!ok) {
        return;
    }

    try {

        const result =
            await apiPost(
                "/examiner/lock_evaluation",
                {
                    session_id:
                        sessionId
                }
            );

        showSuccess(
            result.message ||
            "Evaluation locked"
        );

    } catch (err) {

        showError(
            err.message
        );
    }
}


export async function reopenEvaluation(
    sessionId
) {

    const ok =
        confirm(
            "Re-open this evaluation for changes?"
        );

    if (!ok) {
        return;
    }

    try {

        const result =
            await apiPost(
                "/examiner/reopen_evaluation",
                {
                    session_id:
                        sessionId
                }
            );

        showSuccess(
            result.message ||
            "Evaluation re-opened"
        );

    } catch (err) {

        showError(
            err.message
        );
    }
}


