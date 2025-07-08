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

// export function formatDate(dateString: string) {
// 	if (dateString) {
// 		let [year, month, day] = dateString.split('-');
// 		return new Date(+year, +month - 1, +day);
// 	}
// }

export function formatDate(timestamp: number | null | undefined): Date {
	if (timestamp == null) return new Date('2024-01-01'); // fallback

	// If it's in seconds, convert to milliseconds
	const ms = timestamp < 10 ** 12 ? timestamp * 1000 : timestamp;

	return new Date(ms);
}

// export function epochToDate(epoch:GLfloat){
	
// }

export function range(start: number, end: number): number[] {
  return [...Array(end - start + 1)].map((_, i) => start + i);
}