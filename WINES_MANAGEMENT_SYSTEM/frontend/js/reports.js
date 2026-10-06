/**
 * Wines Management System - Reports Page Controller
 * Handles 10 academic DBMS reports, live SQL aggregation queries,
 * dynamic table header and row rendering, client search, and CSV streaming downloads.
 */

let activeReport = 'available-stock';
let currentReportData = [];

const REPORT_CONFIG = {
    'available-stock': {
        title: 'Available Stock Report',
        url: '/api/reports/available-stock',
        headers: ['Wine ID', 'Wine Label', 'Category', 'Unit Price', 'In Stock', 'Reorder Level', 'Supplier', 'Last Updated'],
        renderRow: (r) => `
            <tr>
                <td class="text-muted">#${r.wine_id}</td>
                <td class="fw-bold" style="color: var(--wine-dark);">${r.wine_name}</td>
                <td><span class="badge bg-light text-dark border">${r.category}</span></td>
                <td>${formatCurrency(r.price)}</td>
                <td class="fw-bold text-success">${r.stock_quantity}</td>
                <td>${r.reorder_level}</td>
                <td>${r.supplier_name}</td>
                <td class="small text-muted">${formatDateTime(r.last_updated)}</td>
            </tr>
        `
    },
    'low-stock': {
        title: 'Low Stock Products (Reorder Warning)',
        url: '/api/reports/low-stock',
        headers: ['Wine ID', 'Wine Label', 'Category', 'Stock Qty', 'Reorder Level', 'Unit Price', 'Supplier', 'Supplier Phone'],
        renderRow: (r) => `
            <tr>
                <td class="text-muted">#${r.wine_id}</td>
                <td class="fw-bold text-danger">${r.wine_name}</td>
                <td><span class="badge bg-light text-dark border">${r.category}</span></td>
                <td class="fw-bold text-danger fs-6">${r.stock_quantity}</td>
                <td>${r.reorder_level}</td>
                <td>${formatCurrency(r.price)}</td>
                <td>${r.supplier_name}</td>
                <td>${r.supplier_phone || 'N/A'}</td>
            </tr>
        `
    },
    'out-of-stock': {
        title: 'Out of Stock Products (Critical)',
        url: '/api/reports/out-of-stock',
        headers: ['Wine ID', 'Wine Label', 'Category', 'Stock Qty', 'Reorder Level', 'Unit Price', 'Supplier', 'Contact Email'],
        renderRow: (r) => `
            <tr>
                <td class="text-muted">#${r.wine_id}</td>
                <td class="fw-bold text-danger">${r.wine_name}</td>
                <td><span class="badge bg-light text-dark border">${r.category}</span></td>
                <td><span class="badge badge-out-stock">0 (OUT OF STOCK)</span></td>
                <td>${r.reorder_level}</td>
                <td>${formatCurrency(r.price)}</td>
                <td>${r.supplier_name}</td>
                <td><a href="mailto:${r.supplier_email}">${r.supplier_email || 'N/A'}</a></td>
            </tr>
        `
    },
    'customer-history': {
        title: 'Customer Order History',
        url: '/api/reports/customer-history',
        headers: ['Cust ID', 'Customer Name', 'Contact Phone', 'Order ID', 'Order Date', 'Total Amount', 'Payment Status', 'Items'],
        renderRow: (r) => `
            <tr>
                <td class="text-muted">#${r.customer_id}</td>
                <td class="fw-bold" style="color: var(--wine-dark);">${r.customer_name}</td>
                <td>${r.phone || 'N/A'}</td>
                <td class="fw-semibold">#${r.order_id}</td>
                <td>${formatDateTime(r.order_date)}</td>
                <td class="fw-bold">${formatCurrency(r.total_amount)}</td>
                <td><span class="badge ${r.payment_status === 'Paid' ? 'badge-paid' : 'badge-pending'}">${r.payment_status}</span></td>
                <td>${r.items_count}</td>
            </tr>
        `
    },
    'sales': {
        title: 'Total Sales by Payment Status',
        url: '/api/reports/sales',
        headers: ['Payment Status', 'Total Orders Placed', 'Total Gross Revenue', 'Average Order Value (AOV)'],
        renderRow: (r) => `
            <tr>
                <td><span class="badge ${r.payment_status === 'Paid' ? 'badge-paid' : (r.payment_status === 'Pending' ? 'badge-pending' : 'bg-secondary')}">${r.payment_status}</span></td>
                <td class="fw-bold">${r.order_count} orders</td>
                <td class="fw-bold fs-6" style="color: var(--wine-primary);">${formatCurrency(r.total_revenue)}</td>
                <td>${formatCurrency(r.average_order_value)}</td>
            </tr>
        `
    },
    'sales-by-date': {
        title: 'Daily Sales Volume & Revenue',
        url: '/api/reports/sales-by-date',
        headers: ['Sale Date', 'Orders Count', 'Daily Sales Revenue'],
        renderRow: (r) => `
            <tr>
                <td class="fw-bold">${r.sale_date}</td>
                <td>${r.total_orders} orders</td>
                <td class="fw-bold text-success fs-6">${formatCurrency(r.total_sales)}</td>
            </tr>
        `
    },
    'sales-by-wine': {
        title: 'Sales Performance by Wine SKU',
        url: '/api/reports/sales-by-wine',
        headers: ['Wine ID', 'Wine Label', 'Category', 'Bottle Price', 'Total Bottles Sold', 'Total Revenue'],
        renderRow: (r) => `
            <tr>
                <td class="text-muted">#${r.wine_id}</td>
                <td class="fw-bold" style="color: var(--wine-dark);">${r.wine_name}</td>
                <td><span class="badge bg-light text-dark border">${r.category}</span></td>
                <td>${formatCurrency(r.price)}</td>
                <td class="fw-bold">${r.total_units_sold}</td>
                <td class="fw-bold" style="color: var(--wine-primary);">${formatCurrency(r.total_revenue)}</td>
            </tr>
        `
    },
    'sales-by-category': {
        title: 'Sales Revenue by Wine Category',
        url: '/api/reports/sales-by-category',
        headers: ['Wine Category', 'Catalog Varieties', 'Bottles Sold', 'Cumulative Revenue'],
        renderRow: (r) => `
            <tr>
                <td class="fw-bold fs-6" style="color: var(--wine-dark);">${r.category}</td>
                <td>${r.total_wines} SKUs</td>
                <td class="fw-bold">${r.units_sold} units</td>
                <td class="fw-bold fs-6" style="color: var(--wine-primary);">${formatCurrency(r.revenue)}</td>
            </tr>
        `
    },
    'supplier-wines': {
        title: 'Supplier Portfolio & Total Stock Supplied',
        url: '/api/reports/supplier-wines',
        headers: ['Supplier ID', 'Vineyard / Estate Name', 'Contact Phone', 'Corporate Email', 'Wines Offered', 'Total Physical Stock'],
        renderRow: (r) => `
            <tr>
                <td class="text-muted">#${r.supplier_id}</td>
                <td class="fw-bold" style="color: var(--wine-dark);">${r.supplier_name}</td>
                <td>${r.phone || 'N/A'}</td>
                <td><a href="mailto:${r.email}">${r.email || 'N/A'}</a></td>
                <td class="fw-bold">${r.total_wines_supplied} varieties</td>
                <td class="fw-bold text-success">${r.total_stock_supplied} bottles</td>
            </tr>
        `
    },
    'top-wines': {
        title: 'Top 10 Selling Wines (Best Performers)',
        url: '/api/reports/top-wines?limit=10',
        headers: ['Rank', 'Wine Label', 'Category', 'Unit Price', 'Supplier', 'Units Sold', 'Total Sales Value'],
        renderRow: (r, idx) => `
            <tr>
                <td class="fw-bold fs-6 text-muted">#${idx + 1}</td>
                <td class="fw-bold" style="color: var(--wine-dark);">${r.wine_name}</td>
                <td><span class="badge bg-light text-dark border">${r.category}</span></td>
                <td>${formatCurrency(r.price)}</td>
                <td>${r.supplier_name}</td>
                <td class="fw-bold text-danger fs-6">${r.total_quantity_sold} bottles</td>
                <td class="fw-bold" style="color: var(--wine-primary);">${formatCurrency(r.total_sales_value)}</td>
            </tr>
        `
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Report switchers
    const buttons = document.querySelectorAll('.report-tab-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => {
                b.classList.remove('btn-wine', 'active');
                b.classList.add('btn-outline-wine');
            });
            btn.classList.add('btn-wine', 'active');
            btn.classList.remove('btn-outline-wine');

            activeReport = btn.getAttribute('data-report');
            loadReportData(activeReport);
        });
    });

    // Search within report
    const searchInput = document.getElementById('reportSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            filterReportData(searchInput.value.trim().toLowerCase());
        });
    }

    loadReportData(activeReport);
});

async function loadReportData(reportKey) {
    const config = REPORT_CONFIG[reportKey];
    if (!config) return;

    document.getElementById('reportTitleDisplay').innerText = config.title;
    const thead = document.getElementById('reportTableHead');
    const tbody = document.getElementById('reportTableBody');

    // Build thead
    thead.innerHTML = `<tr>${config.headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
    tbody.innerHTML = `<tr><td colspan="${config.headers.length}" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading report from MySQL...</td></tr>`;

    try {
        const res = await fetch(`${API_BASE}${config.url}`);
        if (!res.ok) throw new Error('Failed to load report data.');

        currentReportData = await res.json();
        renderReportRows(currentReportData, config);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="${config.headers.length}" class="text-center text-danger py-4">Error loading report: ${err.message}</td></tr>`;
        showToast(err.message, 'error');
    }
}

function renderReportRows(data, config) {
    const tbody = document.getElementById('reportTableBody');
    const badge = document.getElementById('reportCountBadge');
    if (badge) badge.innerText = `${data.length} Records`;

    if (!data.length) {
        tbody.innerHTML = `<tr><td colspan="${config.headers.length}" class="text-center py-4 text-muted">No data returned for this query.</td></tr>`;
        return;
    }

    tbody.innerHTML = data.map((row, idx) => config.renderRow(row, idx)).join('');
}

function filterReportData(query) {
    const config = REPORT_CONFIG[activeReport];
    if (!config || !currentReportData) return;

    if (!query) {
        renderReportRows(currentReportData, config);
        return;
    }

    const filtered = currentReportData.filter(row => {
        return Object.values(row).some(val => 
            String(val || '').toLowerCase().includes(query)
        );
    });

    renderReportRows(filtered, config);
}

function downloadActiveReportCsv() {
    window.location.href = `${API_BASE}/api/reports/export/${activeReport}`;
}
