import {
    initializeAlerts
}
from "../common/alerts.js";

import {
    logAdminEvent
}
from "./users.js";


document.addEventListener(

    "DOMContentLoaded",

    () => {

        initializeAlerts();

        initializeDashboard();
    }
);


function initializeDashboard() {

    logAdminEvent(
        "Admin dashboard initialized"
    );

    initializeRegistrationToggle();
    initializeCandidateAcademicToggle();
}


function initializeRegistrationToggle() {

    const checkbox =
        document.getElementById(
            "auto-generate-reg"
        );

    const manualInput =
        document.getElementById(
            "registration-number-group"
        );

    if (
        !checkbox ||
        !manualInput
    ) {

        return;
    }

    checkbox.addEventListener(

        "change",

        () => {

            manualInput.style.display =

                checkbox.checked
                    ? "none"
                    : "block";
        }
    );
}


function initializeCandidateAcademicToggle() {

    const roleSelect =
        document.getElementById(
            "role-select"
        );

    const fields =
        document.querySelectorAll(
            ".candidate-academic-field"
        );

    if (!roleSelect || fields.length === 0) {
        return;
    }

    const syncVisibility = () => {
        fields.forEach(field => {
            field.style.display =
                roleSelect.value === "CANDIDATE"
                    ? "block"
                    : "none";
        });
    };

    roleSelect.addEventListener(
        "change",
        syncVisibility
    );

    syncVisibility();
}
