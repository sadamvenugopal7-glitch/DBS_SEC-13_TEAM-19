/**
 * Wines Management System - Inventory Page Controller
 * Handles stock listings, status computation (IN STOCK, LOW STOCK, OUT OF STOCK),
 * transactional Add Stock, transactional Remove Stock (insufficient stock check),
 * Edit stock, Delete stock, Stock CSV upload, and Stock CSV download.
 */

let currentInventory = [];
let deleteTargetInvId = null;
let currentStatusFilter = 'ALL';

document.addEventListener('DOMContentLoaded', () => {
    loadInventory();
    loadWinesDropdown();

    // Search filter
    const searchInput = document.getElementById('inventorySearchInput');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(loadInventory, 300);
        });
    }

    // Status Tab buttons
    const tabAll = document.getElementById('tabAllStock');
    const tabLow = document.getElementById('tabLowStock');
    const tabOut = document.getElementById('tabOutOfStock');

    if (tabAll) {
        tabAll.addEventListener('click', () => {
            currentStatusFilter = 'ALL';
            setActiveTab(tabAll);
            loadInventory();
        });
    }
    if (tabLow) {
        tabLow.addEventListener('click', () => {
            currentStatusFilter = 'LOW STOCK';
            setActiveTab(tabLow);
            loadInventory();
        });
    }
    if (tabOut) {
        tabOut.addEventListener('click', () => {
            currentStatusFilter = 'OUT OF STOCK';
            setActiveTab(tabOut);
            loadInventory();
        });
    }

    // Forms
    const addStockForm = document.getElementById('addStockForm');
    if (addStockForm) addStockForm.addEventListener('submit', handleAddStockSubmit);

    const removeStockForm = document.getElementById('removeStockForm');
    if (removeStockForm) removeStockForm.addEventListener('submit', handleRemoveStockSubmit);

    const editStockForm = document.getElementById('editStockForm');
    if (editStockForm) editStockForm.addEventListener('submit', handleEditStockSubmit);

    const csvForm = document.getElementById('stockCsvForm');
    if (csvForm) csvForm.addEventListener('submit', handleStockCsvUpload);

    const confirmDeleteBtn = document.getElementById('confirmDeleteStockBtn');
    if (confirmDeleteBtn) confirmDeleteBtn.addEventListener('click', executeDeleteStock);
});

function setActiveTab(activeEl) {
    ['tabAllStock', 'tabLowStock', 'tabOutOfStock'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('active');
    });
    activeEl.classList.add('active');
}

// Fetch Inventory Records from API
async function loadInventory() {
    const search = document.getElementById('inventorySearchInput')?.value.trim() || '';
    const tbody = document.getElementById('inventoryTableBody');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading inventory from database...</td></tr>`;

    try {
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (currentStatusFilter && currentStatusFilter !== 'ALL') {
            params.append('status', currentStatusFilter);
        }

        const res = await fetch(`${API_BASE}/api/inventory?${params.toString()}`);
        if (!res.ok) throw new Error('Failed to load inventory.');

        currentInventory = await res.json();
        renderInventoryTable(currentInventory);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger py-4">Error loading inventory: ${err.message}</td></tr>`;
        showToast(err.message, 'error');
    }
}

// Render Table
function renderInventoryTable(items) {
    const tbody = document.getElementById('inventoryTableBody');
    const badge = document.getElementById('inventoryCountBadge');
    if (badge) badge.innerText = `${items.length} Products Tracked`;

    if (!items.length) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No stock records found.</td></tr>`;
        return;
    }

    tbody.innerHTML = items.map(item => {
        let statusBadge = '<span class="badge badge-in-stock">IN STOCK</span>';
        if (item.status === 'LOW STOCK') {
            statusBadge = '<span class="badge badge-low-stock">LOW STOCK</span>';
        } else if (item.status === 'OUT OF STOCK') {
            statusBadge = '<span class="badge badge-out-stock">OUT OF STOCK</span>';
        }

        return `
            <tr>
                <td class="fw-bold" style="color: var(--wine-dark);">${item.wine_name}</td>
                <td><span class="badge bg-light text-dark border">${item.category}</span></td>
                <td class="fw-bold fs-6 ${item.stock_quantity <= item.reorder_level ? 'text-danger' : 'text-success'}">${item.stock_quantity}</td>
                <td>${item.reorder_level}</td>
                <td>${formatCurrency(item.price)}</td>
                <td>${item.supplier_name}</td>
                <td class="small text-muted">${formatDateTime(item.last_updated)}</td>
                <td>${statusBadge}</td>
                <td>
                    <div class="d-flex gap-1">
                        <button class="btn btn-sm btn-outline-success" title="Add Stock" onclick="quickAddStock(${item.wine_id})">
                            <i class="bi bi-plus-lg"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-warning text-dark" title="Remove Stock" onclick="quickRemoveStock(${item.wine_id})">
                            <i class="bi bi-dash-lg"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-wine" title="Edit Levels" onclick="openEditStockModal(${item.inventory_id})">
                            <i class="bi bi-pencil-square"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" title="Delete Record" onclick="confirmDeleteStock(${item.inventory_id}, '${escapeQuote(item.wine_name)}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Populate Wine Selects
async function loadWinesDropdown() {
    try {
        const res = await fetch(`${API_BASE}/api/wines`);
        if (!res.ok) return;
        const wines = await res.json();
        
        const optionsHtml = '<option value="">-- Choose Wine --</option>' +
            wines.map(w => `<option value="${w.wine_id}">#${w.wine_id} - ${w.wine_name} (${w.category}) - Stock: ${w.stock_quantity}</option>`).join('');

        const addSel = document.getElementById('addStockWineSelect');
        const remSel = document.getElementById('removeStockWineSelect');
        if (addSel) addSel.innerHTML = optionsHtml;
        if (remSel) remSel.innerHTML = optionsHtml;
    } catch (e) {
        console.warn('Could not load wines dropdown', e);
    }
}

// 1. ADD STOCK
function openAddStockModal() {
    document.getElementById('addStockForm').reset();
    loadWinesDropdown();
    new bootstrap.Modal(document.getElementById('addStockModal')).show();
}

function quickAddStock(wineId) {
    openAddStockModal();
    setTimeout(() => {
        const sel = document.getElementById('addStockWineSelect');
        if (sel) sel.value = wineId;
    }, 200);
}

async function handleAddStockSubmit(e) {
    e.preventDefault();
    const wineId = document.getElementById('addStockWineSelect').value;
    const qty = parseInt(document.getElementById('addStockQtyInput').value, 10);

    if (!wineId || isNaN(qty) || qty <= 0) {
        showToast('Please select a wine and enter a valid quantity to add.', 'error');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/inventory/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wine_id: parseInt(wineId, 10), quantity: qty })
        });
        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.message || 'Failed to add stock.');
        }

        showToast(data.message, 'success');
        bootstrap.Modal.getInstance(document.getElementById('addStockModal')).hide();
        loadInventory();
        loadWinesDropdown();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// 2. REMOVE STOCK
function openRemoveStockModal() {
    document.getElementById('removeStockForm').reset();
    loadWinesDropdown();
    new bootstrap.Modal(document.getElementById('removeStockModal')).show();
}

function quickRemoveStock(wineId) {
    openRemoveStockModal();
    setTimeout(() => {
        const sel = document.getElementById('removeStockWineSelect');
        if (sel) sel.value = wineId;
    }, 200);
}

async function handleRemoveStockSubmit(e) {
    e.preventDefault();
    const wineId = document.getElementById('removeStockWineSelect').value;
    const qty = parseInt(document.getElementById('removeStockQtyInput').value, 10);

    if (!wineId || isNaN(qty) || qty <= 0) {
        showToast('Please select a wine and enter a valid quantity to remove.', 'error');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/inventory/remove`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wine_id: parseInt(wineId, 10), quantity: qty })
        });
        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.message || 'Failed to remove stock.');
        }

        showToast(data.message, 'success');
        bootstrap.Modal.getInstance(document.getElementById('removeStockModal')).hide();
        loadInventory();
        loadWinesDropdown();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// 3. EDIT STOCK
function openEditStockModal(invId) {
    const item = currentInventory.find(i => i.inventory_id === invId);
    if (!item) return;

    document.getElementById('editInvId').value = item.inventory_id;
    document.getElementById('editWineNameInput').value = `${item.wine_name} (${item.category})`;
    document.getElementById('editStockQtyInput').value = item.stock_quantity;
    document.getElementById('editReorderInput').value = item.reorder_level;

    new bootstrap.Modal(document.getElementById('editStockModal')).show();
}

async function handleEditStockSubmit(e) {
    e.preventDefault();
    const invId = document.getElementById('editInvId').value;
    const stock = parseInt(document.getElementById('editStockQtyInput').value, 10);
    const reorder = parseInt(document.getElementById('editReorderInput').value, 10);

    if (isNaN(stock) || stock < 0 || isNaN(reorder) || reorder < 0) {
        showToast('Stock quantity and reorder level cannot be negative.', 'error');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/inventory/${invId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stock_quantity: stock, reorder_level: reorder })
        });
        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.message || 'Failed to update stock levels.');
        }

        showToast(data.message, 'success');
        bootstrap.Modal.getInstance(document.getElementById('editStockModal')).hide();
        loadInventory();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// 4. DELETE STOCK
function confirmDeleteStock(invId, wineName) {
    deleteTargetInvId = invId;
    document.getElementById('deleteStockTargetName').innerText = wineName;
    new bootstrap.Modal(document.getElementById('deleteStockModal')).show();
}

async function executeDeleteStock() {
    if (!deleteTargetInvId) return;

    try {
        const res = await fetch(`${API_BASE}/api/inventory/${deleteTargetInvId}`, {
            method: 'DELETE'
        });
        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.message || 'Cannot delete inventory record.');
        }

        showToast('Stock record deleted successfully.', 'success');
        bootstrap.Modal.getInstance(document.getElementById('deleteStockModal')).hide();
        deleteTargetInvId = null;
        loadInventory();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// 5. CSV BATCH UPLOAD
async function handleStockCsvUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById('stockCsvFile');
    if (!fileInput.files.length) {
        showToast('Please choose an inventory CSV file.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const resultBox = document.getElementById('stockCsvResult');
    resultBox.innerHTML = `<div class="text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Reconciling stock records...</div>`;

    try {
        const res = await fetch(`${API_BASE}/api/inventory/import`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.success) {
            resultBox.innerHTML = `
                <div class="alert alert-success mt-3 py-2">
                    <i class="bi bi-check-circle-fill me-1"></i>
                    Updated <strong>${data.inserted}</strong> stock rows. Failed: <strong>${data.failed}</strong>.
                    ${data.errors.length ? `<div class="mt-2 small text-danger">${data.errors.join('<br>')}</div>` : ''}
                </div>
            `;
            showToast(`Inventory CSV import finished: ${data.inserted} updated.`, 'success');
            loadInventory();
        } else {
            resultBox.innerHTML = `<div class="alert alert-danger mt-3 py-2">${data.errors.join('<br>')}</div>`;
        }
    } catch (err) {
        resultBox.innerHTML = `<div class="alert alert-danger mt-3 py-2">Import failed: ${err.message}</div>`;
    }
}

// 6. CSV EXPORT
function downloadInventoryCsv() {
    window.location.href = `${API_BASE}/api/inventory/export`;
}

function escapeQuote(str) {
    return (str || '').replace(/'/g, "\\'");
}
