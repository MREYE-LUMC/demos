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
    var lastHeight = iframe.contentWindow.document.body.scrollHeight;

    const iframeObserver = new MutationObserver(() => {
        const newHeight = iframe.contentWindow.document.body.scrollHeight;

        if (newHeight !== lastHeight) {
            console.log(`Resizing iframe from ${lastHeight}px to ${newHeight}px`);
            lastHeight = newHeight;
            iframe.style.height = `${newHeight + offset}px`;
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
        iframe.style.height = `${iframe.contentWindow.document.body.scrollHeight + 30}px`; // Initial height adjustment
        registerObserver(iframe, 30); // Initial offset to account for padding/margin
    });
});