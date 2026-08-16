// Dashboard JavaScript for SITADC Youth Hub

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    loadDashboardWidgets();
    setupNotificationBell();
    
    // Set up periodic refresh if needed
    setInterval(loadDashboardWidgets, 300000); // 5 minutes
});

function loadDashboardWidgets() {
    // Load stats row widgets
    loadStatsRow();
    
    // Load main content widgets
    loadMainContent();
}

function loadStatsRow() {
    const statsRow = document.getElementById('stats-row');
    if (!statsRow) return;
    
    // Show loading state
    statsRow.innerHTML = '<div class="col-12"><div class="text-center py-5">Loading statistics...</div></div>';
    
    // Fetch widget data from dashboard configuration
    // For now, we'll create some sample statistic widgets
    fetch('/dashboard/widget-config/stats/')
        .then(response => response.json())
        .then(data => {
            renderStatsRow(data.widgets);
        })
        .catch(error => {
            console.error('Error loading stats row:', error);
            statsRow.innerHTML = '<div class="col-12"><div class="text-center py-5 text-danger">Error loading statistics</div></div>';
        });
}

function loadMainContent() {
    const mainContent = document.getElementById('main-content');
    if (!mainContent) return;
    
    // Show loading state
    mainContent.innerHTML = '<div class="col-12"><div class="text-center py-5">Loading dashboard content...</div></div>';
    
    // Fetch widget data from dashboard configuration
    fetch('/dashboard/widget-config/main/')
        .then(response => response.json())
        .then(data => {
            renderMainContent(data.widgets);
        })
        .catch(error => {
            console.error('Error loading main content:', error);
            mainContent.innerHTML = '<div class="col-12"><div class="text-center py-5 text-danger">Error loading dashboard content</div></div>';
        });
}

function renderStatsRow(widgets) {
    const statsRow = document.getElementById('stats-row');
    if (!statsRow) return;
    
    if (widgets.length === 0) {
        statsRow.innerHTML = '<div class="col-12"><div class="alert alert-info">No statistics configured</div></div>';
        return;
    }
    
    let html = '';
    widgets.forEach(widget => {
        html += `
            <div class="col-${12/widgets.length}">
                <div class="card h-100 border-0">
                    <div class="card-body d-flex align-items-center">
                        <div class="flex-shrink-0 me-3">
                            <div class="rounded-3 p-3" style="background-color: rgba(0,86,179,0.1);">
                                <i class="${widget.icon || 'bi bi-question-circle'} fs-4 text-primary-brand"></i>
                            </div>
                        </div>
                        <div>
                            <p class="mb-0 text-muted small">${widget.title}</p>
                            <p class="mb-0 fs-5 fw-bold" id="stat-${widget.id}">${widget.value || '--'}</p>
                            ${widget.trend ? `<small class="text-${widget.trend === 'up' ? 'success' : widget.trend === 'down' ? 'danger' : 'muted'}">${widget.trend_indicator || ''} ${widget.percentage || 0}%</small>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    statsRow.innerHTML = html;
}

function renderMainContent(widgets) {
    const mainContent = document.getElementById('main-content');
    if (!mainContent) return;
    
    if (widgets.length === 0) {
        mainContent.innerHTML = '<div class="col-12"><div class="alert alert-info">No widgets configured</div></div>';
        return;
    }
    
    // Group widgets by row based on column span
    const rows = [];
    let currentRow = [];
    let currentColSpan = 0;
    
    widgets.forEach(widget => {
        if (currentColSpan + widget.column_span > 12) {
            rows.push(currentRow);
            currentRow = [widget];
            currentColSpan = widget.column_span;
        } else {
            currentRow.push(widget);
            currentColSpan += widget.column_span;
        }
    });
    
    if (currentRow.length > 0) {
        rows.push(currentRow);
    }
    
    let html = '';
    rows.forEach(row => {
        html += '<div class="row g-3 mb-4">';
        row.forEach(widget => {
            html += renderWidget(widget);
        });
        html += '</div>';
    });
    
    mainContent.innerHTML = html;
    
    // Initialize any widget-specific JavaScript
    initializeWidgets();
}

function renderWidget(widget) {
    return `
        <div class="col-${12/12 * widget.column_span}">
            <div class="card h-100 border-0">
                <div class="card-header bg-white border-0">
                    <h6 class="fw-bold mb-0">${widget.title}</h6>
                    ${widget.actions ? renderWidgetActions(widget.actions) : ''}
                </div>
                <div class="card-body p-3" id="widget-${widget.id}">
                    ${widget.loading_state ? '<div class="text-center py-4">Loading...</div>' : ''}
                </div>
            </div>
        </div>
    `;
}

function renderWidgetActions(actions) {
    if (!actions || actions.length === 0) return '';
    
    let html = '<div class="card-action-buttons d-flex justify-content-end">';
    actions.forEach(action => {
        html += `<button type="button" class="btn btn-sm btn-outline-secondary me-1" onclick="${action.handler || ''}">${action.label}</button>`;
    });
    html += '</div>';
    
    return html;
}

function initializeWidgets() {
    // Initialize any widget-specific JavaScript here
    // For example, charts, tables, etc.
    initializeStatisticWidgets();
    initializeChartWidgets();
}

function initializeStatisticWidgets() {
    // Add any initialization logic for statistic widgets
}

function initializeChartWidgets() {
    // Add any initialization logic for chart widgets
    // This would typically initialize Chart.js or similar libraries
}

function setupNotificationBell() {
    const notificationToggle = document.getElementById('notification-toggle');
    const notificationBadge = document.getElementById('notification-badge');
    
    if (notificationToggle && notificationBadge) {
        notificationToggle.addEventListener('click', function() {
            // Toggle notification dropdown or redirect to notifications page
            window.location.href = '{% url \'notifications:dashboard\' %}';
        });
        
        // Fetch unread notification count
        fetch('/notifications/api/unread-count/')
            .then(response => response.json())
            .then(data => {
                if (data.count > 0) {
                    notificationBadge.textContent = data.count;
                    notificationBadge.style.display = 'inline-block';
                }
            })
            .catch(error => {
                console.error('Error fetching notification count:', error);
            });
    }
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}