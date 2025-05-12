document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('admin-table');
    if (!table) return; // Exit if table not found

    const headers = table.querySelectorAll('th.sortable-header');
    const tbody = table.querySelector('tbody#admin-table-body');
    let sortDirection = {}; // Store sort direction for each column

    headers.forEach((header, index) => {
        // Initialize sort direction state for each column
        const columnName = header.dataset.columnName;
        if (!columnName) return; // Skip if no data-column-name
        sortDirection[columnName] = 'asc'; // Default to ascending

        header.addEventListener('click', () => {
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const currentDirection = sortDirection[columnName];
            const isAscending = currentDirection === 'asc';

            // Sort rows
            rows.sort((a, b) => {
                const aText = a.children[index]?.textContent.trim() || '';
                const bText = b.children[index]?.textContent.trim() || '';

                // Basic numeric comparison (add date/currency parsing if needed)
                const aNum = parseFloat(aText);
                const bNum = parseFloat(bText);
                let comparison = 0;

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    comparison = aNum - bNum;
                } else {
                    // Case-insensitive string comparison
                    comparison = aText.toLowerCase().localeCompare(bText.toLowerCase());
                }

                return isAscending ? comparison : -comparison;
            });

            // Update sort direction for the next click
            sortDirection[columnName] = isAscending ? 'desc' : 'asc';

            // Reset directions for other columns if needed (optional)
            // Object.keys(sortDirection).forEach(key => {
            //     if (key !== columnName) sortDirection[key] = 'asc';
            // });

            // Update header indicators
            headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
            header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');

            // Clear and re-append sorted rows
            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
        });
    });

    // Add some basic CSS for sort indicators (can be moved to style.css)
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
            border-bottom: 5px solid currentColor; /* Default arrow pointing up */
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
    `;
    document.head.appendChild(style);
});
