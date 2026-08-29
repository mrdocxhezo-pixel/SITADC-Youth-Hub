// QA Module JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('qaSidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        if (sidebar && sidebar.classList.contains('show')) {
            if (!sidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
                sidebar.classList.remove('show');
            }
        }
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirm delete actions
    document.querySelectorAll('[data-confirm-delete]').forEach(function(element) {
        element.addEventListener('click', function(event) {
            if (!confirm(this.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this item?')) {
                event.preventDefault();
            }
        });
    });

    // Form validation enhancement
    document.querySelectorAll('form.needs-validation').forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Search form auto-submit on Enter
    document.querySelectorAll('.search-form input[type="search"]').forEach(function(input) {
        input.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                this.closest('form').submit();
            }
        });
    });

    // Table row click navigation
    document.querySelectorAll('table[data-row-link] tbody tr').forEach(function(row) {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function(event) {
            if (event.target.tagName !== 'A' && event.target.tagName !== 'BUTTON' &&
                !event.target.closest('a') && !event.target.closest('button')) {
                var link = this.getAttribute('data-row-link');
                if (link) {
                    window.location.href = link;
                }
            }
        });
    });

    // Toggle password visibility
    document.querySelectorAll('[data-toggle-password]').forEach(function(button) {
        button.addEventListener('click', function() {
            var targetId = this.getAttribute('data-toggle-password');
            var target = document.getElementById(targetId);
            if (target) {
                var type = target.getAttribute('type') === 'password' ? 'text' : 'password';
                target.setAttribute('type', type);
                this.querySelector('i').classList.toggle('bi-eye');
                this.querySelector('i').classList.toggle('bi-eye-slash');
            }
        });
    });

    // Copy to clipboard
    document.querySelectorAll('[data-copy]').forEach(function(button) {
        button.addEventListener('click', function() {
            var text = this.getAttribute('data-copy');
            navigator.clipboard.writeText(text).then(function() {
                var originalText = button.innerHTML;
                button.innerHTML = '<i class="bi bi-check"></i> Copied!';
                setTimeout(function() {
                    button.innerHTML = originalText;
                }, 2000);
            });
        });
    });

    // Test execution status auto-refresh
    if (document.querySelector('.test-execution-running')) {
        setInterval(function() {
            var runningElements = document.querySelectorAll('.test-execution-running[data-execution-id]');
            runningElements.forEach(function(element) {
                var executionId = element.getAttribute('data-execution-id');
                fetch('/qa/api/execution-status/' + executionId + '/')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status !== 'RUNNING') {
                            location.reload();
                        }
                    })
                    .catch(console.error);
            });
        }, 10000); // Check every 10 seconds
    }

    // Notification count auto-refresh
    function updateNotificationCount() {
        fetch('/qa/api/notification-count/')
            .then(response => response.json())
            .then(data => {
                var badge = document.querySelector('.notification-count-badge');
                if (badge) {
                    if (data.count > 0) {
                        badge.textContent = data.count;
                        badge.style.display = 'flex';
                    } else {
                        badge.style.display = 'none';
                    }
                }
            })
            .catch(console.error);
    }

    // Update notification count every 30 seconds
    setInterval(updateNotificationCount, 30000);
    updateNotificationCount(); // Initial call

    // Mark notification as read via AJAX
    document.querySelectorAll('[data-mark-read]').forEach(function(element) {
        element.addEventListener('click', function(event) {
            event.preventDefault();
            var notificationId = this.getAttribute('data-mark-read');
            fetch('/qa/notifications/' + notificationId + '/read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.closest('.notification-item').classList.add('read');
                    updateNotificationCount();
                }
            })
            .catch(console.error);
        });
    });

    // Mark all notifications as read
    var markAllRead = document.getElementById('markAllNotificationsRead');
    if (markAllRead) {
        markAllRead.addEventListener('click', function(event) {
            event.preventDefault();
            fetch('/qa/notifications/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                document.querySelectorAll('.notification-item').forEach(function(item) {
                    item.classList.add('read');
                });
                updateNotificationCount();
            })
            .catch(console.error);
        });
    }

    // Autocomplete for test cases
    var testCaseAutocomplete = document.getElementById('testCaseAutocomplete');
    if (testCaseAutocomplete) {
        var debounceTimer;
        testCaseAutocomplete.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                var query = testCaseAutocomplete.value;
                if (query.length >= 2) {
                    fetch('/qa/api/test-case-autocomplete/?q=' + encodeURIComponent(query))
                        .then(response => response.json())
                        .then(data => {
                            showAutocompleteResults(testCaseAutocomplete, data.results, 'test_case');
                        })
                        .catch(console.error);
                } else {
                    hideAutocompleteResults(testCaseAutocomplete);
                }
            }, 300);
        });
    }

    // Autocomplete for defects
    var defectAutocomplete = document.getElementById('defectAutocomplete');
    if (defectAutocomplete) {
        var debounceTimer;
        defectAutocomplete.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                var query = defectAutocomplete.value;
                if (query.length >= 2) {
                    fetch('/qa/api/defect-autocomplete/?q=' + encodeURIComponent(query))
                        .then(response => response.json())
                        .then(data => {
                            showAutocompleteResults(defectAutocomplete, data.results, 'defect');
                        })
                        .catch(console.error);
                } else {
                    hideAutocompleteResults(defectAutocomplete);
                }
            }, 300);
        });
    }

    function showAutocompleteResults(input, results, type) {
        var container = document.getElementById(input.id + '-results');
        if (!container) {
            container = document.createElement('div');
            container.id = input.id + '-results';
            container.className = 'autocomplete-results position-absolute w-100 bg-white border rounded shadow-sm mt-1';
            container.style.zIndex = '1000';
            input.parentNode.appendChild(container);
        }
        container.innerHTML = '';
        results.forEach(function(result) {
            var item = document.createElement('div');
            item.className = 'autocomplete-item px-3 py-2 hover-bg-light cursor-pointer';
            item.textContent = result.text;
            item.addEventListener('click', function() {
                input.value = result.text;
                if (input.dataset.hiddenInput) {
                    document.getElementById(input.dataset.hiddenInput).value = result.id;
                }
                hideAutocompleteResults(input);
            });
            container.appendChild(item);
        });
        container.style.display = 'block';
    }

    function hideAutocompleteResults(input) {
        var container = document.getElementById(input.id + '-results');
        if (container) {
            container.style.display = 'none';
        }
    }

    // Hide autocomplete when clicking outside
    document.addEventListener('click', function(event) {
        document.querySelectorAll('.autocomplete-results').forEach(function(container) {
            if (!container.contains(event.target) && container.id !== event.target.id + '-results') {
                container.style.display = 'none';
            }
        });
    });

    // Drag and drop for test suite ordering
    var sortableLists = document.querySelectorAll('.sortable-list');
    sortableLists.forEach(function(list) {
        new Sortable(list, {
            animation: 150,
            handle: '.drag-handle',
            onEnd: function(evt) {
                var items = list.querySelectorAll('[data-sortable-id]');
                var order = [];
                items.forEach(function(item, index) {
                    order.push({
                        id: item.getAttribute('data-sortable-id'),
                        order: index + 1
                    });
                });
                fetch(list.getAttribute('data-sort-url'), {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ order: order })
                }).catch(console.error);
            }
        });
    });

    // Chart initialization placeholder
    if (typeof Chart !== 'undefined') {
        // Quality trend chart
        var trendChart = document.getElementById('qualityTrendChart');
        if (trendChart) {
            new Chart(trendChart, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Quality Score',
                        data: [],
                        borderColor: '#4e73df',
                        backgroundColor: 'rgba(78, 115, 223, 0.1)',
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true, max: 100 }
                    }
                }
            });
        }

        // Defect severity chart
        var severityChart = document.getElementById('defectSeverityChart');
        if (severityChart) {
            new Chart(severityChart, {
                type: 'doughnut',
                data: {
                    labels: ['Blocker', 'Critical', 'High', 'Medium', 'Low'],
                    datasets: [{
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: ['#5a5c69', '#e74a3b', '#f6c23e', '#36b9cc', '#1cc88a']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }

    // Utility function to get CSRF token
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + K for search
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            var searchInput = document.querySelector('input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape to close modals
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal.show').forEach(function(modal) {
                var bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
        }
    });

    console.log('QA Module JavaScript initialized');
});