(() => {
    const IFRAME_OFFSET = 30; // Offset to account for padding/margin

    const isIframeLoaded = (selector) => {
        // Check if the iframe exists and has a valid src attribute
        const iframe = document.querySelector(selector);
        return iframe && iframe.src;
    }

    const waitForIframeLoad = (selector) => {
        return new Promise((resolve) => {
            if (isIframeLoaded(selector)) {
                return resolve(document.querySelector(selector));
            }

            const observer = new MutationObserver(() => {
                if (isIframeLoaded(selector)) {
                    observer.disconnect();
                    resolve(document.querySelector(selector));
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true,
            });
        });
    }

    const registerObserver = (iframe, offset) => {
        if (!iframe.contentWindow?.document?.body) {
            console.error("Iframe content is not accessible.");
            return;
        }

        let lastHeight = iframe.contentWindow.document.body.scrollHeight;
        let resizeTimeout;

        const iframeObserver = new MutationObserver(() => {
            try {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(() => {
                    const newHeight = iframe.contentWindow.document.body.scrollHeight;

                    if (newHeight !== lastHeight) {
                        console.log(`Resizing iframe from ${lastHeight}px to ${newHeight}px`);
                        lastHeight = newHeight;
                        iframe.style.height = `${newHeight + offset}px`;
                    }
                }, 100); // Debounce resize to avoid rapid firing
            } catch (e) {
                console.error("Error accessing iframe content:", e);
            }
        });

        iframeObserver.observe(iframe.contentWindow.document.body, {
            subtree: true,
            childList: true,
        });
    }

    waitForIframeLoad('iframe.app-frame').then((iframe) => {
        console.log("Iframe loaded, starting resize observer");

        iframe.addEventListener('load', () => {
            try {
                iframe.style.height = `${iframe.contentWindow.document.body.scrollHeight + IFRAME_OFFSET}px`; // Initial height adjustment
                registerObserver(iframe, IFRAME_OFFSET);
            } catch (e) {
                console.error("Error accessing iframe content on load:", e);
            }
        });
    });
})();