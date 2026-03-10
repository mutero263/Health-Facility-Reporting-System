/**
 * HEALTH FACILITY REPORTING SYSTEM - MAIN JAVASCRIPT
 * 
 * Handles:
 * - UI interactions
 * - Form validation
 * - AJAX requests
 * - Notifications
 * - Date pickers
 * - Mobile menu
 */

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

const API_BASE_URL = window.location.origin;
const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

// ============================================================================
// DOM CONTENT LOADED
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Health Facility Reporting System loaded');
    
    // Initialize all components
    initMobileMenu();
    initDatePickers();
    initFormValidation();
    initNotifications();
    initTooltips();
    initDropdowns();
    initTabs();
    initCharts();
    initDataTables();
    initFileUploads();
    initAutoRefresh();
    
    // Load initial data
    loadDashboardData();
});

// ============================================================================
// MOBILE MENU
// ============================================================================

function initMobileMenu() {
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.dashboard-sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (!menuToggle) return;
    
    menuToggle.addEventListener('click', function(e) {
        e.preventDefault();
        sidebar?.classList.toggle('show');
        overlay?.classList.toggle('show');
        document.body.classList.toggle('sidebar-open');
    });
    
    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar?.classList.remove('show');
            overlay.classList.remove('show');
            document.body.classList.remove('sidebar-open');
        });
    }
    
    // Close on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar?.classList.contains('show')) {
            sidebar.classList.remove('show');
            overlay?.classList.remove('show');
            document.body.classList.remove('sidebar-open');
        }
    });
}

// ============================================================================
// DATE PICKERS
// ============================================================================

function initDatePickers() {
    const dateInputs = document.querySelectorAll('.date-picker');
    
    dateInputs.forEach(input => {
        // Simple native date picker for now
        input.type = 'date';
        
        // Set default to today
        if (!input.value) {
            const today = new Date().toISOString().split('T')[0];
            input.value = today;
        }
    });
    
    // Week picker
    const weekPickers = document.querySelectorAll('.week-picker');
    
    weekPickers.forEach(picker => {
        const weekSelect = picker.querySelector('.week-select');
        const yearSelect = picker.querySelector('.year-select');
        const applyBtn = picker.querySelector('.apply-week');
        
        if (!weekSelect || !yearSelect) return;
        
        // Populate weeks (1-53)
        for (let i = 1; i <= 53; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `Week ${i}`;
            weekSelect.appendChild(option);
        }
        
        // Populate years (current year - 5 to current year + 1)
        const currentYear = new Date().getFullYear();
        for (let i = currentYear - 5; i <= currentYear + 1; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = i;
            yearSelect.appendChild(option);
        }
        
        // Set current week and year
        const now = new Date();
        const week = getWeekNumber(now);
        weekSelect.value = week;
        yearSelect.value = currentYear;
        
        if (applyBtn) {
            applyBtn.addEventListener('click', function() {
                const week = weekSelect.value;
                const year = yearSelect.value;
                const event = new CustomEvent('weekchange', { 
                    detail: { week, year } 
                });
                picker.dispatchEvent(event);
            });
        }
    });
}

// Helper: Get week number
function getWeekNumber(date) {
    const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
    const pastDaysOfYear = (date - firstDayOfYear) / 86400000;
    return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
}

// ============================================================================
// FORM VALIDATION
// ============================================================================

function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
    
    // Real-time validation
    const inputs = document.querySelectorAll('.form-control[required]');
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

function validateField(field) {
    const isValid = field.checkValidity();
    
    if (!isValid) {
        field.classList.add('is-invalid');
        
        // Find or create feedback message
        let feedback = field.nextElementSibling;
        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.insertBefore(feedback, field.nextSibling);
        }
        
        feedback.textContent = field.validationMessage;
    } else {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    }
}

// ============================================================================
// NOTIFICATIONS
// ============================================================================

function initNotifications() {
    // Auto-hide notifications after 5 seconds
    const notifications = document.querySelectorAll('.notification:not(.persistent)');
    
    notifications.forEach(notification => {
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in-out';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    });
    
    // Close button
    const closeButtons = document.querySelectorAll('.notification-close');
    
    closeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const notification = this.closest('.notification');
            if (notification) {
                notification.style.animation = 'slideOutRight 0.3s ease-in-out';
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }
        });
    });
}

// Show notification
function showNotification(message, type = 'info', duration = 5000) {
    const container = document.querySelector('.notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-header">
            <strong>${type.toUpperCase()}</strong>
            <button class="notification-close">&times;</button>
        </div>
        <div class="notification-body">
            ${message}
        </div>
    `;
    
    container.appendChild(notification);
    
    // Add close handler
    notification.querySelector('.notification-close').addEventListener('click', function() {
        notification.style.animation = 'slideOutRight 0.3s ease-in-out';
        setTimeout(() => notification.remove(), 300);
    });
    
    // Auto-hide
    if (duration > 0) {
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in-out';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
}

// ============================================================================
// TOOLTIPS
// ============================================================================

function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
        element.addEventListener('mousemove', moveTooltip);
    });
}

function showTooltip(e) {
    const element = e.target;
    const text = element.getAttribute('data-tooltip');
    
    if (!text) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.id = 'current-tooltip';
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('current-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

function moveTooltip(e) {
    const tooltip = document.getElementById('current-tooltip');
    if (tooltip) {
        tooltip.style.left = e.pageX + 'px';
        tooltip.style.top = e.pageY - tooltip.offsetHeight - 10 + 'px';
    }
}

// ============================================================================
// DROPDOWNS
// ============================================================================

function initDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown');
    
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (!toggle || !menu) return;
        
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Close other dropdowns
            dropdowns.forEach(d => {
                if (d !== dropdown) {
                    d.classList.remove('show');
                }
            });
            
            dropdown.classList.toggle('show');
        });
        
        // Close on click outside
        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });
    });
}

// ============================================================================
// TABS
// ============================================================================

function initTabs() {
    const tabContainers = document.querySelectorAll('.tabs');
    
    tabContainers.forEach(container => {
        const tabs = container.querySelectorAll('.tab');
        const panes = container.querySelectorAll('.tab-pane');
        
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Deactivate all tabs
                tabs.forEach(t => t.classList.remove('active'));
                panes.forEach(p => p.classList.remove('active'));
                
                // Activate current tab
                tab.classList.add('active');
                if (panes[index]) {
                    panes[index].classList.add('active');
                }
                
                // Trigger custom event
                const event = new CustomEvent('tabchange', { 
                    detail: { tab: index } 
                });
                container.dispatchEvent(event);
            });
        });
    });
}

// ============================================================================
// CHARTS (delegated to charts.js)
// ============================================================================

function initCharts() {
    // Check if Chart object exists (from charts.js)
    if (typeof window.HealthCharts !== 'undefined') {
        window.HealthCharts.init();
    } else {
        console.warn('Chart library not loaded');
    }
}

// ============================================================================
// DATA TABLES
// ============================================================================

function initDataTables() {
    const tables = document.querySelectorAll('.data-table');
    
    tables.forEach(table => {
        const searchInput = document.querySelector(`#search-${table.id}`);
        const rowsPerPage = document.querySelector(`#rows-${table.id}`);
        
        if (searchInput) {
            searchInput.addEventListener('input', debounce(function() {
                filterTable(table, this.value);
            }, 300));
        }
        
        if (rowsPerPage) {
            rowsPerPage.addEventListener('change', function() {
                changeRowsPerPage(table, this.value);
            });
        }
        
        // Add sorting
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                sortTable(table, this);
            });
            header.style.cursor = 'pointer';
        });
    });
}

function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(term)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function sortTable(table, header) {
    const column = header.cellIndex;
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const isAscending = header.getAttribute('data-order') !== 'asc';
    
    // Update sort indicators
    table.querySelectorAll('th[data-sort]').forEach(th => {
        th.removeAttribute('data-order');
    });
    header.setAttribute('data-order', isAscending ? 'asc' : 'desc');
    
    // Sort rows
    rows.sort((a, b) => {
        const aVal = a.cells[column].textContent.trim();
        const bVal = b.cells[column].textContent.trim();
        
        // Try numeric comparison
        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        // String comparison
        return isAscending 
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
    });
    
    // Reorder DOM
    const tbody = table.querySelector('tbody');
    rows.forEach(row => tbody.appendChild(row));
}

function changeRowsPerPage(table, count) {
    const rows = table.querySelectorAll('tbody tr');
    const pagination = document.querySelector(`#pagination-${table.id}`);
    
    rows.forEach((row, index) => {
        if (index < count) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    
    if (pagination) {
        updatePagination(pagination, Math.ceil(rows.length / count));
    }
}

function updatePagination(container, totalPages) {
    container.innerHTML = '';
    
    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm btn-outline';
        btn.textContent = i;
        btn.addEventListener('click', function() {
            // Handle page change
        });
        container.appendChild(btn);
    }
}

// ============================================================================
// FILE UPLOADS
// ============================================================================

function initFileUploads() {
    const uploaders = document.querySelectorAll('.file-uploader');
    
    uploaders.forEach(uploader => {
        const input = uploader.querySelector('input[type="file"]');
        const dropZone = uploader.querySelector('.drop-zone');
        const preview = uploader.querySelector('.file-preview');
        
        if (!input) return;
        
        // Handle file selection
        input.addEventListener('change', function() {
            handleFiles(this.files, preview);
        });
        
        // Drag and drop
        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('dragover');
            });
            
            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('dragover');
            });
            
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                input.files = files;
                handleFiles(files, preview);
            });
        }
    });
}

function handleFiles(files, preview) {
    if (!preview) return;
    
    preview.innerHTML = '';
    
    Array.from(files).forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        const icon = getFileIcon(file.type);
        const size = formatFileSize(file.size);
        
        fileItem.innerHTML = `
            <span class="file-icon">${icon}</span>
            <span class="file-name">${file.name}</span>
            <span class="file-size">${size}</span>
            <button class="file-remove">&times;</button>
        `;
        
        fileItem.querySelector('.file-remove').addEventListener('click', function() {
            fileItem.remove();
            // Clear input if last file
            if (preview.children.length === 0) {
                const input = preview.closest('.file-uploader').querySelector('input[type="file"]');
                input.value = '';
            }
        });
        
        preview.appendChild(fileItem);
    });
}

function getFileIcon(mimeType) {
    if (mimeType.startsWith('image/')) return '🖼️';
    if (mimeType.startsWith('text/')) return '📄';
    if (mimeType.includes('spreadsheet')) return '📊';
    if (mimeType.includes('pdf')) return '📑';
    return '📁';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ============================================================================
// AUTO REFRESH
// ============================================================================

function initAutoRefresh() {
    const refreshElements = document.querySelectorAll('[data-auto-refresh]');
    
    refreshElements.forEach(element => {
        const interval = element.getAttribute('data-auto-refresh') || 30000; // 30 seconds default
        
        setInterval(() => {
            refreshData(element);
        }, interval);
    });
}

function refreshData(element) {
    const url = element.getAttribute('data-refresh-url');
    if (!url) return;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            updateElementWithData(element, data);
        })
        .catch(error => {
            console.error('Auto-refresh failed:', error);
        });
}

function updateElementWithData(element, data) {
    // Update based on element type
    if (element.classList.contains('metric-value')) {
        element.textContent = data.value;
    } else if (element.classList.contains('chart-container')) {
        // Trigger chart update
        if (window.HealthCharts) {
            window.HealthCharts.update(element.id, data);
        }
    }
}

// ============================================================================
// DASHBOARD DATA LOADING
// ============================================================================

function loadDashboardData() {
    const dashboard = document.querySelector('.dashboard');
    if (!dashboard) return;
    
    const summaryCards = dashboard.querySelectorAll('[data-summary]');
    
    summaryCards.forEach(card => {
        const metric = card.getAttribute('data-summary');
        loadSummaryMetric(card, metric);
    });
}

function loadSummaryMetric(element, metric) {
    const url = `${API_BASE_URL}/api/summary/${metric}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            element.querySelector('.metric-value').textContent = data.value;
            element.querySelector('.metric-change').textContent = data.change;
            
            if (data.trend === 'up') {
                element.querySelector('.metric-change').classList.add('positive');
            } else if (data.trend === 'down') {
                element.querySelector('.metric-change').classList.add('negative');
            }
        })
        .catch(error => {
            console.error('Failed to load summary metric:', error);
        });
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format percentage
function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(value);
}

// Format number with commas
function formatNumber(value) {
    return new Intl.NumberFormat('en-US').format(value);
}

// Parse query string
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    const result = {};
    
    for (const [key, value] of params) {
        result[key] = value;
    }
    
    return result;
}

// Set query parameter
function setQueryParam(key, value) {
    const url = new URL(window.location.href);
    url.searchParams.set(key, value);
    window.history.pushState({}, '', url);
}

// Cookie helpers
function setCookie(name, value, days = 7) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function deleteCookie(name) {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
}

// ============================================================================
// EXPORT FUNCTIONS
// ============================================================================

function exportData(format = 'csv') {
    const url = `${API_BASE_URL}/export?format=${format}`;
    
    fetch(url)
        .then(response => response.blob())
        .then(blob => {
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `export.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
        })
        .catch(error => {
            showNotification('Export failed: ' + error.message, 'danger');
        });
}

// ============================================================================
// PRINT FUNCTIONS
// ============================================================================

function printDashboard() {
    window.print();
}

// ============================================================================
// EXPORT GLOBALS
// ============================================================================

// Make functions available globally
window.HealthSystem = {
    showNotification,
    exportData,
    printDashboard,
    formatCurrency,
    formatPercentage,
    formatNumber,
    getQueryParams,
    setQueryParam,
    setCookie,
    getCookie,
    deleteCookie
};

// ============================================================================
// INITIALIZATION COMPLETE
// ============================================================================

console.log('Health Facility Reporting System initialized');