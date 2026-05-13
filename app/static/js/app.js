import {
    initializeAlerts
}
from "./common/alerts.js";


document.addEventListener(

    "DOMContentLoaded",

    () => {

        initializeApp();
    }
);


function initializeApp() {

    initializeAlerts();

    initializeNavigation();

    initializeGlobalForms();

    initializeConfirmActions();

    console.log(
        "Application initialized"
    );
}


function initializeNavigation() {

    const currentPath =
        window.location.pathname;

    const navLinks =
        document.querySelectorAll(
            "[data-nav]"
        );

    navLinks.forEach(link => {

        const target =
            link.dataset.nav;

        if (
            currentPath.includes(target)
        ) {

            link.classList.add(
                "active"
            );
        }
    });
}


function initializeGlobalForms() {

    const forms =
        document.querySelectorAll(
            "form[data-disable-submit]"
        );

    forms.forEach(form => {

        form.addEventListener(

            "submit",

            () => {

                const btn =
                    form.querySelector(
                        `
                        button[type="submit"]
                        `
                    );

                if (btn) {

                    btn.disabled = true;

                    btn.textContent =
                        "Processing...";
                }
            }
        );
    });
}


function initializeConfirmActions() {

    const buttons =
        document.querySelectorAll(
            "[data-confirm]"
        );

    buttons.forEach(btn => {

        btn.addEventListener(

            "click",

            event => {

                const msg =
                    btn.dataset.confirm;

                const ok =
                    confirm(msg);

                if (!ok) {

                    event.preventDefault();

                    event.stopPropagation();
                }
            }
        );
    });
}