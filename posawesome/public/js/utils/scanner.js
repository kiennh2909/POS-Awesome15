
// Scanner utility based on onScan.js library
export const onScan = {
	attachTo: function(element, options) {
		if (!element || typeof element.addEventListener !== 'function') {
			console.warn('Invalid element provided to onScan.attachTo');
			return;
		}

		const config = {
			onScan: options.onScan || function() {},
			onKeyDetect: options.onKeyDetect || function() {},
			keyCodeMapper: options.keyCodeMapper || this.decodeKeyEvent,
			avgTimeByChar: options.avgTimeByChar || 30,
			minLength: options.minLength || 6,
			endChar: options.endChar || [13], // Enter key
			suffixKeyCodes: options.suffixKeyCodes || []
		};

		let scanBuffer = [];
		let lastKeyTime = Date.now();
		let scanning = false;

		const keyHandler = (e) => {
			const currentTime = Date.now();
			const timeDiff = currentTime - lastKeyTime;
			
			if (config.keyCodeMapper) {
				config.keyCodeMapper(e);
			}

			// Check if this could be part of a barcode scan
			if (timeDiff < config.avgTimeByChar * 3) {
				scanning = true;
				scanBuffer.push(String.fromCharCode(e.keyCode));
			} else if (scanning) {
				// Time gap too large, reset buffer
				scanBuffer = [String.fromCharCode(e.keyCode)];
			}

			lastKeyTime = currentTime;

			// Check for end characters
			if (config.endChar.includes(e.keyCode) && scanning && scanBuffer.length >= config.minLength) {
				const scannedCode = scanBuffer.join('').trim();
				if (scannedCode.length >= config.minLength) {
					config.onScan(scannedCode, scanBuffer.length);
				}
				scanBuffer = [];
				scanning = false;
			}

			// Auto-clear buffer after timeout
			setTimeout(() => {
				if (Date.now() - lastKeyTime > config.avgTimeByChar * 3) {
					scanBuffer = [];
					scanning = false;
				}
			}, config.avgTimeByChar * 3);

			if (config.onKeyDetect) {
				config.onKeyDetect(e, scannedCode);
			}
		};

		element.addEventListener('keydown', keyHandler);

		// Store cleanup function
		if (!element._onScanCleanup) {
			element._onScanCleanup = [];
		}
		element._onScanCleanup.push(() => {
			element.removeEventListener('keydown', keyHandler);
		});
	},

	detachFrom: function(element) {
		if (element && element._onScanCleanup) {
			element._onScanCleanup.forEach(cleanup => cleanup());
			element._onScanCleanup = [];
		}
	},

	decodeKeyEvent: function(e) {
		// Basic key event decoder
		return {
			keyCode: e.keyCode,
			key: e.key,
			char: String.fromCharCode(e.keyCode)
		};
	}
};
