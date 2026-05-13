import { log }
from "./logging.js";


export async function startExamAPI() {

    try {

        const response =
            await fetch("/api/start_exam");

        return await response.json();

    } catch (err) {

        log(
            `Start exam API error: ${err}`
        );

        throw err;
    }
}


export async function getQuestionsAPI() {

    try {

        const response =
            await fetch("/api/questions");

        return await response.json();

    } catch (err) {

        log(
            `Questions API error: ${err}`
        );

        throw err;
    }
}


export async function saveAnswerAPI(
    questionId,
    answer
) {

    try {

        const response =
            await fetch(
                "/api/save_answer",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        question_id: questionId,
                        answer: answer
                    })
                }
            );

        return await response.json();

    } catch (err) {

        log(
            `Save answer API error: ${err}`
        );

        throw err;
    }
}


export async function submitExamAPI() {

    try {

        const response =
            await fetch(
                "/api/submit_exam",
                {
                    method: "POST",

                    credentials:
                        "same-origin"
                }
            );

        return await response.json();

    } catch (err) {

        log(
            `Submit exam API error: ${err}`
        );

        throw err;
    }
}