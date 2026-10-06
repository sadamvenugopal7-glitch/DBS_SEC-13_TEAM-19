/**
 * Wines Management System - Wines Page Controller
 * Handles CRUD operations, category filtering, price/quantity sorting,
 * search queries, CSV imports, and CSV exports via backend REST endpoints.
 */

let currentWines = [];
let deleteTargetId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadWines();
    loadSuppliersDropdown();

    // Search and Filters
    const searchInput = document.getElementById('wineSearchInput');
    const categoryFilter = document.getElementById('wineCategoryFilter');
    const sortBySelect = document.getElementById('wineSortBy');
    const sortOrderSelect = document.getElementById('wineSortOrder');

    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(loadWines, 300);
        });
    }

    if (categoryFilter) categoryFilter.addEventListener('change', loadWines);
    if (sortBySelect) sortBySelect.addEventListener('change', loadWines);
    if (sortOrderSelect) sortOrderSelect.addEventListener('change', loadWines);

    // Add / Edit Form Submit
    const wineForm = document.getElementById('wineForm');
    if (wineForm) {
        wineForm.addEventListener('submit', handleWineFormSubmit);
    }

    // CSV Import Form
    const csvImportForm = document.getElementById('wineCsvForm');
    if (csvImportForm) {
        csvImportForm.addEventListener('submit', handleWineCsvUpload);
    }

    // Confirm Delete Button
    const confirmDeleteBtn = document.getElementById('confirmDeleteWineBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', executeDeleteWine);
    }
});

// Fetch Wines from Backend
async function loadWines() {
    const search = document.getElementById('wineSearchInput')?.value.trim() || '';
    const category = document.getElementById('wineCategoryFilter')?.value || 'All';
    const sortBy = document.getElementById('wineSortBy')?.value || 'wine_id';
    const sortOrder = document.getElementById('wineSortOrder')?.value || 'asc';

    const tbody = document.getElementById('winesTableBody');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading wine catalog from database...</td></tr>`;

    try {
        const params = new URLSearchParams({
            sort_by: sortBy,
            sort_order: sortOrder
        });
        if (search) params.append('search', search);
        if (category && category !== 'All') params.append('category', category);

        const response = await fetch(`${API_BASE}/api/wines?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to load wines.');

        currentWines = await response.json();
        renderWinesTable(currentWines);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Error loading wines: ${err.message}</td></tr>`;
        showToast(err.message, 'error');
    }
}

// Render Table
function renderWinesTable(wines) {
    const tbody = document.getElementById('winesTableBody');
    const countBadge = document.getElementById('wineCountBadge');
    if (countBadge) countBadge.innerText = `${wines.length} Items`;

    if (!wines.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No wines found matching criteria.</td></tr>`;
        return;
    }

    tbody.innerHTML = wines.map(w => `
        <tr>
            <td class="fw-semibold text-muted">#${w.wine_id}</td>
            <td class="fw-bold" style="color: var(--wine-dark);">${w.wine_name}</td>
            <td><span class="badge" style="background-color: var(--wine-subtle); color: var(--wine-primary); border: 1px solid rgba(106, 27, 41, 0.2);">${w.category}</span></td>
            <td class="fw-semibold">${formatCurrency(w.price)}</td>
            <td>
                <span class="badge ${w.quantity <= 10 ? 'badge-low-stock' : 'badge-available'}">
                    ${w.quantity} in stock
                </span>
            </td>
            <td class="text-muted">${w.supplier_name || 'N/A'}</td>
            <td>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-wine" onclick="openEditWineModal(${w.wine_id})">
                        <i class="bi bi-pencil-square"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmDeleteWine(${w.wine_id}, '${escapeQuote(w.wine_name)}')">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Load Suppliers for Dropdown
async function loadSuppliersDropdown() {
    const select = document.getElementById('wineSupplierSelect');
    if (!select) return;

    try {
        const res = await fetch(`${API_BASE}/api/suppliers?limit=300`);
        if (!res.ok) return;
        const suppliers = await res.json();
        select.innerHTML = '<option value="">-- None / Direct Sourcing --</option>' +
            suppliers.map(s => `<option value="${s.supplier_id}">${s.supplier_name}</option>`).join('');
    } catch (e) {
        console.warn('Could not load suppliers dropdown', e);
    }
}

// Open Add Modal
function openAddWineModal() {
    document.getElementById('wineModalTitle').innerText = 'Add New Wine Product';
    document.getElementById('wineForm').reset();
    document.getElementById('wineEditId').value = '';
    const modal = new bootstrap.Modal(document.getElementById('wineModal'));
    modal.show();
}

// Open Edit Modal
function openEditWineModal(wineId) {
    const wine = currentWines.find(w => w.wine_id === wineId);
    if (!wine) return;

    document.getElementById('wineModalTitle').innerText = 'Edit Wine Product';
    document.getElementById('wineEditId').value = wine.wine_id;
    document.getElementById('wineNameInput').value = wine.wine_name;
    document.getElementById('wineCategoryInput').value = wine.category;
    document.getElementById('winePriceInput').value = wine.price;
    document.getElementById('wineQuantityInput').value = wine.quantity;
    document.getElementById('wineSupplierSelect').value = wine.supplier_id || '';

    const modal = new bootstrap.Modal(document.getElementById('wineModal'));
    modal.show();
}

// Handle Form Submission
async function handleWineFormSubmit(e) {
    e.preventDefault();
    const editId = document.getElementById('wineEditId').value;
    const isEdit = !!editId;

    const payload = {
        wine_name: document.getElementById('wineNameInput').value.trim(),
        category: document.getElementById('wineCategoryInput').value,
        price: parseFloat(document.getElementById('winePriceInput').value),
        quantity: parseInt(document.getElementById('wineQuantityInput').value, 10),
        supplier_id: document.getElementById('wineSupplierSelect').value ? parseInt(document.getElementById('wineSupplierSelect').value, 10) : null
    };

    try {
        const url = isEdit ? `${API_BASE}/api/wines/${editId}` : `${API_BASE}/api/wines`;
        const method = isEdit ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || data.message || 'Operation failed.');

        showToast(isEdit ? 'Wine updated successfully.' : 'Wine added successfully.', 'success');
        bootstrap.Modal.getInstance(document.getElementById('wineModal')).hide();
        loadWines();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// Delete Wine Flow
function confirmDeleteWine(id, name) {
    deleteTargetId = id;
    document.getElementById('deleteWineTargetName').innerText = name;
    const modal = new bootstrap.Modal(document.getElementById('deleteWineModal'));
    modal.show();
}

async function executeDeleteWine() {
    if (!deleteTargetId) return;

    try {
        const res = await fetch(`${API_BASE}/api/wines/${deleteTargetId}`, {
            method: 'DELETE'
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Delete operation failed.');

        showToast('Wine deleted successfully.', 'success');
        bootstrap.Modal.getInstance(document.getElementById('deleteWineModal')).hide();
        deleteTargetId = null;
        loadWines();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// CSV Batch Import
async function handleWineCsvUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById('wineCsvFile');
    if (!fileInput.files.length) {
        showToast('Please select a CSV file first.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const resultBox = document.getElementById('wineCsvResult');
    resultBox.innerHTML = `<div class="text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Processing and validating CSV data...</div>`;

    try {
        const res = await fetch(`${API_BASE}/api/wines/import`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.success) {
            resultBox.innerHTML = `
                <div class="alert alert-success mt-3 py-2">
                    <i class="bi bi-check-circle-fill me-1"></i>
                    Imported <strong>${data.inserted}</strong> records successfully! Failed: <strong>${data.failed}</strong>.
                    ${data.errors.length ? `<div class="mt-2 small text-danger">${data.errors.join('<br>')}</div>` : ''}
                </div>
            `;
            showToast(`Batch import complete: ${data.inserted} inserted.`, 'success');
            loadWines();
        } else {
            resultBox.innerHTML = `<div class="alert alert-danger mt-3 py-2">${data.errors.join('<br>')}</div>`;
        }
    } catch (err) {
        resultBox.innerHTML = `<div class="alert alert-danger mt-3 py-2">Import failed: ${err.message}</div>`;
    }
}

// Download CSV
function downloadWinesCsv() {
    window.location.href = `${API_BASE}/api/wines/export/csv`;
}

function escapeQuote(str) {
    return (str || '').replace(/'/g, "\\'");
}
