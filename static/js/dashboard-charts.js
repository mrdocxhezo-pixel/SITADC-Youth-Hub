// SITADC Youth Hub - Dashboard Charts
// Handles Chart.js initialization with user's preferred chart style

(function () {
    'use strict';

    // Chart color palette
    const CHART_COLORS = {
        primary: 'rgba(0, 86, 179, 0.8)',
        primaryLight: 'rgba(77, 148, 255, 0.8)',
        success: 'rgba(25, 135, 84, 0.8)',
        warning: 'rgba(255, 193, 7, 0.8)',
        danger: 'rgba(220, 53, 69, 0.8)',
        info: 'rgba(23, 162, 184, 0.8)',
        purple: 'rgba(111, 66, 193, 0.8)',
        orange: 'rgba(253, 126, 20, 0.8)',
        teal: 'rgba(20, 184, 166, 0.8)',
    };

    const CHART_BORDER_COLORS = {
        primary: 'rgba(0, 86, 179, 1)',
        primaryLight: 'rgba(77, 148, 255, 1)',
        success: 'rgba(25, 135, 84, 1)',
        warning: 'rgba(255, 193, 7, 1)',
        danger: 'rgba(220, 53, 69, 1)',
        info: 'rgba(23, 162, 184, 1)',
        purple: 'rgba(111, 66, 193, 1)',
        orange: 'rgba(253, 126, 20, 1)',
        teal: 'rgba(20, 184, 166, 1)',
    };

    // Get text color based on theme
    function getChartTextColor() {
        const isDark = document.body.getAttribute('data-theme') === 'dark' || 
            (!document.body.hasAttribute('data-theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
        return isDark ? '#dee2e6' : '#495057';
    }

    function getGridColor() {
        const isDark = document.body.getAttribute('data-theme') === 'dark' || 
            (!document.body.hasAttribute('data-theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
        return isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    }

    // Chart default options
    const DEFAULT_OPTIONS = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: getChartTextColor(),
                    font: {
                        family: "'Inter', system-ui, -apple-system, sans-serif",
                        size: 12,
                    },
                    padding: 20,
                },
            },
            tooltip: {
                backgroundColor: 'rgba(33, 37, 41, 0.9)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                padding: 12,
                titleFont: {
                    family: "'Inter', system-ui, -apple-system, sans-serif",
                    size: 13,
                    weight: '600',
                },
                bodyFont: {
                    family: "'Inter', system-ui, -apple-system, sans-serif",
                    size: 12,
                },
                cornerRadius: 8,
                displayColors: true,
            },
        },
        scales: {
            x: {
                ticks: {
                    color: getChartTextColor(),
                    font: {
                        family: "'Inter', system-ui, -apple-system, sans-serif",
                        size: 11,
                    },
                },
                grid: {
                    color: getGridColor(),
                    drawBorder: false,
                },
            },
            y: {
                ticks: {
                    color: getChartTextColor(),
                    font: {
                        family: "'Inter', system-ui, -apple-system, sans-serif",
                        size: 11,
                    },
                },
                grid: {
                    color: getGridColor(),
                    drawBorder: false,
                },
            },
        },
        animation: {
            duration: 750,
            easing: 'easeOutQuart',
        },
    };

    // Chart style configurations
    const CHART_STYLES = {
        bar: {
            type: 'bar',
            defaultOptions: {
                ...DEFAULT_OPTIONS,
                plugins: {
                    ...DEFAULT_OPTIONS.plugins,
                },
            },
        },
        line: {
            type: 'line',
            defaultOptions: {
                ...DEFAULT_OPTIONS,
                elements: {
                    line: {
                        tension: 0.3,
                        borderWidth: 3,
                    },
                    point: {
                        radius: 4,
                        hoverRadius: 6,
                        borderWidth: 2,
                    },
                },
            },
        },
        area: {
            type: 'line',
            defaultOptions: {
                ...DEFAULT_OPTIONS,
                elements: {
                    line: {
                        tension: 0.3,
                        borderWidth: 3,
                    },
                    point: {
                        radius: 0,
                        hoverRadius: 6,
                        borderWidth: 2,
                    },
                },
                plugins: {
                    ...DEFAULT_OPTIONS.plugins,
                    fill: true,
                },
            },
        },
        doughnut: {
            type: 'doughnut',
            defaultOptions: {
                ...DEFAULT_OPTIONS,
                cutout: '65%',
                plugins: {
                    ...DEFAULT_OPTIONS.plugins,
                    legend: {
                        ...DEFAULT_OPTIONS.plugins.legend,
                        position: 'right',
                    },
                },
            },
        },
        pie: {
            type: 'pie',
            defaultOptions: {
                ...DEFAULT_OPTIONS,
                plugins: {
                    ...DEFAULT_OPTIONS.plugins,
                    legend: {
                        ...DEFAULT_OPTIONS.plugins.legend,
                        position: 'right',
                    },
                },
            },
        },
    };

    // Generate colors for datasets
    function generateColors(count, style) {
        const colorKeys = Object.keys(CHART_COLORS);
        const colors = [];
        const borderColors = [];
        
        for (let i = 0; i < count; i++) {
            const key = colorKeys[i % colorKeys.length];
            colors.push(CHART_COLORS[key]);
            borderColors.push(CHART_BORDER_COLORS[key]);
        }
        
        // For area charts, use lighter fill
        if (style === 'area') {
            return colors.map(c => c.replace('0.8', '0.2'));
        }
        
        return { backgroundColor: colors, borderColor: borderColors };
    }

    // Create chart based on widget configuration
    function createChart(ctx, config, chartStyle, userChartPreference) {
        // Use user's preference if available, otherwise use widget config
        const style = userChartPreference || chartStyle || 'bar';
        const styleConfig = CHART_STYLES[style] || CHART_STYLES.bar;
        
        const chartType = styleConfig.type;
        const data = config.data || { labels: [], datasets: [] };
        
        // Apply colors if not already set
        if (data.datasets && data.datasets.length > 0) {
            const colorCount = Math.max(data.datasets.length, 
                Math.max(...data.datasets.map(d => (d.data || []).length)));
            const colors = generateColors(colorCount, style);
            
            data.datasets.forEach((dataset, i) => {
                if (!dataset.backgroundColor) {
                    if (style === 'doughnut' || style === 'pie') {
                        dataset.backgroundColor = colors.backgroundColor || colors;
                        dataset.borderColor = colors.borderColor || colors;
                        dataset.borderWidth = 2;
                    } else if (style === 'area') {
                        dataset.backgroundColor = colors[i] || colors[0];
                        dataset.borderColor = CHART_BORDER_COLORS[Object.keys(CHART_COLORS)[i % Object.keys(CHART_COLORS).length]];
                        dataset.fill = true;
                    } else {
                        dataset.backgroundColor = colors.backgroundColor?.[i] || colors[i] || colors.backgroundColor?.[0];
                        dataset.borderColor = colors.borderColor?.[i] || colors[i] || colors.borderColor?.[0];
                        dataset.borderWidth = style === 'line' ? 3 : 1;
                    }
                }
            });
        }
        
        const options = {
            ...styleConfig.defaultOptions,
            ...config.options,
        };
        
        // Merge scales if provided
        if (config.options?.scales) {
            options.scales = {
                ...options.scales,
                ...config.options.scales,
            };
        }
        
        return new Chart(ctx, {
            type: chartType,
            data: data,
            options: options,
        });
    }

    // Initialize all chart widgets on the page
    function initCharts() {
        const chartContainers = document.querySelectorAll('[data-chart-widget]');
        
        chartContainers.forEach(container => {
            const canvas = container.querySelector('canvas');
            if (!canvas) return;
            
            // Prevent double initialization
            if (canvas.chartInstance) {
                canvas.chartInstance.destroy();
            }
            
            try {
                const widgetConfig = JSON.parse(container.getAttribute('data-chart-widget') || '{}');
                const userChartStyle = container.getAttribute('data-user-chart-style');
                
                canvas.chartInstance = createChart(
                    canvas.getContext('2d'),
                    widgetConfig,
                    widgetConfig.defaultStyle,
                    userChartStyle
                );
            } catch (e) {
                console.error('Chart initialization failed:', e);
            }
        });
    }

    // Update all charts when theme changes
    function updateChartsForTheme() {
        const chartContainers = document.querySelectorAll('[data-chart-widget]');
        
        chartContainers.forEach(container => {
            const canvas = container.querySelector('canvas');
            if (canvas && canvas.chartInstance) {
                const textColor = getChartTextColor();
                const gridColor = getGridColor();
                
                canvas.chartInstance.options.plugins.legend.labels.color = textColor;
                canvas.chartInstance.options.scales.x.ticks.color = textColor;
                canvas.chartInstance.options.scales.y.ticks.color = textColor;
                canvas.chartInstance.options.scales.x.grid.color = gridColor;
                canvas.chartInstance.options.scales.y.grid.color = gridColor;
                canvas.chartInstance.options.plugins.tooltip.backgroundColor = 
                    document.body.getAttribute('data-theme') === 'dark' ? 'rgba(33, 37, 41, 0.9)' : 'rgba(255, 255, 255, 0.9)';
                canvas.chartInstance.options.plugins.tooltip.titleColor = 
                    document.body.getAttribute('data-theme') === 'dark' ? '#fff' : '#212529';
                canvas.chartInstance.options.plugins.tooltip.bodyColor = 
                    document.body.getAttribute('data-theme') === 'dark' ? '#fff' : '#212529';
                canvas.chartInstance.update('none');
            }
        });
    }

    // Listen for theme changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'data-theme') {
                updateChartsForTheme();
            }
        });
    });
    
    observer.observe(document.body, { attributes: true, attributeFilter: ['data-theme'] });

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function() {
        if (!document.body.hasAttribute('data-theme') || document.body.getAttribute('data-theme') === 'system') {
            updateChartsForTheme();
        }
    });

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        // Wait for Chart.js to load
        function waitForChart() {
            if (typeof Chart !== 'undefined') {
                initCharts();
            } else {
                setTimeout(waitForChart, 100);
            }
        }
        waitForChart();
    });

    // Export for external use
    window.SITADC = window.SITADC || {};
    window.SITADC.Charts = {
        init: initCharts,
        createChart: createChart,
        updateForTheme: updateChartsForTheme,
        CHART_STYLES: CHART_STYLES,
    };

})();