export function $(selector) {

    return document.querySelector(
        selector
    );
}


export function $all(selector) {

    return document.querySelectorAll(
        selector
    );
}


export function show(el) {

    if (!el) return;

    el.style.display = "";
}


export function hide(el) {

    if (!el) return;

    el.style.display = "none";
}


export function toggle(
    el,
    condition
) {

    if (!el) return;

    el.style.display =
        condition
            ? ""
            : "none";
}


export function disable(el) {

    if (!el) return;

    el.disabled = true;
}


export function enable(el) {

    if (!el) return;

    el.disabled = false;
}


export function clear(el) {

    if (!el) return;

    el.innerHTML = "";
}