import {
    apiGet
}
from "../common/api.js";

import {
    showError
}
from "../common/alerts.js";


export async function loadResults(
    examId
) {

    const container =
        document.getElementById(
            "results-container"
        );

    if (!container) {
        return;
    }

    try {

        const data =
            await apiGet(
                `
                /invigilator/results/${examId}
                `
            );

        container.innerHTML = "";

        if (
            !data.results ||
            data.results.length === 0
        ) {

            container.innerHTML = `
                <p>
                    No results available.
                </p>
            `;

            return;
        }

        data.results.forEach(result => {

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "result-row";

            row.innerHTML = `

                <strong>
                    ${result.student_name}
                </strong>

                <span>
                    ${result.marks}
                </span>

                <span>
                    ${result.grade}
                </span>
            `;

            container.appendChild(row);
        });

    } catch (err) {

        showError(
            err.message
        );
    }
}