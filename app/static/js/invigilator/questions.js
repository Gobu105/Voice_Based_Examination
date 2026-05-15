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


let currentExamId = null;


export async function loadQuestions(examId) {

    currentExamId = examId;

    const container =
        document.getElementById(
            "questionArea"
        );

    if (!container) {
        return;
    }

    try {

        const data =
            await apiGet(
                `/invigilator/get_questions/${examId}`
            );

        container.innerHTML = "";

        if (
            !data ||
            data.length === 0
        ) {

            container.innerHTML = `
                <p>
                    No questions available for this exam.
                </p>
                <div style="margin-top: 20px;">
                    <input type="text" id="new-question-text" placeholder="Question text" style="width: 100%; margin-bottom: 10px;" />
                    <textarea id="new-question-answer" placeholder="Model answer" style="width: 100%; height: 100px; margin-bottom: 10px;"></textarea>
                    <button onclick="addQuestion()" class="btn btn-success">Add Question</button>
                </div>
            `;

            return;
        }

        let html = `
            <div style="margin-bottom: 20px;">
                <input type="text" id="new-question-text" placeholder="Question text" style="width: 100%; margin-bottom: 10px;" />
                <textarea id="new-question-answer" placeholder="Model answer" style="width: 100%; height: 100px; margin-bottom: 10px;"></textarea>
                <button onclick="addQuestion()" class="btn btn-success">Add Question</button>
            </div>
        `;

        data.forEach(q => {

            html += `

                <div class="question-card" style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px;">

                    <h3>
                        Question ${q.id}
                    </h3>

                    <p>
                        ${q.text}
                    </p>

                    <p><strong>Model Answer:</strong> ${q.model_answer}</p>

                    <button
                        class="delete-question-btn"
                        data-id="${q.id}">

                        Delete

                    </button>
                </div>
            `;
        });

        container.innerHTML = `
            <div class="section-title">Question Management</div>
            <div id="questions-container">
                ${html}
            </div>
        `;

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


export async function addQuestion() {

    const textInput = document.getElementById('new-question-text');
    const answerInput = document.getElementById('new-question-answer');
    const text = textInput.value.trim();
    const modelAnswer = answerInput.value.trim();

    if (!text || !modelAnswer) {
        showError("Both question text and model answer are required");
        return;
    }

    if (!currentExamId) {
        showError("No exam selected");
        return;
    }

    try {

        const result =
            await apiPost(
                "/invigilator/add_question",
                {
                    exam_id: currentExamId,
                    text: text,
                    model_answer: modelAnswer
                }
            );

        showSuccess(
            result.message ||
            "Question added"
        );

        textInput.value = '';
        answerInput.value = '';

        await loadQuestions(currentExamId);

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
                `/invigilator/delete_question/${questionId}`
            );

        showSuccess(
            result.message ||
            "Question deleted"
        );

        if (currentExamId) {
            await loadQuestions(currentExamId);
        }

    } catch (err) {

        showError(
            err.message
        );
    }
}