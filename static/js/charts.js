
const CHART_COLORS = {
    primary: '#2E86AB',
    secondary: '#A23B72',
    success: '#28A745',
    warning: '#FFC107',
    danger: '#DC3545',
    info: '#17A2B8',
    
    // Health-specific
    malaria: '#DC3545',
    maternal: '#A23B72',
    child: '#28A745',
    hiv: '#FFC107',
    tb: '#17A2B8',
    
    // Gradients
    gradientBlue: ['#c6e2ff', '#2E86AB'],
    gradientGreen: ['#d4edda', '#28A745'],
    gradientRed: ['#f8d7da', '#DC3545']
};

const CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'bottom',
            labels: {
                font: {
                    family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                    size: 12
                }
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleFont: { size: 14, weight: 'bold' },
            bodyFont: { size: 13 },
            padding: 10,
            cornerRadius: 4
        }
    }
};

// ============================================================================
// CHART MANAGER
// ============================================================================

const HealthCharts = {
    charts: {},
    
    init() {
        console.log('Initializing charts...');
        this.initTrendCharts();
        this.initComparisonCharts();
        this.initDistributionCharts();
        this.initMalariaCharts();
        this.initMaternalCharts();
    },
    
    // Create new chart
    create(chartId, type, data, options = {}) {
        const canvas = document.getElementById(chartId);
        if (!canvas) {
            console.warn(`Canvas element not found: ${chartId}`);
            return null;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Merge with defaults
        const chartOptions = { ...CHART_DEFAULTS, ...options };
        
        // Create chart
        const chart = new Chart(ctx, {
            type: type,
            data: data,
            options: chartOptions
        });
        
        // Store reference
        this.charts[chartId] = chart;
        
        return chart;
    },
    
    // Update existing chart
    update(chartId, newData) {
        const chart = this.charts[chartId];
        if (!chart) return;
        
        chart.data = newData;
        chart.update();
    },
    
    // Destroy chart
    destroy(chartId) {
        const chart = this.charts[chartId];
        if (chart) {
            chart.destroy();
            delete this.charts[chartId];
        }
    },
    
    // ============================================================================
    // TREND CHARTS
    // ============================================================================
    
    initTrendCharts() {
        document.querySelectorAll('[data-chart="trend"]').forEach(element => {
            const facilityId = element.dataset.facility;
            const metric = element.dataset.metric || 'opd_visits';
            
            this.loadTrendData(element.id, facilityId, metric);
        });
    },
    
    loadTrendData(chartId, facilityId, metric) {
        const url = `/api/trends/${facilityId}?metric=${metric}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.createTrendChart(chartId, data);
            })
            .catch(error => {
                console.error('Failed to load trend data:', error);
            });
    },
    
    createTrendChart(chartId, data) {
        const chartData = {
            labels: data.labels,
            datasets: [{
                label: data.metric,
                data: data.values,
                borderColor: CHART_COLORS.primary,
                backgroundColor: 'rgba(46, 134, 171, 0.1)',
                borderWidth: 2,
                pointRadius: 3,
                pointHoverRadius: 5,
                tension: 0.1,
                fill: true
            }]
        };
        
        const options = {
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0,0,0,0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `${data.metric} Trends Over Time`
                }
            }
        };
        
        this.create(chartId, 'line', chartData, options);
    },
    
    // ============================================================================
    // COMPARISON CHARTS
    // ============================================================================
    
    initComparisonCharts() {
        document.querySelectorAll('[data-chart="comparison"]').forEach(element => {
            const facilityIds = element.dataset.facilities?.split(',') || [];
            const metric = element.dataset.metric || 'opd_visits';
            const week = element.dataset.week;
            const year = element.dataset.year;
            
            this.loadComparisonData(element.id, facilityIds, metric, week, year);
        });
    },
    
    loadComparisonData(chartId, facilityIds, metric, week, year) {
        const url = `/api/comparison?facilities=${facilityIds.join(',')}&metric=${metric}&week=${week}&year=${year}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.createComparisonChart(chartId, data);
            })
            .catch(error => {
                console.error('Failed to load comparison data:', error);
            });
    },
    
    createComparisonChart(chartId, data) {
        const chartData = {
            labels: data.facilities,
            datasets: [{
                label: data.metric,
                data: data.values,
                backgroundColor: data.values.map((v, i) => 
                    i === 0 ? CHART_COLORS.success : 
                    i === data.values.length - 1 ? CHART_COLORS.danger : 
                    CHART_COLORS.primary
                ),
                borderRadius: 4
            }]
        };
        
        const options = {
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0,0,0,0.05)' }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `Facility Comparison - ${data.metric}`
                },
                legend: { display: false }
            }
        };
        
        this.create(chartId, 'bar', chartData, options);
    },
    
    // ============================================================================
    // DISTRIBUTION CHARTS
    // ============================================================================
    
    initDistributionCharts() {
        document.querySelectorAll('[data-chart="distribution"]').forEach(element => {
            const facilityId = element.dataset.facility;
            const metric = element.dataset.metric || 'opd_visits';
            
            this.loadDistributionData(element.id, facilityId, metric);
        });
    },
    
    loadDistributionData(chartId, facilityId, metric) {
        const url = `/api/distribution/${facilityId}?metric=${metric}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.createDistributionChart(chartId, data);
            })
            .catch(error => {
                console.error('Failed to load distribution data:', error);
            });
    },
    
    createDistributionChart(chartId, data) {
        const chartData = {
            labels: data.bins,
            datasets: [{
                label: 'Frequency',
                data: data.frequencies,
                backgroundColor: CHART_COLORS.primary,
                borderColor: CHART_COLORS.primary,
                borderWidth: 1
            }]
        };
        
        const options = {
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0,0,0,0.05)' }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `Distribution of ${data.metric}`
                }
            }
        };
        
        this.create(chartId, 'bar', chartData, options);
    },
    
    // ============================================================================
    // MALARIA SURVEILLANCE CHARTS
    // ============================================================================
    
    initMalariaCharts() {
        document.querySelectorAll('[data-chart="malaria"]').forEach(element => {
            const facilityId = element.dataset.facility;
            
            this.loadMalariaData(element.id, facilityId);
        });
    },
    
    loadMalariaData(chartId, facilityId) {
        const url = `/api/malaria/${facilityId}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.createMalariaChart(chartId, data);
            })
            .catch(error => {
                console.error('Failed to load malaria data:', error);
            });
    },
    
    createMalariaChart(chartId, data) {
        // Create dual-axis chart
        const ctx = document.getElementById(chartId).getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.weeks,
                datasets: [
                    {
                        label: 'Tested',
                        data: data.tested,
                        borderColor: CHART_COLORS.info,
                        backgroundColor: 'rgba(23, 162, 184, 0.1)',
                        yAxisID: 'y',
                        fill: false
                    },
                    {
                        label: 'Positive',
                        data: data.positive,
                        borderColor: CHART_COLORS.danger,
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        yAxisID: 'y',
                        fill: false
                    },
                    {
                        label: 'Positivity Rate',
                        data: data.rates,
                        borderColor: CHART_COLORS.warning,
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        yAxisID: 'y1',
                        type: 'line',
                        borderDash: [5, 5]
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: 'Number of Cases' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: 'Positivity Rate' },
                        min: 0,
                        max: 1,
                        grid: { drawOnChartArea: false },
                        ticks: {
                            callback: function(value) {
                                return (value * 100) + '%';
                            }
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Malaria Surveillance'
                    },
                    annotation: {
                        annotations: {
                            line1: {
                                type: 'line',
                                yMin: 0.1,
                                yMax: 0.1,
                                borderColor: CHART_COLORS.warning,
                                borderWidth: 2,
                                borderDash: [6, 6],
                                label: {
                                    content: 'Warning (10%)',
                                    enabled: true,
                                    position: 'end'
                                }
                            },
                            line2: {
                                type: 'line',
                                yMin: 0.2,
                                yMax: 0.2,
                                borderColor: CHART_COLORS.danger,
                                borderWidth: 2,
                                borderDash: [6, 6],
                                label: {
                                    content: 'Critical (20%)',
                                    enabled: true,
                                    position: 'end'
                                }
                            }
                        }
                    }
                }
            }
        });
        
        this.charts[chartId] = chart;
    },
    
    // ============================================================================
    // MATERNAL HEALTH CHARTS
    // ============================================================================
    
    initMaternalCharts() {
        document.querySelectorAll('[data-chart="maternal"]').forEach(element => {
            const facilityId = element.dataset.facility;
            
            this.loadMaternalData(element.id, facilityId);
        });
    },
    
    loadMaternalData(chartId, facilityId) {
        const url = `/api/maternal/${facilityId}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.createMaternalChart(chartId, data);
            })
            .catch(error => {
                console.error('Failed to load maternal data:', error);
            });
    },
    
    createMaternalChart(chartId, data) {
        const chartData = {
            labels: data.weeks,
            datasets: [
                {
                    label: 'Deliveries',
                    data: data.deliveries,
                    backgroundColor: CHART_COLORS.maternal,
                    stack: 'maternal'
                },
                {
                    label: 'ANC',
                    data: data.anc,
                    backgroundColor: '#5D9B9B',
                    stack: 'maternal'
                },
                {
                    label: 'PNC',
                    data: data.pnc,
                    backgroundColor: '#B5C9C9',
                    stack: 'maternal'
                },
                {
                    label: 'FP',
                    data: data.fp,
                    backgroundColor: '#E6B89C',
                    stack: 'maternal'
                }
            ]
        };
        
        const options = {
            scales: {
                y: {
                    beginAtZero: true,
                    stacked: true,
                    title: { display: true, text: 'Number of Clients' }
                },
                x: {
                    stacked: true
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Maternal Health Services'
                },
                tooltip: {
                    callbacks: {
                        footer: (items) => {
                            const total = items.reduce((sum, item) => sum + item.raw, 0);
                            return `Total: ${total}`;
                        }
                    }
                }
            }
        };
        
        this.create(chartId, 'bar', chartData, options);
    },
    
    // ============================================================================
    // PERFORMANCE RADAR CHART
    // ============================================================================
    
    createPerformanceRadar(chartId, data) {
        const chartData = {
            labels: data.metrics,
            datasets: [{
                label: 'Performance',
                data: data.values,
                backgroundColor: 'rgba(46, 134, 171, 0.2)',
                borderColor: CHART_COLORS.primary,
                pointBackgroundColor: CHART_COLORS.primary,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: CHART_COLORS.primary
            }]
        };
        
        const options = {
            scales: {
                r: {
                    beginAtZero: true,
                    max: 1,
                    ticks: {
                        stepSize: 0.2,
                        callback: (value) => (value * 100) + '%'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Performance Indicators'
                }
            }
        };
        
        this.create(chartId, 'radar', chartData, options);
    },
    
    // ============================================================================
    // PIE/DOUGHNUT CHARTS
    // ============================================================================
    
    createPieChart(chartId, data) {
        const chartData = {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    CHART_COLORS.primary,
                    CHART_COLORS.secondary,
                    CHART_COLORS.success,
                    CHART_COLORS.warning,
                    CHART_COLORS.danger,
                    CHART_COLORS.info
                ],
                borderWidth: 1
            }]
        };
        
        const options = {
            plugins: {
                title: {
                    display: true,
                    text: data.title || 'Distribution'
                },
                legend: {
                    position: 'right'
                }
            }
        };
        
        this.create(chartId, 'pie', chartData, options);
    },
    
    // ============================================================================
    // HEATMAP (using Plotly)
    // ============================================================================
    
    createHeatmap(elementId, data) {
        const trace = {
            z: data.matrix,
            x: data.columns,
            y: data.rows,
            type: 'heatmap',
            colorscale: 'YlGnBu',
            hoverongaps: false
        };
        
        const layout = {
            title: data.title || 'Activity Heatmap',
            xaxis: { title: 'Hour of Day' },
            yaxis: { title: 'Day of Week' },
            width: 800,
            height: 400
        };
        
        Plotly.newPlot(elementId, [trace], layout);
    },
    
    // ============================================================================
    // GAUGE CHART
    // ============================================================================
    
    createGaugeChart(elementId, value, max, title) {
        const data = [{
            type: "indicator",
            mode: "gauge+number",
            value: value,
            title: { text: title },
            gauge: {
                axis: { range: [null, max] },
                bar: { color: CHART_COLORS.primary },
                steps: [
                    { range: [0, max * 0.5], color: CHART_COLORS.success },
                    { range: [max * 0.5, max * 0.8], color: CHART_COLORS.warning },
                    { range: [max * 0.8, max], color: CHART_COLORS.danger }
                ],
                threshold: {
                    line: { color: "red", width: 4 },
                    thickness: 0.75,
                    value: max
                }
            }
        }];
        
        const layout = {
            width: 300,
            height: 250,
            margin: { t: 25, r: 25, l: 25, b: 25 }
        };
        
        Plotly.newPlot(elementId, data, layout);
    }
};

window.HealthCharts = HealthCharts;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    HealthCharts.init();
});
