// static/js/voice/main.js

import { initializeUI } from "./ui.js";
import { initializeLogger } from "./logging.js";
import { initializeVoices } from "./tts.js";
import { startExam } from "./lifecycle.js";

const init = () => {
    initializeUI();
    initializeLogger();
    initializeVoices();

    const startBtn = document.getElementById("start-exam-btn");
if (startBtn) {
    startBtn.addEventListener("click", function handleStart() {
        window._examAutoStarted = true;
        window._examInProgress = true;

        // 1. Disable the button immediately
        startBtn.disabled = true;
        
        // 2. Visual feedback
        startBtn.textContent = "Exam in Progress...";
        startBtn.style.opacity = "0.6";
        startBtn.style.cursor = "not-allowed";
        
        // 3. Call the original start function
        if (typeof startExam === 'function') {
            startExam();
        }
        
        // 4. Remove the listener to ensure it only runs once
        startBtn.removeEventListener("click", handleStart);
    });
}
    
    // CRITICAL: Expose startExam to window so the
    // inline polling script can find it for auto-start
    window.startExam = startExam;
};

// If the DOM is already ready, run init immediately;
// otherwise, wait for DOMContentLoaded.
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
