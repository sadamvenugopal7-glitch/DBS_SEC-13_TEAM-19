/**
 * Wines Management System - Dashboard Controller
 * Real-time relational database analytics, KPI calculations,
 * dynamic Chart.js charts, and live database feeds.
 */

let categoryChartInstance = null;
let topWinesChartInstance = null;
let stockStatusChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
});

async function initDashboard() {
    await checkDatabaseHealth();
    await loadDashboardData();
}

async function checkDatabaseHealth() {
    try {
        const res = await fetch(`${API_BASE}/api/health`);
        const data = await res.json();
        const badge = document.getElementById('dbConnectionStatus');
        if (badge) {
            badge.innerText = `${data.database} (${data.engine})`;
        }
    } catch (e) {
        console.warn("Health check error:", e);
    }
}

async function loadDashboardData() {
    try {
        const res = await fetch(`${API_BASE}/api/dashboard`);
        if (!res.ok) throw new Error('Failed to retrieve dashboard data');
        const data = await res.json();

        // 1. Update KPI Values
        document.getElementById('kpiTotalWines').innerText = (data.total_wines || 0).toLocaleString();
        document.getElementById('kpiTotalCustomers').innerText = (data.total_customers || 0).toLocaleString();
        document.getElementById('kpiTotalSuppliers').innerText = (data.total_suppliers || 0).toLocaleString();
        document.getElementById('kpiTotalOrders').innerText = (data.total_orders || 0).toLocaleString();
        document.getElementById('kpiTotalStock').innerText = (data.total_stock || 0).toLocaleString();
        document.getElementById('kpiLowStock').innerText = (data.low_stock_count || 0).toLocaleString();
        
        const outOfStockEl = document.getElementById('kpiOutOfStock');
        if (outOfStockEl) {
            outOfStockEl.innerText = (data.out_of_stock_count || 0).toLocaleString();
        }

        document.getElementById('kpiTotalSales').innerText = formatCurrency(data.total_sales || 0);

        // 2. Render Charts
        renderCategoryChart(data.category_distribution || []);
        renderTopWinesChart(data.top_selling_wines || []);
        renderStockStatusChart(data.in_stock_count || 0, data.low_stock_count || 0, data.out_of_stock_count || 0);

        // 3. Render Recent Orders Table
        renderRecentOrders(data.recent_orders || []);

        // 4. Fetch and render Low Stock table
        loadLowStockAlerts();

    } catch (err) {
        console.error("Dashboard initialization error:", err);
        showToast('Error loading live dashboard metrics: ' + err.message, 'error');
    }
}

function renderCategoryChart(categories) {
    const ctx = document.getElementById('categoryPieChart');
    if (!ctx) return;

    if (categoryChartInstance) {
        categoryChartInstance.destroy();
    }

    const labels = categories.map(c => c.category);
    const counts = categories.map(c => c.count);

    const winePalette = [
        '#6a1b29', // Deep Burgundy
        '#a33b4d', // Merlot
        '#d4af37', // Gold
        '#800020', // Bordeaux
        '#4a1525', // Cabernet
        '#b8860b', // Dark Goldenrod
        '#343a40'  // Slate Dark
    ];

    categoryChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: winePalette.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        font: { size: 11 }
                    }
                }
            },
            cutout: '65%'
        }
    });
}

function renderTopWinesChart(topWines) {
    const ctx = document.getElementById('topWinesBarChart');
    if (!ctx) return;

    if (topWinesChartInstance) {
        topWinesChartInstance.destroy();
    }

    const labels = topWines.map(w => w.wine_name);
    const data = topWines.map(w => w.total_sold);

    topWinesChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Bottles Sold',
                data: data,
                backgroundColor: '#6a1b29',
                borderRadius: 6,
                maxBarThickness: 32
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { precision: 0 }
                },
                y: {
                    ticks: {
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function renderStockStatusChart(inStock, lowStock, outOfStock) {
    const ctx = document.getElementById('stockStatusBarChart');
    if (!ctx) return;

    if (stockStatusChartInstance) {
        stockStatusChartInstance.destroy();
    }

    stockStatusChartInstance = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['In Stock', 'Low Stock', 'Out of Stock'],
            datasets: [{
                data: [inStock, lowStock, outOfStock],
                backgroundColor: ['#28a745', '#ffc107', '#dc3545'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 12, font: { size: 11 } }
                }
            }
        }
    });
}

function renderRecentOrders(orders) {
    const tbody = document.getElementById('dashboardRecentOrdersTable');
    if (!tbody) return;

    if (!orders || !orders.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-muted">No orders recorded yet.</td></tr>`;
        return;
    }

    tbody.innerHTML = orders.map(o => `
        <tr>
            <td class="fw-semibold text-muted">#${o.order_id}</td>
            <td class="fw-bold" style="color: var(--wine-dark);">${o.customer_name}</td>
            <td>${formatDateTime(o.order_date)}</td>
            <td class="fw-bold">${formatCurrency(o.total_amount)}</td>
            <td>
                <span class="badge ${o.payment_status === 'Paid' ? 'badge-paid' : (o.payment_status === 'Pending' ? 'badge-pending' : 'bg-secondary')}">
                    ${o.payment_status}
                </span>
            </td>
            <td>
                <a href="orders.html?id=${o.order_id}" class="btn btn-sm btn-outline-wine">
                    <i class="bi bi-eye"></i> View
                </a>
            </td>
        </tr>
    `).join('');
}

async function loadLowStockAlerts() {
    const tbody = document.getElementById('dashboardLowStockTable');
    if (!tbody) return;

    try {
        const res = await fetch(`${API_BASE}/api/reports/low-stock`);
        const items = await res.json();

        if (!items || !items.length) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-success"><i class="bi bi-check-circle me-1"></i>All items are adequately stocked!</td></tr>`;
            return;
        }

        tbody.innerHTML = items.slice(0, 5).map(item => `
            <tr>
                <td class="fw-semibold small">${item.wine_name}</td>
                <td class="fw-bold text-danger">${item.stock_quantity}</td>
                <td>${item.reorder_level}</td>
                <td><span class="badge badge-low-stock">LOW STOCK</span></td>
            </tr>
        `).join('');
    } catch (e) {
        console.warn("Could not load low stock table:", e);
    }
}
