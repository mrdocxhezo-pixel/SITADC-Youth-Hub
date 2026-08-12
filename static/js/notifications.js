// SITADC Youth Hub - Notifications & Announcements
// Bell polling, dropdown rendering and AJAX read/dismiss actions.

(function () {
    'use strict';

    const UNREAD_URL = '/notifications/api/unread-count/';
    const RECENT_URL = '/notifications/api/recent-notifications/';

    function fetchJson(url) {
        return fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin',
        }).then(function (response) {
            if (!response.ok) {
                return Promise.reject(new Error('Notification request failed'));
            }
            return response.json();
        });
    }

    function getCsrfToken() {
        const cookie = document.cookie
            .split(';')
            .map(function (part) { return part.trim(); })
            .find(function (part) { return part.indexOf('csrftoken=') === 0; });
        return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
    }

    function postJson(url) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(),
            },
            credentials: 'same-origin',
        });
    }

    function updateBellBadge(unreadCount) {
        document.querySelectorAll('[data-notification-badge]').forEach(function (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount > 99 ? '99+' : String(unreadCount);
                badge.classList.remove('d-none');
            } else {
                badge.textContent = '';
                badge.classList.add('d-none');
            }
        });
    }

    function renderDropdown(items) {
        const list = document.getElementById('notificationDropdownList');
        if (!list) return;
        list.innerHTML = '';
        const empty = document.createElement('li');
        empty.className = 'dropdown-item py-3 text-muted text-center small';
        if (!items || !items.length) {
            empty.textContent = 'You have no notifications.';
            list.appendChild(empty);
            return;
        }
        items.forEach(function (item) {
            const li = document.createElement('li');
            const link = document.createElement('a');
            link.href = item.url;
            link.className = 'dropdown-item py-3 border-bottom text-wrap';
            const title = document.createElement('small');
            title.className = 'fw-bold d-block';
            title.textContent = item.title;
            const body = document.createElement('span');
            body.className = 'text-muted small d-block text-truncate';
            body.style.maxWidth = '250px';
            body.textContent = item.short_message || item.title;
            link.appendChild(title);
            link.appendChild(body);
            li.appendChild(link);
            list.appendChild(li);
        });
    }

    function refreshNotifications() {
        fetchJson(UNREAD_URL).then(function (data) {
            updateBellBadge(data.unread || 0);
        }).catch(function () {
            /* Bell is non-critical; ignore transient failures. */
        });
    }

    function refreshRecent() {
        fetchJson(RECENT_URL).then(function (data) {
            updateBellBadge(data.unread || 0);
            renderDropdown(data.items || []);
        }).catch(function () {
            /* Ignore transient failures. */
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        refreshNotifications();
        refreshRecent();

        // Refresh the dropdown each time it is opened.
        const dropdownButton = document.getElementById('notificationDropdown');
        if (dropdownButton) {
            dropdownButton.addEventListener('show.bs.dropdown', refreshRecent);
        }

        // Wire AJAX mark-read / dismiss forms.
        document.body.addEventListener('submit', function (event) {
            const form = event.target;
            const action = form.getAttribute('data-notification-ajax');
            if (!action) return;
            event.preventDefault();
            const url = form.getAttribute('action');
            postJson(url).then(function (response) {
                return response.ok ? response.json() : Promise.reject(new Error('Action failed'));
            }).then(function () {
                refreshNotifications();
                const row = form.closest('[data-notification-row]');
                const dismissForm = form.dataset.dismiss === 'true';
                const dismissRow = row && (row.dataset.dismiss === 'true' || dismissForm);
                if (dismissRow) {
                    row.remove();
                }
            }).catch(function () {
                form.submit();
            });
        });

        // Poll periodically so the bell badge stays fresh.
        setInterval(refreshNotifications, 60000);
    });
})();
