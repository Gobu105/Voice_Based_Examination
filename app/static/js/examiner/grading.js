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