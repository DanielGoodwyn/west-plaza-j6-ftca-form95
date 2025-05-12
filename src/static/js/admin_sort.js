document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('admin-table');
    if (!table) return; // Exit if table not found

    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody#admin-table-body');
    const headers = Array.from(thead.querySelectorAll('th.sortable-header')); // Convert NodeList to Array
    let sortDirection = {}; // Store sort direction for each column

    // --- Filter Elements ---
    const filterNameInput = document.getElementById('filter-name');
    const filterStateSelect = document.getElementById('filter-state');
    const filterEmploymentSelect = document.getElementById('filter-employment');
    const filterSignatureRadios = document.querySelectorAll('.filter-signature');

    // --- Column Index Mapping ---
    // Create a map from display header name to column index
    const columnIndexMap = {};
    headers.forEach((header, index) => {
        const columnName = header.dataset.columnName || header.textContent.trim();
        columnIndexMap[columnName] = index;
    });

    // --- Filter Function ---
    function applyFilters() {
        if (!tbody) return;
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const nameFilter = filterNameInput.value.toLowerCase();
        const stateFilter = filterStateSelect.value;
        const employmentFilter = filterEmploymentSelect.value;
        let signatureFilter = '';
        filterSignatureRadios.forEach(radio => {
            if (radio.checked) {
                signatureFilter = radio.value;
            }
        });

        const nameIndex = columnIndexMap['Claimant Name'];
        const stateIndex = columnIndexMap['State'];
        const employmentIndex = columnIndexMap['Type of Employment'];
        const signatureDateIndex = columnIndexMap['Date and Time Signed']; // Assuming this column indicates signed status

        rows.forEach(row => {
            let showRow = true;
            const cells = row.children;

            // Name Filter (Contains)
            if (nameFilter && typeof nameIndex !== 'undefined') {
                const nameText = cells[nameIndex]?.textContent?.trim().toLowerCase() || ''; 
                const includesCheck = nameText.includes(nameFilter); 
                if (!includesCheck) { 
                    showRow = false;
                }
            } 

            // State Filter (Exact Match)
            if (showRow && stateFilter && typeof stateIndex !== 'undefined') {
                const stateText = cells[stateIndex]?.textContent.trim() || '';
                if (stateText !== stateFilter) {
                    showRow = false;
                }
            }

            // Employment Filter (Exact Match)
            if (showRow && employmentFilter && typeof employmentIndex !== 'undefined') {
                const employmentText = cells[employmentIndex]?.textContent.trim() || '';
                if (employmentText !== employmentFilter) {
                    showRow = false;
                }
            }

            // Signature Filter ('pending' or 'signed')
            if (showRow && signatureFilter && typeof signatureDateIndex !== 'undefined') {
                const signatureDateText = cells[signatureDateIndex]?.textContent.trim() || '';
                const isSigned = signatureDateText !== '' && signatureDateText.toLowerCase() !== 'pending'; 

                if (signatureFilter === 'pending' && isSigned) {
                    showRow = false;
                }
                if (signatureFilter === 'signed' && !isSigned) {
                    showRow = false;
                }
            }

            // Apply visibility
            row.style.display = showRow ? '' : 'none';
        });
    }

    // --- Event Listeners ---
    // Sorting Listeners (Existing Code)
    headers.forEach((header) => {
        const columnName = header.dataset.columnName || header.textContent.trim();
        if (!columnName || header.textContent.trim() === 'Actions') return; 

        sortDirection[columnName] = 'asc'; 

        header.addEventListener('click', () => {
            const rows = Array.from(tbody.querySelectorAll('tr:not([style*="display: none"])')); 
            if (rows.length === 0) return;

            const headerIndex = columnIndexMap[columnName]; 
            if (typeof headerIndex === 'undefined') return; 

            const currentDirection = sortDirection[columnName];
            const isAscending = currentDirection === 'asc';

            // Sort visible rows
            rows.sort((a, b) => {
                const aText = a.children[headerIndex]?.textContent.trim() || '';
                const bText = b.children[headerIndex]?.textContent.trim() || '';

                // Basic numeric/date/string comparison (can be enhanced)
                let comparison = 0;
                // Attempt date comparison first for 'Date' columns
                if (columnName.includes('Date')) {
                    try {
                        // Attempt to parse dates - might need more robust parsing
                        const dateA = new Date(aText);
                        const dateB = new Date(bText);
                        if (!isNaN(dateA) && !isNaN(dateB)) {
                            comparison = dateA - dateB;
                        } else {
                           // Fallback to string compare if dates are invalid/mixed
                            comparison = aText.localeCompare(bText);
                        }
                    } catch (e) {
                        comparison = aText.localeCompare(bText); 
                    }
                } else {
                     // Attempt numeric comparison
                    const aNum = parseFloat(aText.replace(/[^\d.-]/g, '')); 
                    const bNum = parseFloat(bText.replace(/[^\d.-]/g, ''));
                    if (!isNaN(aNum) && !isNaN(bNum)) {
                        comparison = aNum - bNum;
                    } else {
                        // Fallback to case-insensitive string comparison
                        comparison = aText.toLowerCase().localeCompare(bText.toLowerCase());
                    }
                }

                return isAscending ? comparison : -comparison;
            });

            // Update sort direction for the next click
            sortDirection[columnName] = isAscending ? 'desc' : 'asc';

            // Update header indicators
            headers.forEach(h => {
                 const hColName = h.dataset.columnName || h.textContent.trim();
                 if (hColName !== 'Actions') {
                    h.classList.remove('sort-asc', 'sort-desc');
                 }
            });
            header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');

            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row)); 
        });
    });

    // Filter Listeners
    filterNameInput.addEventListener('input', applyFilters);
    filterStateSelect.addEventListener('change', applyFilters);
    filterEmploymentSelect.addEventListener('change', applyFilters);
    filterSignatureRadios.forEach(radio => radio.addEventListener('change', applyFilters));

    // --- Initial Styling for Sort Arrows (Existing Code) ---
    const style = document.createElement('style');
    style.textContent = `
        .sortable-header::after {
            content: '';
            display: inline-block;
            margin-left: 5px;
            opacity: 0.3;
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-bottom: 5px solid currentColor; 
        }
        .sortable-header.sort-asc::after {
            opacity: 1;
            border-bottom: 5px solid currentColor;
            border-top: none;
        }
        .sortable-header.sort-desc::after {
            opacity: 1;
            border-top: 5px solid currentColor;
            border-bottom: none;
        }
        /* Style for filtered rows (optional) */
        /* tbody tr[style*="display: none"] { */
        /*     background-color: #f8f9fa; */
        /* } */
    `;
    document.head.appendChild(style);
});
