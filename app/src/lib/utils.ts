// Function to split text into lines based on a maximum length for formatting
export const splitTextIntoLines = (text: string, maxLength: number) => {
	const words = text.split(' ');
	const lines = [];
	let currentLine = '';

	for (const word of words) {
		if (currentLine.length + word.length + 1 <= maxLength) {
			// Add word to current line
			currentLine += (currentLine ? ' ' : '') + word;
		} else {
			// Start a new line
			if (currentLine) {
				lines.push(currentLine);
				currentLine = '';
			}

			// Handle long words
			if (word.length > maxLength) {
				let remainingWord = word;
				while (remainingWord.length > maxLength) {
					lines.push(remainingWord.slice(0, maxLength - 1) + '-');
					remainingWord = remainingWord.slice(maxLength - 1);
				}
				currentLine = remainingWord;
			} else {
				currentLine = word;
			}
		}
	}

	// Add the last line if it's not empty
	if (currentLine) {
		lines.push(currentLine);
	}

	return lines.join('\n');
};

export function formatDate(dateString: string) {
	if (dateString) {
		let [day, month, year] = dateString.split('/');
		return new Date(+year, +month - 1, +day);
	}
}
