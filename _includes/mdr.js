(function () {
    const sessionStorageKey = 'shown-mdr-modal-' + window.location.pathname;

    document.addEventListener('DOMContentLoaded', function () {
        if (sessionStorage.getItem(sessionStorageKey) != 'true') {
            let mdrModal = new bootstrap.Modal(document.getElementById('mdr-modal'));
            mdrModal.show();
        }
    });

    document.getElementById('dismiss-mdr-modal').addEventListener('click', function () {
        sessionStorage.setItem(sessionStorageKey, 'true');
    });
})();