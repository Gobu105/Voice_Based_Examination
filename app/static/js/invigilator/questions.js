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


export async function loadQuestions() {

    const container =
        document.getElementById(
            "questions-container"
        );

    if (!container) {
        return;
    }

    try {

        const data =
            await apiGet(
                "/invigilator/questions"
            );

        container.innerHTML = "";

        if (
            !data.questions ||
            data.questions.length === 0
        ) {

            container.innerHTML = `
                <p>
                    No questions available.
                </p>
            `;

            return;
        }

        data.questions.forEach(q => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "question-card";

            card.innerHTML = `

                <h3>
                    Question ${q.number}
                </h3>

                <p>
                    ${q.text}
                </p>

                <button
                    class="delete-question-btn"
                    data-id="${q.id}">

                    Delete

                </button>
            `;

            container.appendChild(card);
        });

        bindDeleteButtons();

    } catch (err) {

        showError(
            err.message
        );
    }
}


function bindDeleteButtons() {

    const buttons =
        document.querySelectorAll(
            ".delete-question-btn"
        );

    buttons.forEach(btn => {

        btn.addEventListener(

            "click",

            async () => {

                const questionId =
                    btn.dataset.id;

                await deleteQuestion(
                    questionId
                );
            }
        );
    });
}


export async function addQuestion(
    text
) {

    if (!text.trim()) {

        showError(
            "Question cannot be empty"
        );

        return;
    }

    try {

        const result =
            await apiPost(
                "/invigilator/add_question",
                {
                    text
                }
            );

        showSuccess(
            result.message ||
            "Question added"
        );

        await loadQuestions();

    } catch (err) {

        showError(
            err.message
        );
    }
}


export async function deleteQuestion(
    questionId
) {

    const ok =
        confirm(
            `
            Delete this question?
            `
        );

    if (!ok) {
        return;
    }

    try {

        const result =
            await apiPost(
                "/invigilator/delete_question",
                {
                    question_id:
                        questionId
                }
            );

        showSuccess(
            result.message ||
            "Question deleted"
        );

        await loadQuestions();

    } catch (err) {

        showError(
            err.message
        );
    }
}