const PHRASE_NORMALIZATIONS = new Map([
    ["agla question", "next question"],
    ["agla sawal", "next question"],
    ["pichla question", "previous question"],
    ["pichla sawal", "previous question"],
    ["dobara", "repeat question"],
    ["jama karo", "submit exam"],
]);


export function normalizeCommandLanguage(text) {

    let normalized =
        text;

    for (const [source, target] of PHRASE_NORMALIZATIONS.entries()) {
        normalized =
            normalized.replace(
                new RegExp(`\\b${source}\\b`, "gi"),
                target
            );
    }

    return normalized;
}
