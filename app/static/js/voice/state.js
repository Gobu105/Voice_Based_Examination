export const state = {

    questions: [],

    questionIds: [],

    answers: [],

    currentIndex: -1,

    examSessionId: null,

    isListening: false,

    examActive: false,

    ttsActive: false,

    restartTimer: null,

    cooldownUntil: 0,

    timerInterval: null,

    remainingSeconds: 0,

    lastAnnouncedQuarter: -1,

    autosaveTimer: null,

    lastSavedAt: null,

    saveInProgress: false,

    pendingSubmission: false,

    syncedAnswers: {},

    pendingAnswers: {},

    networkOnline: navigator.onLine,

    lastSaveError: null,

    saveStatus: 'idle',
};
