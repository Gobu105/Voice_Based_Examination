let container = null;


export function initializeAlerts() {

    container =
        document.getElementById(
            "toast-container"
        );

    if (!container) {

        container =
            document.createElement(
                "div"
            );

        container.id =
            "toast-container";

        document.body.appendChild(
            container
        );
    }
}


export function showToast(
    message,
    type = "info"
) {

    const toast =
        document.createElement(
            "div"
        );

    toast.className =
        `toast toast-${type}`;

    toast.textContent =
        message;

    container.appendChild(
        toast
    );

    setTimeout(() => {

        toast.remove();

    }, 4000);
}


export function showSuccess(
    message
) {

    showToast(
        message,
        "success"
    );
}


export function showError(
    message
) {

    showToast(
        message,
        "error"
    );
}