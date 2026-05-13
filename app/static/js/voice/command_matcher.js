import {
    COMMAND_THRESHOLD
}
from "./config.js";


export function matchCommand(
    transcript,
    commands
) {

    let bestMatch = null;

    let bestScore = 0;

    for (const [name, cmd]
        of Object.entries(commands)) {

        for (const synonym of cmd.synonyms) {

            // Exact match
            if (
                transcript.includes(synonym)
            ) {

                return {
                    name,
                    action: cmd.action,
                    score: 1.0
                };
            }

            // Word overlap
            const overlapScore =
                wordOverlap(
                    transcript,
                    synonym
                );

            if (
                overlapScore > bestScore
            ) {

                bestScore = overlapScore;

                bestMatch = {
                    name,
                    action: cmd.action,
                    score: overlapScore
                };
            }

            // Similarity score
            const simScore =
                similarity(
                    transcript,
                    synonym
                );

            if (
                simScore > bestScore
            ) {

                bestScore = simScore;

                bestMatch = {
                    name,
                    action: cmd.action,
                    score: simScore
                };
            }
        }
    }

    if (
        bestMatch &&
        bestMatch.score >= COMMAND_THRESHOLD
    ) {

        return bestMatch;
    }

    return null;
}


function wordOverlap(a, b) {

    const wordsA =
        new Set(a.split(/\s+/));

    const wordsB =
        b.split(/\s+/);

    if (wordsB.length === 0) {
        return 0;
    }

    let hits = 0;

    for (const word of wordsB) {

        if (wordsA.has(word)) {
            hits++;
        }
    }

    return hits / wordsB.length;
}


function similarity(a, b) {

    const distance =
        levenshtein(a, b);

    const maxLen =
        Math.max(
            a.length,
            b.length
        );

    if (maxLen === 0) {
        return 1;
    }

    return 1 - (
        distance / maxLen
    );
}


function levenshtein(a, b) {

    const m = a.length;

    const n = b.length;

    const dp = Array.from(
        { length: m + 1 },
        () => new Array(n + 1).fill(0)
    );

    for (let i = 0; i <= m; i++) {
        dp[i][0] = i;
    }

    for (let j = 0; j <= n; j++) {
        dp[0][j] = j;
    }

    for (let i = 1; i <= m; i++) {

        for (let j = 1; j <= n; j++) {

            const cost =
                a[i - 1] === b[j - 1]
                    ? 0
                    : 1;

            dp[i][j] = Math.min(

                dp[i - 1][j] + 1,

                dp[i][j - 1] + 1,

                dp[i - 1][j - 1] + cost
            );
        }
    }

    return dp[m][n];
}