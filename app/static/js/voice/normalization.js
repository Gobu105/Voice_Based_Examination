/**
 * Normalize voice transcript text for display and storage
 * - Cleans up spacing and filler words
 * - Fixes common grammar issues (a/an, capitalization)
 * - Standardizes text for exam answers
 */

export function normalize(text) {
  if (!text) return text;

  // Clean up spacing
  text = text.trim().split(/\s+/).join(' ');

  // Fix "im" -> "I'm"
  text = text.replace(/\bim\b/gi, "I'm");

  // Capital I
  text = text.replace(/\bi\b/g, 'I');

  // Remove common filler words and repeated sounds
  const fillers = ['um', 'uh', 'erm', 'like', 'you know', 'sort of', 'kind of', 'basically', 'actually'];
  fillers.forEach(filler => {
    const pattern = new RegExp(`\\b${filler.replace(' ', '\\s+')}\\b`, 'gi');
    text = text.replace(pattern, '');
  });

  // Clean up spacing again after removing fillers
  text = text.trim().split(/\s+/).join(' ');

  // Fix a/an usage
  const words = text.split(' ');
  for (let i = 0; i < words.length - 1; i++) {
    if (words[i].toLowerCase() === 'a' || words[i].toLowerCase() === 'an') {
      const nextWord = words[i + 1].replace(/[^a-zA-Z]/g, '');
      if (nextWord) {
        const startsVowel = /^[aeiou]/i.test(nextWord);
        if (words[i].toLowerCase() === 'a' && startsVowel) {
          words[i] = 'an';
        } else if (words[i].toLowerCase() === 'an' && !startsVowel) {
          words[i] = 'a';
        }
      }
    }
  }
  text = words.join(' ');

  // Capitalize first letter
  if (text.length > 0) {
    text = text[0].toUpperCase() + text.slice(1);
  }

  // Capitalize after sentence endings
  text = text.replace(/([.!?]\s+)([a-z])/g, (match, separator, letter) => {
    return separator + letter.toUpperCase();
  });

  // Add period at end if missing
  if (text && !/[.!?]$/.test(text)) {
    text += '.';
  }

  return text;
}


export function updateTimerDisplay(timeString) {

    if (!els.timerBox) return;

    els.timerBox.textContent = timeString;
}


export function getUIElements() {

    return els;
}