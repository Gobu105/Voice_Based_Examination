import {
    initializeAlerts
}
from "../common/alerts.js";

import {
    loadPendingAnswers,
    loadStudentAnswers
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
    
    // Make loadStudentAnswers globally available
    window.loadStudentAnswers = loadStudentAnswers;
}