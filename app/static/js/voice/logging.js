let logBox = null;


export function initializeLogger() {

    logBox =
        document.getElementById(
            "activity-log"
        );
}


export function log(
    message,
    type = "info"
) {

    const ts =
        new Date()
            .toLocaleTimeString("en-IN");

    const entry =
        `[${ts}] ${message}`;

    console.log(entry);

    if (!logBox) return;

    const div =
        document.createElement("div");

    div.className =
        `log-entry ${type}`;

    div.textContent = entry;

    logBox.prepend(div);
}


export function logError(message) {

    log(message, "error");
}


export function logWarning(message) {

    log(message, "warning");
}


export function clearLogs() {

    if (!logBox) return;

    logBox.innerHTML = "";
}