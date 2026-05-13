import {
    apiGet
}
from "../common/api.js";

import {
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
                `
                /invigilator/answers/${sessionId}
                `
            );

        container.innerHTML = "";

        if (
            !data.answers ||
            data.answers.length === 0
        ) {

            container.innerHTML = `
                <p>
                    No answers submitted.
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
            `;

            container.appendChild(card);
        });

    } catch (err) {

        showError(
            err.message
        );
    }
}