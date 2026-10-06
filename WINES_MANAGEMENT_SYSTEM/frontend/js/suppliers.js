/**
 * Wines Management System - Suppliers Page Controller
 * Handles supplier CRUD, search, CSV import, and CSV export.
 */

let currentSuppliers = [];
let deleteTargetSupplierId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadSuppliers();

    // Search
    const searchInput = document.getElementById('supplierSearchInput');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(loadSuppliers, 300);
        });
    }

    // Form
    const form = document.getElementById('supplierForm');
    if (form) {
        form.addEventListener('submit', handleSupplierFormSubmit);
    }

    // CSV Form
    const csvForm = document.getElementById('supplierCsvForm');
    if (csvForm) {
        csvForm.addEventListener('submit', handleSupplierCsvUpload);
    }

    // Confirm Delete
    const confirmDeleteBtn = document.getElementById('confirmDeleteSupplierBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', executeDeleteSupplier);
    }
});

// Fetch Suppliers from Backend
async function loadSuppliers() {
    const search = document.getElementById('supplierSearchInput')?.value.trim() || '';
    const tbody = document.getElementById('suppliersTableBody');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading suppliers from database...</td></tr>`;

    try {
        const params = new URLSearchParams();
        if (search) params.append('search', search);

        const res = await fetch(`${API_BASE}/api/suppliers?${params.toString()}`);
        if (!res.ok) throw new Error('Failed to load suppliers.');

        currentSuppliers = await res.json();
        renderSuppliersTable(currentSuppliers);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Error loading suppliers: ${err.message}</td></tr>`;
        showToast(err.message, 'error');
    }
}

// Render Table
function renderSuppliersTable(suppliers) {
    const tbody = document.getElementById('suppliersTableBody');
    const badge = document.getElementById('supplierCountBadge');
    if (badge) badge.innerText = `${suppliers.length} Vineyards & Distributors`;

    if (!suppliers.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No suppliers found.</td></tr>`;
        return;
    }

    tbody.innerHTML = suppliers.map(s => `
        <tr>
            <td class="fw-semibold text-muted">#${s.supplier_id}</td>
            <td class="fw-bold" style="color: var(--wine-dark);">${s.supplier_name}</td>
            <td>${s.phone || 'N/A'}</td>
            <td><a href="mailto:${s.email}" class="text-decoration-none">${s.email || 'N/A'}</a></td>
            <td class="text-truncate" style="max-width: 220px;">${s.address || 'N/A'}</td>
            <td>
                <span class="badge" style="background-color: var(--wine-subtle); color: var(--wine-primary); font-weight: 600;">
                    ${s.wine_count || 0} Wines Supplied
                </span>
            </td>
            <td>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-wine" onclick="openEditSupplierModal(${s.supplier_id})">
                        <i class="bi bi-pencil-square"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmDeleteSupplier(${s.supplier_id}, '${escapeQuote(s.supplier_name)}')">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Open Add Modal
function openAddSupplierModal() {
    document.getElementById('supplierModalTitle').innerText = 'Add New Supplier';
    document.getElementById('supplierForm').reset();
    document.getElementById('supplierEditId').value = '';
    const modal = new bootstrap.Modal(document.getElementById('supplierModal'));
    modal.show();
}

// Open Edit Modal
function openEditSupplierModal(supplierId) {
    const s = currentSuppliers.find(x => x.supplier_id === supplierId);
    if (!s) return;

    document.getElementById('supplierModalTitle').innerText = 'Edit Supplier Details';
    document.getElementById('supplierEditId').value = s.supplier_id;
    document.getElementById('supplierNameInput').value = s.supplier_name;
    document.getElementById('supplierPhoneInput').value = s.phone || '';
    document.getElementById('supplierEmailInput').value = s.email || '';
    document.getElementById('supplierAddressInput').value = s.address || '';

    const modal = new bootstrap.Modal(document.getElementById('supplierModal'));
    modal.show();
}

// Handle Form Submission
async function handleSupplierFormSubmit(e) {
    e.preventDefault();
    const editId = document.getElementById('supplierEditId').value;
    const isEdit = !!editId;

    const payload = {
        supplier_name: document.getElementById('supplierNameInput').value.trim(),
        phone: document.getElementById('supplierPhoneInput').value.trim() || null,
        email: document.getElementById('supplierEmailInput').value.trim() || null,
        address: document.getElementById('supplierAddressInput').value.trim() || null
    };

    try {
        const url = isEdit ? `${API_BASE}/api/suppliers/${editId}` : `${API_BASE}/api/suppliers`;
        const method = isEdit ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || data.message || 'Operation failed.');

        showToast(isEdit ? 'Supplier updated successfully.' : 'Supplier added successfully.', 'success');
        bootstrap.Modal.getInstance(document.getElementById('supplierModal')).hide();
        loadSuppliers();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// Delete Supplier Flow
function confirmDeleteSupplier(id, name) {
    deleteTargetSupplierId = id;
    document.getElementById('deleteSupplierTargetName').innerText = name;
    const modal = new bootstrap.Modal(document.getElementById('deleteSupplierModal'));
    modal.show();
}

async function executeDeleteSupplier() {
    if (!deleteTargetSupplierId) return;

    try {
        const res = await fetch(`${API_BASE}/api/suppliers/${deleteTargetSupplierId}`, {
            method: 'DELETE'
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Delete operation failed.');

        showToast('Supplier deleted successfully.', 'success');
        bootstrap.Modal.getInstance(document.getElementById('deleteSupplierModal')).hide();
        deleteTargetSupplierId = null;
        loadSuppliers();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// CSV Batch Import
async function handleSupplierCsvUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById('supplierCsvFile');
    if (!fileInput.files.length) {
        showToast('Please select a supplier CSV file.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const resultBox = document.getElementById('supplierCsvResult');
    resultBox.innerHTML = `<div class="text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Validating and inserting supplier records...</div>`;

    try {
        const res = await fetch(`${API_BASE}/api/suppliers/import`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.success) {
            resultBox.innerHTML = `
                <div class="alert alert-success mt-3 py-2">
                    <i class="bi bi-check-circle-fill me-1"></i>
                    Imported <strong>${data.inserted}</strong> suppliers! Failed: <strong>${data.failed}</strong>.
                    ${data.errors.length ? `<div class="mt-2 small text-danger">${data.errors.join('<br>')}</div>` : ''}
                </div>
            `;
            showToast(`Supplier import complete: ${data.inserted} inserted.`, 'success');
            loadSuppliers();
        } else {
            resultBox.innerHTML = `<div class="alert alert-danger mt-3 py-2">${data.errors.join('<br>')}</div>`;
        }
    } catch (err) {
        resultBox.innerHTML = `<div class="alert alert-danger mt-3 py-2">Import failed: ${err.message}</div>`;
    }
}

// Export CSV
function downloadSuppliersCsv() {
    window.location.href = `${API_BASE}/api/suppliers/export/csv`;
}

function escapeQuote(str) {
    return (str || '').replace(/'/g, "\\'");
}
