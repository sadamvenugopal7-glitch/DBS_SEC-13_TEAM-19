/**
 * Wines Management System - Customers Page Controller
 * Handles customer CRUD, order dependency checks on delete, CSV import, and CSV export.
 */

let currentCustomers = [];
let deleteTargetCustomerId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadCustomers();

    // Search
    const searchInput = document.getElementById('customerSearchInput');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(loadCustomers, 300);
        });
    }

    // Customer Form Submit
    const customerForm = document.getElementById('customerForm');
    if (customerForm) {
        customerForm.addEventListener('submit', handleCustomerFormSubmit);
    }

    // CSV Import Form
    const csvForm = document.getElementById('customerCsvForm');
    if (csvForm) {
        csvForm.addEventListener('submit', handleCustomerCsvUpload);
    }

    // Confirm Delete
    const confirmDeleteBtn = document.getElementById('confirmDeleteCustomerBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', executeDeleteCustomer);
    }
});

// Fetch Customers from Backend
async function loadCustomers() {
    const search = document.getElementById('customerSearchInput')?.value.trim() || '';
    const tbody = document.getElementById('customersTableBody');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading customers from database...</td></tr>`;

    try {
        const params = new URLSearchParams();
        if (search) params.append('search', search);

        const res = await fetch(`${API_BASE}/api/customers?${params.toString()}`);
        if (!res.ok) throw new Error('Failed to load customers.');

        currentCustomers = await res.json();
        renderCustomersTable(currentCustomers);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Error loading customers: ${err.message}</td></tr>`;
        showToast(err.message, 'error');
    }
}

// Render Table
function renderCustomersTable(customers) {
    const tbody = document.getElementById('customersTableBody');
    const badge = document.getElementById('customerCountBadge');
    if (badge) badge.innerText = `${customers.length} Registered`;

    if (!customers.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No customers found.</td></tr>`;
        return;
    }

    tbody.innerHTML = customers.map(c => `
        <tr>
            <td class="fw-semibold text-muted">#${c.customer_id}</td>
            <td class="fw-bold" style="color: var(--wine-dark);">${c.customer_name}</td>
            <td>${c.phone || 'N/A'}</td>
            <td><a href="mailto:${c.email}" class="text-decoration-none">${c.email || 'N/A'}</a></td>
            <td class="text-truncate" style="max-width: 200px;">${c.address || 'N/A'}</td>
            <td>
                <span class="badge" style="background: rgba(106, 27, 41, 0.08); color: var(--wine-primary); font-weight: 600;">
                    ${c.total_orders || 0} orders (${formatCurrency(c.total_spent || 0)})
                </span>
            </td>
            <td>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-wine" onclick="openEditCustomerModal(${c.customer_id})">
                        <i class="bi bi-pencil-square"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmDeleteCustomer(${c.customer_id}, '${escapeQuote(c.customer_name)}', ${c.total_orders || 0})">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Open Add Modal
function openAddCustomerModal() {
    document.getElementById('customerModalTitle').innerText = 'Add New Customer';
    document.getElementById('customerForm').reset();
    document.getElementById('customerEditId').value = '';
    const modal = new bootstrap.Modal(document.getElementById('customerModal'));
    modal.show();
}

// Open Edit Modal
function openEditCustomerModal(customerId) {
    const cust = currentCustomers.find(c => c.customer_id === customerId);
    if (!cust) return;

    document.getElementById('customerModalTitle').innerText = 'Edit Customer Profile';
    document.getElementById('customerEditId').value = cust.customer_id;
    document.getElementById('customerNameInput').value = cust.customer_name;
    document.getElementById('customerPhoneInput').value = cust.phone || '';
    document.getElementById('customerEmailInput').value = cust.email || '';
    document.getElementById('customerAddressInput').value = cust.address || '';

    const modal = new bootstrap.Modal(document.getElementById('customerModal'));
    modal.show();
}

// Handle Form Submission
async function handleCustomerFormSubmit(e) {
    e.preventDefault();
    const editId = document.getElementById('customerEditId').value;
    const isEdit = !!editId;

    const payload = {
        customer_name: document.getElementById('customerNameInput').value.trim(),
        phone: document.getElementById('customerPhoneInput').value.trim() || null,
        email: document.getElementById('customerEmailInput').value.trim() || null,
        address: document.getElementById('customerAddressInput').value.trim() || null
    };

    try {
        const url = isEdit ? `${API_BASE}/api/customers/${editId}` : `${API_BASE}/api/customers`;
        const method = isEdit ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || data.message || 'Operation failed.');

        showToast(isEdit ? 'Customer updated successfully.' : 'Customer added successfully.', 'success');
        bootstrap.Modal.getInstance(document.getElementById('customerModal')).hide();
        loadCustomers();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// Delete Customer Verification
function confirmDeleteCustomer(id, name, orderCount) {
    deleteTargetCustomerId = id;
    document.getElementById('deleteCustomerTargetName').innerText = name;
    
    const warningAlert = document.getElementById('deleteCustomerOrderWarning');
    const deleteBtn = document.getElementById('confirmDeleteCustomerBtn');

    if (orderCount > 0) {
        warningAlert.classList.remove('d-none');
        warningAlert.innerText = 'This customer has existing orders and cannot be deleted directly.';
        deleteBtn.disabled = true;
    } else {
        warningAlert.classList.add('d-none');
        deleteBtn.disabled = false;
    }

    const modal = new bootstrap.Modal(document.getElementById('deleteCustomerModal'));
    modal.show();
}

async function executeDeleteCustomer() {
    if (!deleteTargetCustomerId) return;

    try {
        const res = await fetch(`${API_BASE}/api/customers/${deleteTargetCustomerId}`, {
            method: 'DELETE'
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Delete operation failed.');

        showToast('Customer deleted successfully.', 'success');
        bootstrap.Modal.getInstance(document.getElementById('deleteCustomerModal')).hide();
        deleteTargetCustomerId = null;
        loadCustomers();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// CSV Batch Import
async function handleCustomerCsvUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById('customerCsvFile');
    if (!fileInput.files.length) {
        showToast('Please select a customer CSV file.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const resultBox = document.getElementById('customerCsvResult');
    resultBox.innerHTML = `<div class="text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Validating and inserting customer records...</div>`;

    try {
        const res = await fetch(`${API_BASE}/api/customers/import`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.success) {
            resultBox.innerHTML = `
                <div class="alert alert-success mt-3 py-2">
                    <i class="bi bi-check-circle-fill me-1"></i>
                    Imported <strong>${data.inserted}</strong> customers! Failed: <strong>${data.failed}</strong>.
                    ${data.errors.length ? `<div class="mt-2 small text-danger">${data.errors.join('<br>')}</div>` : ''}
                </div>
            `;
            showToast(`Customer import complete: ${data.inserted} inserted.`, 'success');
            loadCustomers();
        } else {
            resultBox.innerHTML = `<div class="alert alert-danger mt-3 py-2">${data.errors.join('<br>')}</div>`;
        }
    } catch (err) {
        resultBox.innerHTML = `<div class="alert alert-danger mt-3 py-2">Import failed: ${err.message}</div>`;
    }
}

// Export CSV
function downloadCustomersCsv() {
    window.location.href = `${API_BASE}/api/customers/export/csv`;
}

function escapeQuote(str) {
    return (str || '').replace(/'/g, "\\'");
}
