import {
    initializeAlerts
}
from "../common/alerts.js";

import {
    loadPendingAnswers
}
from "./grading.js";


document.addEventListener(

    "DOMContentLoaded",

    () => {

        initializeAlerts();

        initializeExaminerDashboard();
    }
);


function initializeExaminerDashboard() {

    console.log(
        "Examiner dashboard initialized"
    );

    loadPendingAnswers();
}