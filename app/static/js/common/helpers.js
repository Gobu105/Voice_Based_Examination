export function escapeHtml(text) {

    if (!text) return "";

    const div = document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}


export function escapeRegex(str) {

    return str.replace(
        /[.*+?^${}()|[\]\\]/g,
        "\\$&"
    );
}


export function debounce(fn, delay) {

    let timeout;

    return function (...args) {

        clearTimeout(timeout);

        timeout = setTimeout(() => {
            fn.apply(this, args);
        }, delay);
    };
}


export function throttle(fn, limit) {

    let waiting = false;

    return function (...args) {

        if (waiting) return;

        fn.apply(this, args);

        waiting = true;

        setTimeout(() => {
            waiting = false;
        }, limit);
    };
}


export function formatTime(totalSeconds) {

    const mins = Math.floor(totalSeconds / 60);

    const secs = totalSeconds % 60;

    return (
        String(mins).padStart(2, "0") +
        ":" +
        String(secs).padStart(2, "0")
    );
}