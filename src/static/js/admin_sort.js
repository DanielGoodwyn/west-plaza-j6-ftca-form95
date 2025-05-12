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
    const filterEmailInput = document.getElementById('filter-email');
    const filterDateStartInput = document.getElementById('filter-date-start');
    const filterDateEndInput = document.getElementById('filter-date-end');
    const filterAmountTypeSelect = document.getElementById('filter-amount-type');
    const filterAmountMinInput = document.getElementById('filter-amount-min');
    const filterAmountMaxInput = document.getElementById('filter-amount-max');
    const filterSignedDateStartInput = document.getElementById('filter-signed-date-start');
    const filterSignedDateEndInput = document.getElementById('filter-signed-date-end');
    const filterBasisDeviationCheckbox = document.getElementById('filter-basis-deviation');
    const filterInjuryDeviationCheckbox = document.getElementById('filter-injury-deviation');

    // --- Boilerplate Text & Normalization ---
    const boilerplateBasisText = `While the claimant was protesting on January 6, 2021 at the West side of the U.S. Capitol, the Capitol Police and D.C. Metropolitan Police acting on behalf of the Capitol Police used excessive force against the claimant causing claimant physical injuries. The excessive force took the form of various munitions launched against the protesters including but not limited to: pepper balls, rubber balls or bullets some filled with Oleoresin Capsicum ("OC"), FM 303 projectiles, sting balls, flash bang, sting bomb and tear gas grenades, tripple chasers,pepper spray, CS Gas and physical strikes with firsts or batons.`;

    const boilerplateInjuryText = `The claimant went to the U.S. Capitol to peacefully protest the presidential election. While the claimant was in the area of the West Side of the U.S. Capitol building police launched weapons referenced above and used excessive force. The claimant was struck and or exposed to the launched munitions and/or OC or CS Gas and suffered injuries as a result. The legal ramifications of these actions are currently under review and form part of the ongoing damages being claimed.`;

    function normalizeTextForComparison(text) {
        if (!text) return '';
        // Trim, replace multiple whitespace chars (including newlines, tabs) with single space, AND CONVERT TO LOWERCASE
        return text.trim().replace(/\s+/g, ' ').toLowerCase();
    }

    const normalizedBoilerplateBasis = normalizeTextForComparison(boilerplateBasisText);
    const normalizedBoilerplateInjury = normalizeTextForComparison(boilerplateInjuryText);

    // --- Column Index Mapping ---
    const columnIndexMap = {};
    headers.forEach((header, index) => {
        const columnName = header.dataset.columnName || header.textContent.trim();
        columnIndexMap[columnName] = index;
    });

    // --- Helper Function for Parsing Amount ---
    function parseAmount(amountString) {
        if (!amountString) return null;
        const cleaned = amountString.replace(/[$,\s]/g, '');
        const amount = parseFloat(cleaned);
        return isNaN(amount) ? null : amount;
    }

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
        const emailFilter = filterEmailInput.value.toLowerCase();
        const dateStartFilter = filterDateStartInput.value;
        const dateEndFilter = filterDateEndInput.value;
        const amountTypeFilter = filterAmountTypeSelect.value;
        const amountMinFilter = filterAmountMinInput.value;
        const amountMaxFilter = filterAmountMaxInput.value;
        const signedDateStartFilter = filterSignedDateStartInput.value;
        const signedDateEndFilter = filterSignedDateEndInput.value;
        const filterBasisDeviation = filterBasisDeviationCheckbox.checked;
        const filterInjuryDeviation = filterInjuryDeviationCheckbox.checked;

        console.log(`Initial applyFilters call. filterBasisDeviation: ${filterBasisDeviation}, filterInjuryDeviation: ${filterInjuryDeviation}`);

        const nameIndex = columnIndexMap['Claimant Name'];
        const stateIndex = columnIndexMap['State'];
        const employmentIndex = columnIndexMap['Type of Employment'];
        const signatureIndex = columnIndexMap['Signature'];
        const emailIndex = columnIndexMap['Email Address'];
        const createdDateIndex = columnIndexMap['Date and Time Created'];
        const basisClaimIndex = columnIndexMap['Basis of Claim'];
        const injuryClaimIndex = columnIndexMap['Nature of Injury'];

        console.log("Column Indices:", {
            nameIndex,
            stateIndex,
            employmentIndex,
            signatureIndex,
            emailIndex,
            createdDateIndex,
            basisClaimIndex,
            injuryClaimIndex,
        });

        rows.forEach(row => {
            let showRow = true;
            const cells = row.children;

            if (showRow && nameFilter && typeof nameIndex !== 'undefined') {
                const nameText = cells[nameIndex]?.textContent?.trim().toLowerCase() || '';
                if (!nameText.includes(nameFilter)) {
                    showRow = false;
                }
            }

            if (showRow && emailFilter && typeof emailIndex !== 'undefined') {
                const emailText = cells[emailIndex]?.textContent?.trim().toLowerCase() || '';
                if (!emailText.includes(emailFilter)) {
                    showRow = false;
                }
            }

            if (showRow && stateFilter && typeof stateIndex !== 'undefined') {
                const stateText = cells[stateIndex]?.textContent.trim() || '';
                if (stateText !== stateFilter) {
                    showRow = false;
                }
            }

            if (showRow && employmentFilter && typeof employmentIndex !== 'undefined') {
                const employmentText = cells[employmentIndex]?.textContent.trim() || '';
                if (employmentText !== employmentFilter) {
                    showRow = false;
                }
            }

            if (showRow && signatureFilter && typeof signatureIndex !== 'undefined') {
                const signatureDateText = cells[signatureIndex]?.textContent.trim() || '';
                const isSigned = signatureDateText !== '' && signatureDateText.toLowerCase() !== 'pending';
                if (signatureFilter === 'pending' && isSigned) {
                    showRow = false;
                }
                if (signatureFilter === 'signed' && !isSigned) {
                    showRow = false;
                }
            }

            if (showRow && (dateStartFilter || dateEndFilter)) { // Check filters first
                if (typeof createdDateIndex !== 'undefined') {
                    const createdDateText = cells[createdDateIndex]?.textContent.trim() || '';
                    try {
                        const cellDateTimeStr = createdDateText.split(' ')[0]; // Get 'MM/DD/YYYY' part

                        // --- CONVERT cell date to YYYY-MM-DD --- START
                        let cellDateYYYYMMDD = '';
                        if (cellDateTimeStr) {
                            const parts = cellDateTimeStr.split('/');
                            if (parts.length === 3) {
                                // parts[0]=MM, parts[1]=DD, parts[2]=YYYY
                                cellDateYYYYMMDD = `${parts[2]}-${parts[0].padStart(2, '0')}-${parts[1].padStart(2, '0')}`;
                            }
                        }
                        // --- CONVERT cell date to YYYY-MM-DD --- END

                        if (cellDateYYYYMMDD) { // Use the converted date for comparison
                            if (dateStartFilter && cellDateYYYYMMDD < dateStartFilter) { // Compare YYYY-MM-DD strings
                                showRow = false;
                            }
                            if (showRow && dateEndFilter && cellDateYYYYMMDD > dateEndFilter) { // Compare YYYY-MM-DD strings
                                showRow = false;
                            }
                        } else if (dateStartFilter || dateEndFilter) {
                            // If cell has no date or invalid format but a filter is set, hide it
                            showRow = false;
                        }
                    } catch (e) {
                        console.error(`Row ${row.rowIndex}: Error parsing date:`, createdDateText, e);
                        showRow = false; // Hide row if date parsing fails
                    }
                } else {
                    console.warn("Created Date column index is undefined. Cannot filter by date."); // DEBUG LOG
                    // Decide if we should hide rows if the column is missing. Let's not hide for now.
                    // if (dateStartFilter || dateEndFilter) showRow = false;
                }
            }

            // Signed Date Range Filter - NEW
            if (showRow && (signedDateStartFilter || signedDateEndFilter)) {
                if (typeof signatureIndex !== 'undefined') {
                    const signedDateText = cells[signatureIndex]?.textContent.trim() || '';
                    // If the cell shows 'Pending' or is empty, it doesn't match a date range
                    if (!signedDateText || signedDateText.toLowerCase() === 'pending') {
                        showRow = false;
                    } else {
                        // Assume format is MM/DD/YYYY HH:MM AM/PM like the created date
                        try {
                            const cellDateTimeStr = signedDateText.split(' ')[0]; // Get 'MM/DD/YYYY' part
                            let cellDateYYYYMMDD = '';
                            if (cellDateTimeStr) {
                                const parts = cellDateTimeStr.split('/');
                                if (parts.length === 3) {
                                    cellDateYYYYMMDD = `${parts[2]}-${parts[0].padStart(2, '0')}-${parts[1].padStart(2, '0')}`;
                                }
                            }

                            if (cellDateYYYYMMDD) {
                                if (signedDateStartFilter && cellDateYYYYMMDD < signedDateStartFilter) {
                                    showRow = false;
                                }
                                if (showRow && signedDateEndFilter && cellDateYYYYMMDD > signedDateEndFilter) {
                                    showRow = false;
                                }
                            } else {
                                // Invalid date format in cell, hide if filter is set
                                showRow = false;
                            }
                        } catch (e) {
                            console.error(`Row ${row.rowIndex}: Error parsing signed date:`, signedDateText, e);
                            showRow = false; // Hide row if signed date parsing fails
                        }
                    }
                } else {
                    console.warn("Signed Date column index is undefined. Cannot filter by signed date.");
                    // If column is missing, maybe hide? Let's not for now.
                    // if (signedDateStartFilter || signedDateEndFilter) showRow = false;
                }
            }

            if (showRow && amountTypeFilter && (amountMinFilter || amountMaxFilter)) {
                const amountIndex = columnIndexMap[amountTypeFilter];
                if (typeof amountIndex !== 'undefined') {
                    const cellAmountText = cells[amountIndex]?.textContent || '';
                    const cellAmount = parseAmount(cellAmountText);

                    const minAmount = amountMinFilter ? parseFloat(amountMinFilter) : null;
                    const maxAmount = amountMaxFilter ? parseFloat(amountMaxFilter) : null;

                    if (cellAmount === null && (minAmount !== null || maxAmount !== null)) {
                        showRow = false;
                    } else if (cellAmount !== null) {
                        if (minAmount !== null && !isNaN(minAmount) && cellAmount < minAmount) {
                            showRow = false;
                        }
                        if (showRow && maxAmount !== null && !isNaN(maxAmount) && cellAmount > maxAmount) {
                            showRow = false;
                        }
                    }
                } else {
                    console.warn(`Amount column '${amountTypeFilter}' not found in table headers.`);
                }
            }

            // Basis of Claim Deviation Filter
            if (showRow && filterBasisDeviation && typeof basisClaimIndex !== 'undefined') {
                const cellContent = cells[basisClaimIndex]?.textContent || '';
                const normalizedCellText = normalizeTextForComparison(cellContent);

                console.log(`Row ${row.rowIndex} [Basis Filter]: basisClaimIndex = ${basisClaimIndex}`);
                console.log(`Row ${row.rowIndex} [Basis Filter]: Original Cell Text = '${cellContent}'`);
                console.log(`Row ${row.rowIndex} [Basis Filter]: Normalized Cell Text = '${normalizedCellText}'`);
                console.log(`Row ${row.rowIndex} [Basis Filter]: Normalized Boilerplate Basis = '${normalizedBoilerplateBasis}'`);
                const isExactMatchBasis = normalizedCellText === normalizedBoilerplateBasis;
                console.log(`Row ${row.rowIndex} [Basis Filter]: Does Normalized Cell MATCH Boilerplate Basis? ${isExactMatchBasis}`);
                
                if (isExactMatchBasis) {
                    showRow = false;
                    console.log(`%cRow ${row.rowIndex} [Basis Filter]: Matched boilerplate. Setting showRow = false.`, 'color: orange;');
                }
            } else if (showRow && filterBasisDeviation && typeof basisClaimIndex === 'undefined'){
                console.warn("Basis of Claim column index is undefined. Cannot filter by deviation.");
                // Decide if we should hide rows if column is missing? Let's not hide for now.
            }

            // Personal Injury/Wrongful Death Deviation Filter - Targets 'Nature of Injury'
            if (showRow && filterInjuryDeviation && typeof injuryClaimIndex !== 'undefined') {
                const cellContent = cells[injuryClaimIndex]?.textContent || ''; // Renamed for clarity
                const normalizedCellText = normalizeTextForComparison(cellContent);

                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: injuryClaimIndex = ${injuryClaimIndex}`);
                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: Original Cell Text = '${cellContent}'`);
                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: Normalized Cell Text = '${normalizedCellText}'`);
                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: Normalized Boilerplate Injury = '${normalizedBoilerplateInjury}'`);
                const isExactMatchInjury = normalizedCellText === normalizedBoilerplateInjury;
                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: Does Normalized Cell MATCH Boilerplate Injury? ${isExactMatchInjury}`);
                
                if (isExactMatchInjury) {
                    showRow = false;
                    console.log(`%cRow ${row.rowIndex} [Injury/Damages Filter]: Matched boilerplate. Setting showRow = false.`, 'color: orange;');
                }
            } else if (showRow && filterInjuryDeviation && typeof injuryClaimIndex === 'undefined'){
                console.warn("Column index for 'Nature of Injury' (for Personal Injury/Wrongful Death filter) is undefined. Cannot filter by deviation.");
                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: injuryClaimIndex is undefined.`);
            }

            // Apply visibility
            const intendedDisplay = showRow ? '' : 'none';
            console.log(`%cRow ${row.rowIndex}: Attempting to set display to '${intendedDisplay}'. Final showRow is ${showRow}.`, showRow ? 'color: green;' : 'color: red; font-weight: bold;');
            row.style.display = intendedDisplay;
            
            // Check computed style AFTER attempting to set it
            const computedDisplay = window.getComputedStyle(row).display;
            if (!showRow && computedDisplay !== 'none') {
                 console.error(`Row ${row.rowIndex}: FAILED TO HIDE. Inline style set to '${row.style.display}', but computed display is '${computedDisplay}'.`);
            } else if (showRow && computedDisplay === 'none') {
                 console.warn(`Row ${row.rowIndex}: FAILED TO SHOW. Inline style set to '${row.style.display}', but computed display is 'none'.`);
            } else {
                console.log(`Row ${row.rowIndex}: Style successfully applied. Computed display: '${computedDisplay}'`);
            }
        });
    }

    filterNameInput.addEventListener('input', applyFilters);
    filterStateSelect.addEventListener('change', applyFilters);
    filterEmploymentSelect.addEventListener('change', applyFilters);
    filterSignatureRadios.forEach(radio => radio.addEventListener('change', applyFilters));
    filterEmailInput.addEventListener('input', applyFilters);
    filterDateStartInput.addEventListener('change', applyFilters);
    filterDateEndInput.addEventListener('change', applyFilters);
    filterAmountTypeSelect.addEventListener('change', applyFilters);
    filterAmountMinInput.addEventListener('input', applyFilters);
    filterAmountMaxInput.addEventListener('input', applyFilters);
    filterSignedDateStartInput.addEventListener('change', applyFilters);
    filterSignedDateEndInput.addEventListener('change', applyFilters);
    filterBasisDeviationCheckbox.addEventListener('change', applyFilters);
    filterInjuryDeviationCheckbox.addEventListener('change', applyFilters);

    headers.forEach((header) => {
        const columnName = header.dataset.columnName || header.textContent.trim();
        if (!columnName || header.textContent.trim() === 'Actions') return;

        sortDirection[columnName] = 'asc';

        header.addEventListener('click', () => {
            const rows = Array.from(tbody.querySelectorAll('tr:not([style*="display: none"])'));
            if (rows.length === 0) return;

            const headerIndex = columnIndexMap[columnName];
            if (typeof headerIndex === 'undefined') {
                console.warn(`Column index not found for sorting: ${columnName}`);
                return;
            }

            const currentDirection = sortDirection[columnName];
            const isAscending = currentDirection === 'asc';

            rows.sort((a, b) => {
                const aText = a.children[headerIndex]?.textContent.trim() || '';
                const bText = b.children[headerIndex]?.textContent.trim() || '';

                let comparison = 0;
                if (columnName.includes('Date')) {
                    try {
                        const dateA = new Date(aText);
                        const dateB = new Date(bText);
                        if (!isNaN(dateA) && !isNaN(dateB)) {
                            comparison = dateA - dateB;
                        } else {
                            comparison = aText.localeCompare(bText);
                        }
                    } catch (e) {
                        comparison = aText.localeCompare(bText);
                    }
                } else if (['Property Damage Amount', 'Personal Injury Amount', 'Wrongful Death Amount', 'Total Claim Amount'].includes(columnName)) {
                    const aNum = parseAmount(aText);
                    const bNum = parseAmount(bText);
                    if (aNum !== null && bNum !== null) {
                        comparison = aNum - bNum;
                    } else if (aNum === null && bNum !== null) {
                        comparison = -1;
                    } else if (aNum !== null && bNum === null) {
                        comparison = 1;
                    }
                } else {
                    comparison = aText.toLowerCase().localeCompare(bText.toLowerCase());
                }

                return isAscending ? comparison : -comparison;
            });

            sortDirection[columnName] = isAscending ? 'desc' : 'asc';

            headers.forEach(h => {
                const hColName = h.dataset.columnName || h.textContent.trim();
                if (hColName !== 'Actions') {
                    h.classList.remove('sort-asc', 'sort-desc');
                }
            });
            header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');

            rows.forEach(row => tbody.appendChild(row));
        });
    });

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
    `;
    document.head.appendChild(style);
});
