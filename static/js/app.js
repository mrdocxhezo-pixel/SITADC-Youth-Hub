// SITADC Youth Hub Base Scripts

document.addEventListener('DOMContentLoaded', function () {
    // Dynamically set the current year in the footer
    const yearSpan = document.getElementById('current-year');
    if (yearSpan) {
        yearSpan.textContent = new Date().getFullYear();
    }

    // Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.dashboard-sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function (e) {
            e.preventDefault();
            sidebar.classList.toggle('show');
        });
    }

    if (window.bootstrap) {
        // Initialize Bootstrap Toasts
        const toastElList = document.querySelectorAll('.toast');
        const toastList = [...toastElList].map((toastEl) => new window.bootstrap.Toast(toastEl));
        toastList.forEach((toast) => toast.show());

        // Initialize Bootstrap Tooltips
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipTriggerList.forEach(
            (tooltipTriggerEl) => new window.bootstrap.Tooltip(tooltipTriggerEl)
        );
    }

    // Keep tabbed content usable independently of the Bootstrap CDN.
    const tabTriggers = [...document.querySelectorAll('[data-bs-toggle="tab"]')];
    const activateTab = (trigger) => {
        const targetSelector = trigger.getAttribute('data-bs-target');
        const target = targetSelector ? document.querySelector(targetSelector) : null;
        if (!target) return;

        const tabList = trigger.closest('[role="tablist"]');
        const tabContent = target.closest('.tab-content');
        tabList?.querySelectorAll('[role="tab"]').forEach((tab) => {
            tab.classList.remove('active');
            tab.setAttribute('aria-selected', 'false');
        });
        tabContent?.querySelectorAll('[role="tabpanel"]').forEach((panel) => {
            panel.classList.remove('active', 'show');
        });
        trigger.classList.add('active');
        trigger.setAttribute('aria-selected', 'true');
        target.classList.add('active', 'show');
    };

    tabTriggers.forEach((trigger, index) => {
        trigger.addEventListener('click', () => activateTab(trigger));
        trigger.addEventListener('keydown', (event) => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
            event.preventDefault();
            let nextIndex = index;
            if (event.key === 'ArrowLeft')
                nextIndex = (index - 1 + tabTriggers.length) % tabTriggers.length;
            if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabTriggers.length;
            if (event.key === 'Home') nextIndex = 0;
            if (event.key === 'End') nextIndex = tabTriggers.length - 1;
            tabTriggers[nextIndex].focus();
            activateTab(tabTriggers[nextIndex]);
        });
    });

    // Confirmation Dialog Handlers
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach((button) => {
        button.addEventListener('click', function (e) {
            if (
                !confirm(this.getAttribute('data-confirm') || 'Are you sure you want to proceed?')
            ) {
                e.preventDefault();
            }
        });
    });
});
