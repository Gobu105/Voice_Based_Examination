import {
    apiGet,
    apiPost
}
from "../common/api.js";

import {
    showSuccess,
    showError
}
from "../common/alerts.js";


export async function loadAnswers(
    sessionId
) {

    const container =
        document.getElementById(
            "answers-container"
        );

    if (!container) {
        return;
    }

    try {

        const data =
            await apiGet(
                `/invigilator/get_answers/${sessionId}`
            );

        container.innerHTML = "";

        if (
            !data ||
            data.length === 0
        ) {

            container.innerHTML = `
                <p>
                    No answers submitted.
                </p>
            `;

            return;
        }

        data.forEach(answer => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "answer-card";

            card.innerHTML = `

                <h3>
                    ${answer.question}
                </h3>

                <p>
                    <strong>Answer:</strong>
                    ${answer.answer}
                </p>
            `;

            container.appendChild(card);
        });

    } catch (err) {

        showError(
            err.message
        );
    }
}


export async function viewAnswers(sessionId) {

    const answerArea =
        document.getElementById(
            "answerArea"
        );

    if (!answerArea) {
        return;
    }

    try {

        const answers =
            await apiGet(
                `/invigilator/get_answers/${sessionId}`
            );

        let html = `
            <div class="section-title">Answer Evaluation</div>
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
                answer.marks !== null && answer.marks !== undefined ?
                    `<p><strong>Marks:</strong> ${answer.marks} / 100</p>` :
                    `<p style="color: orange;"><strong>Not Graded Yet</strong></p>`;

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
                        <input type="number" min="0" max="100" id="marks-${answer.answer_id}" placeholder="Marks" value="${answer.marks || ''}" style="margin-right: 10px; padding: 8px; border: 1px solid #ddd;" />
                        <button onclick="saveInvigilatorGrade(${answer.answer_id})" class="btn">Save Marks</button>
                    </div>
                </div>
            `;
        });

        answerArea.innerHTML = html;

    } catch (err) {

        showError(
            err.message
        );
        answerArea.innerHTML = `
            <div class="section-title">Answer Evaluation</div>
            <p style="color: red;">Error loading answers: ${err.message}</p>
        `;
    }
}


export async function saveInvigilatorGrade(answerId) {

    const input = document.getElementById(`marks-${answerId}`);
    const marks = Number(input.value);

    if (
        Number.isNaN(marks) ||
        marks < 0
    ) {

        showError(
            "Invalid marks"
        );

        return;
    }

    try {

        const result =
            await apiPost(
                "/invigilator/save_marks",
                {
                    answer_id: answerId,
                    marks: marks
                }
            );

        showSuccess(
            "Marks saved successfully"
        );

    } catch (err) {

        showError(
            err.message
        );
    }
}


window.viewAnswers = viewAnswers;
window.saveInvigilatorGrade = saveInvigilatorGrade;