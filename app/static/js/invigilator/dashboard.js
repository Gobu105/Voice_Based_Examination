import {
    initializeAlerts
}
from "../common/alerts.js";

import {
    loadQuestions
}
from "./questions.js";


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
}