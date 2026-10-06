/**
 * Wines Management System - Shared JavaScript Utilities
 * Handles API calls, Toast notifications, formatting, and sidebar interaction.
 */

const API_BASE = window.location.origin;

// Format Currency in INR
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 2
    }).format(amount || 0);
}

// Format Datetime
function formatDateTime(dateStr) {
    if (!dateStr) return 'N/A';
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateStr;
    }
}

// Show Toast Message
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `custom-toast toast-${type}`;
    
    let icon = 'bi-check-circle-fill';
    if (type === 'error') icon = 'bi-exclamation-triangle-fill';
    if (type === 'info') icon = 'bi-info-circle-fill';

    toast.innerHTML = `
        <i class="bi ${icon}" style="font-size: 20px;"></i>
        <div style="flex: 1;">
            <div style="font-weight: 600; font-size: 13.5px;">${type === 'error' ? 'Notice' : 'Success'}</div>
            <div style="font-size: 13px; opacity: 0.95;">${message}</div>
        </div>
        <button type="button" class="btn-close btn-close-white" style="font-size: 11px;" onclick="this.parentElement.remove()"></button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        if (toast && toast.parentElement) {
            toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 400);
        }
    }, 4500);
}

// Mobile Sidebar Toggle
document.addEventListener('DOMContentLoaded', () => {
    const mobileToggle = document.getElementById('mobileNavToggle');
    const sidebar = document.getElementById('sidebar');
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }
});
