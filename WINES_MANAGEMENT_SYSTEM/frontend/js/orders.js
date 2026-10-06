/**
 * Wines Management System - Orders Page Controller
 * Handles sales order creation with ACID database transactions,
 * dynamic item additions, auto-price calculation, order details viewing,
 * status filtering, date filtering, and CSV export.
 */

let currentOrders = [];
let availableWinesMap = {}; // wine_id -> { wine_name, price, quantity }
let orderItemsList = []; // Array of { wine_id, quantity, unit_price, line_total }

document.addEventListener('DOMContentLoaded', () => {
    loadOrders();
    loadCustomersDropdown();
    loadWinesDataForOrder();

    // Filters & Search
    const searchInput = document.getElementById('orderSearchInput');
    const statusFilter = document.getElementById('orderStatusFilter');
    const startDate = document.getElementById('orderStartDate');
    const endDate = document.getElementById('orderEndDate');

    if (searchInput) {
        let debounce;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounce);
            debounce = setTimeout(loadOrders, 300);
        });
    }

    if (statusFilter) statusFilter.addEventListener('change', loadOrders);
    if (startDate) startDate.addEventListener('change', loadOrders);
    if (endDate) endDate.addEventListener('change', loadOrders);

    // Create Order Form
    const orderForm = document.getElementById('createOrderForm');
    if (orderForm) {
        orderForm.addEventListener('submit', handleCreateOrderSubmit);
    }
});

// Fetch Orders from Backend
async function loadOrders() {
    const search = document.getElementById('orderSearchInput')?.value.trim() || '';
    const status = document.getElementById('orderStatusFilter')?.value || 'All';
    const startDate = document.getElementById('orderStartDate')?.value || '';
    const endDate = document.getElementById('orderEndDate')?.value || '';

    const tbody = document.getElementById('ordersTableBody');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading sales orders...</td></tr>`;

    try {
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (status && status !== 'All') params.append('payment_status', status);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);

        const res = await fetch(`${API_BASE}/api/orders?${params.toString()}`);
        if (!res.ok) throw new Error('Failed to load orders.');

        currentOrders = await res.json();
        renderOrdersTable(currentOrders);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Error loading orders: ${err.message}</td></tr>`;
        showToast(err.message, 'error');
    }
}

// Render Orders Table
function renderOrdersTable(orders) {
    const tbody = document.getElementById('ordersTableBody');
    const badge = document.getElementById('ordersCountBadge');
    if (badge) badge.innerText = `${orders.length} Orders Placed`;

    if (!orders.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No orders found matching filters.</td></tr>`;
        return;
    }

    tbody.innerHTML = orders.map(o => `
        <tr>
            <td class="fw-semibold text-muted">#${o.order_id}</td>
            <td class="fw-bold" style="color: var(--wine-dark);">${o.customer_name}</td>
            <td>${formatDateTime(o.order_date)}</td>
            <td><span class="badge" style="background-color: var(--wine-subtle); color: var(--wine-primary);">${o.items_count} items</span></td>
            <td class="fw-bold fs-6">${formatCurrency(o.total_amount)}</td>
            <td>
                <span class="badge ${o.payment_status === 'Paid' ? 'badge-paid' : 'badge-pending'}">
                    ${o.payment_status}
                </span>
            </td>
            <td>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-wine" onclick="viewOrderDetails(${o.order_id})">
                        <i class="bi bi-eye"></i> Details
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteOrder(${o.order_id})">
                        <i class="bi bi-trash"></i> Cancel
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Fetch Customers for Order Form
async function loadCustomersDropdown() {
    const select = document.getElementById('orderCustomerSelect');
    if (!select) return;

    try {
        const res = await fetch(`${API_BASE}/api/customers?limit=300`);
        if (!res.ok) return;
        const customers = await res.json();
        select.innerHTML = '<option value="">-- Select Customer --</option>' +
            customers.map(c => `<option value="${c.customer_id}">#${c.customer_id} - ${c.customer_name} (${c.phone || c.email})</option>`).join('');
    } catch (e) {
        console.warn('Could not load customers for orders', e);
    }
}

// Fetch Wines for Order Creation
async function loadWinesDataForOrder() {
    try {
        const res = await fetch(`${API_BASE}/api/wines?limit=500`);
        if (!res.ok) return;
        const wines = await res.json();
        availableWinesMap = {};
        wines.forEach(w => {
            availableWinesMap[w.wine_id] = {
                name: w.wine_name,
                category: w.category,
                price: parseFloat(w.price),
                stock: w.quantity
            };
        });
    } catch (e) {
        console.warn('Could not load wines catalog for order items', e);
    }
}

// Open Create Order Modal
function openCreateOrderModal() {
    document.getElementById('createOrderForm').reset();
    orderItemsList = [];
    renderOrderItemsList();
    addOrderItemRow(); // add initial item row
    const modal = new bootstrap.Modal(document.getElementById('createOrderModal'));
    modal.show();
}

// Dynamic Line Items in Create Order Modal
function addOrderItemRow() {
    orderItemsList.push({ wine_id: null, quantity: 1, unit_price: 0, line_total: 0 });
    renderOrderItemsList();
}

function removeOrderItemRow(index) {
    if (orderItemsList.length <= 1) {
        showToast('Order must contain at least one item.', 'error');
        return;
    }
    orderItemsList.splice(index, 1);
    renderOrderItemsList();
}

function onWineSelected(index, selectElem) {
    const wineId = parseInt(selectElem.value, 10);
    if (!wineId || !availableWinesMap[wineId]) {
        orderItemsList[index].wine_id = null;
        orderItemsList[index].unit_price = 0;
        orderItemsList[index].line_total = 0;
    } else {
        const wine = availableWinesMap[wineId];
        orderItemsList[index].wine_id = wineId;
        orderItemsList[index].unit_price = wine.price;
        orderItemsList[index].line_total = wine.price * orderItemsList[index].quantity;
    }
    renderOrderItemsList();
}

function onQuantityChanged(index, qtyElem) {
    let qty = parseInt(qtyElem.value, 10);
    if (isNaN(qty) || qty < 1) qty = 1;
    orderItemsList[index].quantity = qty;
    orderItemsList[index].line_total = orderItemsList[index].unit_price * qty;
    renderOrderItemsList();
}

function renderOrderItemsList() {
    const container = document.getElementById('orderItemsContainer');
    if (!container) return;

    let grandTotal = 0;

    const html = orderItemsList.map((item, idx) => {
        grandTotal += item.line_total || 0;
        const wineOptions = Object.keys(availableWinesMap).map(id => {
            const w = availableWinesMap[id];
            const isSelected = item.wine_id == id ? 'selected' : '';
            return `<option value="${id}" ${isSelected}>${w.name} - ${formatCurrency(w.price)} (Stock: ${w.stock})</option>`;
        }).join('');

        return `
            <div class="row g-2 align-items-center mb-2 p-2 border rounded bg-light">
                <div class="col-md-5">
                    <label class="form-label small text-muted mb-1">Select Wine Product</label>
                    <select class="form-select form-select-sm" onchange="onWineSelected(${idx}, this)" required>
                        <option value="">-- Choose Wine --</option>
                        ${wineOptions}
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label small text-muted mb-1">Quantity</label>
                    <input type="number" min="1" class="form-control form-select-sm" value="${item.quantity}" oninput="onQuantityChanged(${idx}, this)" required>
                </div>
                <div class="col-md-2">
                    <label class="form-label small text-muted mb-1">Unit Price</label>
                    <div class="fw-semibold text-muted pt-1">${formatCurrency(item.unit_price)}</div>
                </div>
                <div class="col-md-2">
                    <label class="form-label small text-muted mb-1">Subtotal</label>
                    <div class="fw-bold text-wine pt-1" style="color: var(--wine-primary);">${formatCurrency(item.line_total)}</div>
                </div>
                <div class="col-md-1 text-end">
                    <label class="form-label small text-muted mb-1 d-block">&nbsp;</label>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeOrderItemRow(${idx})">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
    const totalElem = document.getElementById('orderGrandTotalDisplay');
    if (totalElem) totalElem.innerText = formatCurrency(grandTotal);
}

// Handle Order Creation (ACID Transaction)
async function handleCreateOrderSubmit(e) {
    e.preventDefault();

    const customerId = parseInt(document.getElementById('orderCustomerSelect').value, 10);
    const paymentStatus = document.getElementById('orderPaymentStatus').value;

    if (!customerId) {
        showToast('Please select a customer.', 'error');
        return;
    }

    const items = orderItemsList
        .filter(i => i.wine_id && i.quantity > 0)
        .map(i => ({ wine_id: i.wine_id, quantity: i.quantity }));

    if (!items.length) {
        showToast('Please add at least one valid wine item with quantity.', 'error');
        return;
    }

    try {
        const payload = {
            customer_id: customerId,
            payment_status: paymentStatus,
            items: items
        };

        const res = await fetch(`${API_BASE}/api/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || data.message || 'Transaction failed.');

        showToast(`Order #${data.order_id} created successfully within ACID Transaction!`, 'success');
        bootstrap.Modal.getInstance(document.getElementById('createOrderModal')).hide();
        loadOrders();
        loadWinesDataForOrder(); // refresh stock numbers
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// View Order Details Modal
async function viewOrderDetails(orderId) {
    try {
        const res = await fetch(`${API_BASE}/api/orders/${orderId}`);
        if (!res.ok) throw new Error('Could not fetch order details.');

        const order = await res.json();

        document.getElementById('viewOrderIdBadge').innerText = `#${order.order_id}`;
        document.getElementById('viewOrderCustomer').innerText = order.customer_name;
        document.getElementById('viewOrderPhone').innerText = order.customer_phone || 'N/A';
        document.getElementById('viewOrderEmail').innerText = order.customer_email || 'N/A';
        document.getElementById('viewOrderAddress').innerText = order.customer_address || 'N/A';
        document.getElementById('viewOrderDate').innerText = formatDateTime(order.order_date);
        document.getElementById('viewOrderStatus').innerText = order.payment_status;
        document.getElementById('viewOrderTotal').innerText = formatCurrency(order.total_amount);

        const tbody = document.getElementById('viewOrderItemsTable');
        tbody.innerHTML = order.items.map(item => `
            <tr>
                <td class="fw-semibold text-muted">#${item.wine_id}</td>
                <td class="fw-bold" style="color: var(--wine-dark);">${item.wine_name}</td>
                <td><span class="badge" style="background-color: var(--wine-subtle); color: var(--wine-primary);">${item.category}</span></td>
                <td>${item.quantity}</td>
                <td>${formatCurrency(item.unit_price)}</td>
                <td class="fw-bold text-end" style="color: var(--wine-primary);">${formatCurrency(item.line_total)}</td>
            </tr>
        `).join('');

        const modal = new bootstrap.Modal(document.getElementById('viewOrderModal'));
        modal.show();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// Delete Order Flow
async function deleteOrder(orderId) {
    if (!confirm(`Are you sure you want to cancel Order #${orderId}? This will automatically restore the ordered wine quantities back to inventory.`)) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/orders/${orderId}`, {
            method: 'DELETE'
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Delete failed.');

        showToast('Order cancelled and inventory restored.', 'success');
        loadOrders();
        loadWinesDataForOrder();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// Export Orders CSV
function downloadOrdersCsv() {
    window.location.href = `${API_BASE}/api/orders/export/csv`;
}
