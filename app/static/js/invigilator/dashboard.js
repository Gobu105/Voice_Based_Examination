import {
    initializeAlerts
}
from "../common/alerts.js";

document.addEventListener(

    "DOMContentLoaded",

    () => {

        console.log("Dashboard DOM loaded");

        initializeAlerts();

        initializeInvigilatorDashboard();
    }
);


function initializeInvigilatorDashboard() {

    console.log(
        "Invigilator dashboard initialized"
    );

}
