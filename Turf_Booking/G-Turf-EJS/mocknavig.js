// const natural = require('natural');
// // Dictionary of correct words
// const dictionary = ['Thiruvanmiyur'];
// const spellcheck = new natural.Spellcheck(dictionary);



// // Input text
// const inputText = 'Tiruvānmiyūr';

// // Find the best spelling correction
// const correctedWord = spellcheck.getCorrections(inputText, 1)[0];
// console.log(`Did you mean: ${correctedWord}?`);

import translate from 'translate';

async function translateText() {
    try {
        // Set the source and target languages
        translate.engine = 'google';
        translate.from = 'lv'; // Latvian
        translate.to = 'en'; // English

        const inputText = 'Tiruvānmiyūr';
        const translatedText =await translate(inputText);

        console.log('Translated Text:', translatedText);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

translateText();
