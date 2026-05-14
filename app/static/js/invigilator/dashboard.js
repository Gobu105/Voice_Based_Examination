import {
    initializeAlerts
}
from "../common/alerts.js";

import {
    loadQuestions
}
from "./questions.js";

import {
    viewAnswers
}
from "./answers.js";


document.addEventListener(

    "DOMContentLoaded",

    () => {

        initializeAlerts();

        initializeInvigilatorDashboard();
    }
);


function initializeInvigilatorDashboard() {

    console.log(
        "Invigilator dashboard initialized"
    );

    loadQuestions();
    
    // Make viewAnswers globally available
    window.viewAnswers = viewAnswers;
}