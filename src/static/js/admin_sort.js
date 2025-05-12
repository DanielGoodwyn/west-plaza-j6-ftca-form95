document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed'); // Log DOM ready

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
    const filterEmailInput = document.getElementById('filter-email');
    const filterAmountMinInput = document.getElementById('filter-amount-min');
    const filterAmountMaxInput = document.getElementById('filter-amount-max');
    const filterBasisDeviationCheckbox = document.getElementById('filter-basis-deviation');
    const filterInjuryDeviationCheckbox = document.getElementById('filter-injury-deviation');
    const filterCreatedStartInput = document.getElementById('filter-created-start');
    const filterCreatedEndInput = document.getElementById('filter-created-end');

    // Add references for new amount filters
    const filterPropDmgMinInput = document.getElementById('filter-prop-dmg-min');
    const filterPropDmgMaxInput = document.getElementById('filter-prop-dmg-max');
    const filterPersInjMinInput = document.getElementById('filter-pers-inj-min');
    const filterPersInjMaxInput = document.getElementById('filter-pers-inj-max');
    const filterWrongfulDeathMinInput = document.getElementById('filter-wrongful-death-min');
    const filterWrongfulDeathMaxInput = document.getElementById('filter-wrongful-death-max');

    // Get references for signed date filters
    const filterSignedDateStartInput = document.getElementById('filter-signed-date-start');
    const filterSignedDateEndInput = document.getElementById('filter-signed-date-end');

    // Get references for new dropdown filters
    const filterSignatureStatusDropdown = document.getElementById('filter-signature-status');
    const filterSignedDateStatusDropdown = document.getElementById('filter-signed-date-status');
    const filterMaritalStatusDropdown = document.getElementById('filter-marital-status');

    // --- References for NEW Text Filters --- 
    const filterPhoneNumberInput = document.getElementById('filter-phone-number');
    const filterStreetAddressInput = document.getElementById('filter-street-address');
    const filterCityInput = document.getElementById('filter-city');
    const filterZipCodeInput = document.getElementById('filter-zip-code');
    const filterBasisOfClaimInput = document.getElementById('filter-basis-of-claim');
    const filterNatureOfInjuryInput = document.getElementById('filter-nature-of-injury');
    const filterCapitolExperienceInput = document.getElementById('filter-capitol-experience');
    const filterInjuriesDamagesInput = document.getElementById('filter-injuries-damages');
    const filterEntryExitTimeInput = document.getElementById('filter-entry-exit-time');
    const filterInsideCapitolDetailsInput = document.getElementById('filter-inside-capitol-details');
    const filterSignatureTextInput = document.getElementById('filter-signature-text');

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

    // --- Helper Function to Parse Display Dates ---
    // Parses dates like 'MM/DD/YYYY hh:mm AM/PM' or 'Pending'
    // Returns Date object or null
    function parseDisplayDate(dateString) {
        if (!dateString || dateString.toLowerCase() === 'pending' || dateString.toLowerCase() === 'pending signature') {
            return null;
        }
        // Basic attempt assuming 'MM/DD/YYYY' is at the start
        const parts = dateString.split(' ')[0].split('/');
        if (parts.length === 3) {
            const month = parseInt(parts[0], 10);
            const day = parseInt(parts[1], 10);
            const year = parseInt(parts[2], 10);
            // Very basic validation
            if (month >= 1 && month <= 12 && day >= 1 && day <= 31 && year > 1900) {
                // Note: This doesn't parse time, but compares against start/end of day
                // For more accuracy, we'd need a more robust parser or ensure consistent format
                return new Date(year, month - 1, day); // Month is 0-indexed
            }
        }
        // console.warn("Failed to parse date string:", dateString);
        return null; // Return null if parsing fails
    }

    // --- Filter Function ---
    function applyFilters() {
        console.log('--- applyFilters function called ---'); // Log function entry
        if (!tbody) {
            console.error("applyFilters: tbody not found");
            return;
        }
        const rows = Array.from(tbody.querySelectorAll('tr'));

        // Explicitly log emailIndex value at the start
        const emailIndex = columnIndexMap['Email Address'];
        console.log(`DEBUG: emailIndex value is: ${emailIndex} (Type: ${typeof emailIndex})`);

        // Explicitly log employmentIndex value at the start
        const employmentIndex = columnIndexMap['Type of Employment'];
        console.log(`DEBUG: employmentIndex value is: ${employmentIndex} (Type: ${typeof employmentIndex})`);

        const nameFilter = filterNameInput.value.toLowerCase();
        const stateFilter = filterStateSelect.value;
        const employmentFilter = filterEmploymentSelect.value.trim().toLowerCase() || '';
        const emailFilter = filterEmailInput.value.toLowerCase();
        const createdStartFilter = filterCreatedStartInput.value;
        const createdEndFilter = filterCreatedEndInput.value;
        const amountMinFilter = filterAmountMinInput.value;
        const amountMaxFilter = filterAmountMaxInput.value;
        const filterBasisDeviation = filterBasisDeviationCheckbox.checked;
        const filterInjuryDeviation = filterInjuryDeviationCheckbox.checked;

        // Get values for new amount filters
        const propDmgMinFilter = filterPropDmgMinInput.value;
        const propDmgMaxFilter = filterPropDmgMaxInput.value;
        const persInjMinFilter = filterPersInjMinInput.value;
        const persInjMaxFilter = filterPersInjMaxInput.value;
        const wrongfulDeathMinFilter = filterWrongfulDeathMinInput.value;
        const wrongfulDeathMaxFilter = filterWrongfulDeathMaxInput.value;

        // Get values for signed date filters
        const signedDateStartFilter = filterSignedDateStartInput.value;
        const signedDateEndFilter = filterSignedDateEndInput.value;

        // Get values from new dropdowns
        const signatureStatusFilter = filterSignatureStatusDropdown.value;
        const signedDateStatusFilter = filterSignedDateStatusDropdown.value;
        const maritalStatusFilter = filterMaritalStatusDropdown.value;

        console.log(`Initial applyFilters call. filterBasisDeviation: ${filterBasisDeviation}, filterInjuryDeviation: ${filterInjuryDeviation}`);
        console.log(`Signature Status: ${signatureStatusFilter}, Signed Date Status: ${signedDateStatusFilter}`);

        // --- Get values for NEW text filters ---
        const phoneNumberFilter = filterPhoneNumberInput?.value.toLowerCase() || '';
        const streetAddressFilter = filterStreetAddressInput?.value.toLowerCase() || '';
        const cityFilter = filterCityInput?.value.toLowerCase() || '';
        const zipCodeFilter = filterZipCodeInput?.value.toLowerCase() || '';
        const basisOfClaimFilter = filterBasisOfClaimInput?.value.toLowerCase() || ''; // Textbox filter for basis
        const natureOfInjuryFilter = filterNatureOfInjuryInput?.value.toLowerCase() || ''; // Textbox filter for injury
        const capitolExperienceFilter = filterCapitolExperienceInput?.value.toLowerCase() || '';
        const injuriesDamagesFilter = filterInjuriesDamagesInput?.value.toLowerCase() || '';
        const entryExitTimeFilter = filterEntryExitTimeInput?.value.toLowerCase() || '';
        const insideCapitolDetailsFilter = filterInsideCapitolDetailsInput?.value.toLowerCase() || '';
        const signatureTextFilter = filterSignatureTextInput?.value.toLowerCase() || ''; // Textbox filter for signature

        const nameIndex = columnIndexMap['Claimant Name'];
        const stateIndex = columnIndexMap['State'];
        const createdIndex = columnIndexMap['Date and Time Created'];
        const signatureIndex = columnIndexMap['Signature']; // Keep for dropdown filter
        const signedDateIndex = columnIndexMap['Date and Time Signed']; // For date range filter
        const basisIndex = columnIndexMap['Basis of Claim'];
        const injuryIndex = columnIndexMap['Nature of Injury'];
        const totalAmountIndex = columnIndexMap['Total Claim Amount'];
        // Add indices for new amount columns
        const propDmgIndex = columnIndexMap['Property Damage Amount'];
        const persInjIndex = columnIndexMap['Personal Injury Amount'];
        const wrongfulDeathIndex = columnIndexMap['Wrongful Death Amount'];

        // --- Get indices for NEW text filter columns ---
        const phoneNumberIndex = columnIndexMap['Phone Number'];
        const streetAddressIndex = columnIndexMap['Street Address'];
        const cityIndex = columnIndexMap['City'];
        const zipCodeIndex = columnIndexMap['Zip Code'];
        // Basis and Injury indices already exist (basisIndex, injuryIndex)
        const capitolExperienceIndex = columnIndexMap['Capitol Experience'];
        const injuriesDamagesIndex = columnIndexMap['Injuries/Damages'];
        const entryExitTimeIndex = columnIndexMap['Entry/Exit Time'];
        const insideCapitolDetailsIndex = columnIndexMap['Inside Capitol Details'];
        // Signature index already exists (signatureIndex) - used for both dropdown and text
        const maritalStatusIndex = columnIndexMap['Marital Status'];

        console.log("Column Indices:", {
            nameIndex,
            emailIndex,
            stateIndex,
            createdIndex,
            signatureIndex,
            signedDateIndex,
            basisIndex,
            injuryIndex,
            totalAmountIndex,
            propDmgIndex,        // Log new indices
            persInjIndex,       // Log new indices
            wrongfulDeathIndex,  // Log new indices
            // Log new text filter indices
            phoneNumberIndex,
            streetAddressIndex,
            cityIndex,
            zipCodeIndex,
            capitolExperienceIndex,
            injuriesDamagesIndex,
            entryExitTimeIndex,
            insideCapitolDetailsIndex,
            maritalStatusIndex
        });

        rows.forEach(row => {
            let showRow = true;
            const cells = row.children;

            // Name Filter
            if (showRow && nameFilter && typeof nameIndex !== 'undefined') {
                const originalNameText = cells[nameIndex]?.textContent?.trim() || ''; // Get original text
                const lowerNameText = originalNameText.toLowerCase(); // Convert to lowercase for comparison
                // nameFilter is already lowercase from its definition above
                const comparisonResult = lowerNameText.includes(nameFilter);
                console.log(`[Name Filter] Index: ${nameIndex}, Filter: '${nameFilter}', OriginalCell: '${originalNameText}', LowerCell: '${lowerNameText}', Matches: ${comparisonResult}`); // Add logging
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            if (showRow && emailFilter && typeof emailIndex !== 'undefined') {
                const originalEmailText = cells[emailIndex]?.textContent?.trim() || '';
                const lowerEmailText = originalEmailText.toLowerCase();
                const comparisonResult = lowerEmailText.includes(emailFilter); // emailFilter is already lowercase
                console.log(`[Email Filter] Index: ${emailIndex}, Filter: '${emailFilter}', OriginalCell: '${originalEmailText}', LowerCell: '${lowerEmailText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            if (showRow && stateFilter && typeof stateIndex !== 'undefined') {
                const stateText = cells[stateIndex]?.textContent.trim() || '';
                if (stateText !== stateFilter) {
                    showRow = false;
                }
            }

            // Type of Employment Filter (Dropdown - requires exact match)
            if (showRow && employmentFilter && typeof employmentIndex !== 'undefined') {
                const originalEmploymentText = cells[employmentIndex]?.textContent.trim() || ''; // Get original text
                const lowerEmploymentText = originalEmploymentText.toLowerCase(); // Convert to lowercase for comparison
                // employmentFilter is already lowercase from its definition
                const comparisonResult = lowerEmploymentText === employmentFilter; // Use strict equality for dropdown
                console.log(`[Employment Filter] Index: ${employmentIndex}, Filter: '${employmentFilter}', OriginalCell: '${originalEmploymentText}', LowerCell: '${lowerEmploymentText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            // Signature Status Filter (replaces radio buttons)
            if (showRow && signatureStatusFilter !== 'all') {
                if (typeof signatureIndex !== 'undefined') {
                    const signatureCellText = cells[signatureIndex]?.textContent.trim().toLowerCase() || '';
                    if (signatureStatusFilter === 'pending') {
                        if (signatureCellText !== 'pending signature') {
                            showRow = false;
                        }
                    } else if (signatureStatusFilter === 'signed') {
                        if (signatureCellText === 'pending signature' || signatureCellText === '') {
                            showRow = false;
                        }
                    }
                } else {
                    console.warn("Signature column index is undefined. Cannot filter by signature status.");
                }
            }

            // Date and Time Signed - Actual Date Range Filter (for its own column's dates)
            if (showRow && (signedDateStartFilter || signedDateEndFilter)) { // Only apply if a date range is entered
                if (typeof signedDateIndex !== 'undefined') {
                    const actualSignedDateCellText = cells[signedDateIndex]?.textContent.trim().toLowerCase() || '';
                    console.log(`[Actual Signed Date Range] Row ${row.rowIndex}: Cell Text='${actualSignedDateCellText}', Start='${signedDateStartFilter}', End='${signedDateEndFilter}'`);

                    if (actualSignedDateCellText === 'pending' || !actualSignedDateCellText) {
                        // If a date range is active, and the cell is pending/empty, hide it.
                        showRow = false;
                    } else {
                        const datePart = actualSignedDateCellText.split(' ')[0]; // Get 'mm/dd/yyyy'
                        let cellDateYYYYMMDD = '';
                        if (datePart) {
                            const parts = datePart.split('/');
                            if (parts.length === 3) { // MM, DD, YYYY
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
                            // If parsing fails and date filter active, hide
                            showRow = false;
                        }
                    }
                } else {
                    showRow = false; // If date range is active but column is missing, hide.
                    console.warn("'Date and Time Signed' column index is undefined. Cannot filter by its date range.");
                }
            }

            if (showRow && (createdStartFilter || createdEndFilter)) { // Check filters first
                if (typeof createdIndex !== 'undefined') {
                    const createdDateText = cells[createdIndex]?.textContent.trim() || '';
                    console.log(`Row ${row.rowIndex} [Date Filter]: Cell Text='${createdDateText}'`); // Log cell text
                    const rowDate = parseDisplayDate(createdDateText);
                    console.log(`Row ${row.rowIndex} [Date Filter]: Parsed Date='${rowDate}'`); // Log parsed date

                    if (rowDate) {
                        const startDate = createdStartFilter ? new Date(createdStartFilter + 'T00:00:00') : null;
                        const endDate = createdEndFilter ? new Date(createdEndFilter + 'T23:59:59') : null;
                        console.log(`Row ${row.rowIndex} [Date Filter]: Comparing with Start='${startDate}', End='${endDate}'`); // Log comparison values

                        if (startDate && rowDate < startDate) {
                            console.log(`Row ${row.rowIndex} [Date Filter]: Hiding - Before Start Date`); // Log reason for hiding
                            showRow = false;
                        }
                        if (endDate && rowDate > endDate) {
                             console.log(`Row ${row.rowIndex} [Date Filter]: Hiding - After End Date`); // Log reason for hiding
                            showRow = false;
                        }
                    } else if (createdStartFilter || createdEndFilter) {
                         console.warn(`Row ${row.rowIndex} [Date Filter]: Hiding - Could not parse date: ${createdDateText}`); // Log parse failure
                        showRow = false;
                    }
                } else {
                    console.warn("Created Date column index is undefined. Cannot filter by date."); // DEBUG LOG
                    // Decide if we should hide rows if the column is missing. Let's not hide for now.
                    // if (createdStartFilter || createdEndFilter) showRow = false;
                }
            }

            if (showRow && (amountMinFilter || amountMaxFilter)) {
                const amountIndex = columnIndexMap['Total Claim Amount'];
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
                    console.warn("Total Amount column index is undefined. Cannot filter by amount.");
                }
            }

            // Property Damage Amount Filter
            if (showRow && (propDmgMinFilter || propDmgMaxFilter)) {
                if (typeof propDmgIndex !== 'undefined') {
                    const cellAmountText = cells[propDmgIndex]?.textContent || '';
                    const cellAmount = parseAmount(cellAmountText);
                    console.log(`[PropDmg Filter] Row ${row.rowIndex}: Cell Text='${cellAmountText}', Parsed Amount=${cellAmount}, Min Filter='${propDmgMinFilter}', Max Filter='${propDmgMaxFilter}'`);
                    if (cellAmount === null) {
                        showRow = false; // Hide if amount cannot be parsed and a filter is set
                    } else {
                        if (propDmgMinFilter && cellAmount < parseFloat(propDmgMinFilter)) {
                            showRow = false;
                        }
                        if (showRow && propDmgMaxFilter && cellAmount > parseFloat(propDmgMaxFilter)) {
                            showRow = false;
                        }
                    }
                } else {
                    console.warn("Property Damage Amount column index is undefined. Cannot filter.");
                }
            }

            // Personal Injury Amount Filter
            if (showRow && (persInjMinFilter || persInjMaxFilter)) {
                if (typeof persInjIndex !== 'undefined') {
                    const cellAmountText = cells[persInjIndex]?.textContent || '';
                    const cellAmount = parseAmount(cellAmountText);
                    console.log(`[PersInj Filter] Row ${row.rowIndex}: Cell Text='${cellAmountText}', Parsed Amount=${cellAmount}, Min Filter='${persInjMinFilter}', Max Filter='${persInjMaxFilter}'`);
                    if (cellAmount === null) {
                        showRow = false;
                    } else {
                        if (persInjMinFilter && cellAmount < parseFloat(persInjMinFilter)) {
                            showRow = false;
                        }
                        if (showRow && persInjMaxFilter && cellAmount > parseFloat(persInjMaxFilter)) {
                            showRow = false;
                        }
                    }
                } else {
                    console.warn("Personal Injury Amount column index is undefined. Cannot filter.");
                }
            }

            // Wrongful Death Amount Filter
            if (showRow && (wrongfulDeathMinFilter || wrongfulDeathMaxFilter)) {
                if (typeof wrongfulDeathIndex !== 'undefined') {
                    const cellAmountText = cells[wrongfulDeathIndex]?.textContent || '';
                    const cellAmount = parseAmount(cellAmountText);
                    console.log(`[WrongfulDeath Filter] Row ${row.rowIndex}: Cell Text='${cellAmountText}', Parsed Amount=${cellAmount}, Min Filter='${wrongfulDeathMinFilter}', Max Filter='${wrongfulDeathMaxFilter}'`);
                    if (cellAmount === null) {
                        showRow = false;
                    } else {
                        if (wrongfulDeathMinFilter && cellAmount < parseFloat(wrongfulDeathMinFilter)) {
                            showRow = false;
                        }
                        if (showRow && wrongfulDeathMaxFilter && cellAmount > parseFloat(wrongfulDeathMaxFilter)) {
                            showRow = false;
                        }
                    }
                } else {
                    console.warn("Wrongful Death Amount column index is undefined. Cannot filter.");
                }
            }

            // Basis of Claim Deviation Filter
            if (showRow && filterBasisDeviation && typeof basisIndex !== 'undefined') {
                const cellContent = cells[basisIndex]?.textContent || '';
                const normalizedCellText = normalizeTextForComparison(cellContent);

                console.log(`Row ${row.rowIndex} [Basis Filter]: basisIndex = ${basisIndex}`);
                console.log(`Row ${row.rowIndex} [Basis Filter]: Original Cell Text = '${cellContent}'`);
                console.log(`Row ${row.rowIndex} [Basis Filter]: Normalized Cell Text = '${normalizedCellText}'`);
                console.log(`Row ${row.rowIndex} [Basis Filter]: Normalized Boilerplate Basis = '${normalizedBoilerplateBasis}'`);
                const isExactMatchBasis = normalizedCellText === normalizedBoilerplateBasis;
                console.log(`Row ${row.rowIndex} [Basis Filter]: Does Normalized Cell MATCH Boilerplate Basis? ${isExactMatchBasis}`);
                
                if (isExactMatchBasis) {
                    showRow = false;
                    console.log(`%cRow ${row.rowIndex} [Basis Filter]: Matched boilerplate. Setting showRow = false.`, 'color: orange;');
                }
            } else if (showRow && filterBasisDeviation && typeof basisIndex === 'undefined'){
                console.warn("Basis of Claim column index is undefined. Cannot filter by deviation.");
                // Decide if we should hide rows if column is missing? Let's not hide for now.
            }

            // Personal Injury/Wrongful Death Deviation Filter - Targets 'Nature of Injury'
            if (showRow && filterInjuryDeviation && typeof injuryIndex !== 'undefined') {
                const cellContent = cells[injuryIndex]?.textContent || ''; // Renamed for clarity
                const normalizedCellText = normalizeTextForComparison(cellContent);

                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: injuryIndex = ${injuryIndex}`);
                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: Original Cell Text = '${cellContent}'`);
                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: Normalized Cell Text = '${normalizedCellText}'`);
                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: Normalized Boilerplate Injury = '${normalizedBoilerplateInjury}'`);
                const isExactMatchInjury = normalizedCellText === normalizedBoilerplateInjury;
                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: Does Normalized Cell MATCH Boilerplate Injury? ${isExactMatchInjury}`);
                
                if (isExactMatchInjury) {
                    showRow = false;
                    console.log(`%cRow ${row.rowIndex} [Injury/Damages Filter]: Matched boilerplate. Setting showRow = false.`, 'color: orange;');
                }
            } else if (showRow && filterInjuryDeviation && typeof injuryIndex === 'undefined'){
                console.warn("Column index for 'Nature of Injury' (for Personal Injury/Wrongful Death filter) is undefined. Cannot filter by deviation.");
                console.log(`Row ${row.rowIndex} [Injury/Damages Filter]: injuryIndex is undefined.`);
            }

            // Date Range Filter
            if (showRow && (createdStartFilter || createdEndFilter)) {
                if (typeof createdIndex !== 'undefined') {
                    const createdDateText = cells[createdIndex]?.textContent.trim() || '';
                    console.log(`Row ${row.rowIndex} [Date Filter]: Cell Text='${createdDateText}'`); // Log cell text
                    const rowDate = parseDisplayDate(createdDateText);
                    console.log(`Row ${row.rowIndex} [Date Filter]: Parsed Date='${rowDate}'`); // Log parsed date

                    if (rowDate) {
                        const startDate = createdStartFilter ? new Date(createdStartFilter + 'T00:00:00') : null;
                        const endDate = createdEndFilter ? new Date(createdEndFilter + 'T23:59:59') : null;
                        console.log(`Row ${row.rowIndex} [Date Filter]: Comparing with Start='${startDate}', End='${endDate}'`); // Log comparison values

                        if (startDate && rowDate < startDate) {
                            console.log(`Row ${row.rowIndex} [Date Filter]: Hiding - Before Start Date`); // Log reason for hiding
                            showRow = false;
                        }
                        if (endDate && rowDate > endDate) {
                             console.log(`Row ${row.rowIndex} [Date Filter]: Hiding - After End Date`); // Log reason for hiding
                            showRow = false;
                        }
                    } else if (createdStartFilter || createdEndFilter) {
                         console.warn(`Row ${row.rowIndex} [Date Filter]: Hiding - Could not parse date: ${createdDateText}`); // Log parse failure
                        showRow = false;
                    }
                } else {
                    console.warn("Created Date column index is undefined. Cannot filter by date."); // DEBUG LOG
                    // Decide if we should hide rows if the column is missing. Let's not hide for now.
                    // if (createdStartFilter || createdEndFilter) showRow = false;
                }
            }

            if (showRow && (amountMinFilter || amountMaxFilter)) {
                const amountIndex = columnIndexMap['Total Claim Amount'];
                if (typeof amountIndex !== 'undefined') {
                    const amountText = cells[amountIndex]?.textContent || '';
                    console.log(`Row ${row.rowIndex} [Amount Filter]: Cell Text='${amountText}'`); // Log cell text
                    const rowAmount = parseFloat(amountText.replace(/[$,]/g, ''));
                    console.log(`Row ${row.rowIndex} [Amount Filter]: Parsed Amount='${rowAmount}'`); // Log parsed amount

                    if (!isNaN(rowAmount)) {
                        const minAmount = amountMinFilter ? parseFloat(amountMinFilter) : null;
                        const maxAmount = amountMaxFilter ? parseFloat(amountMaxFilter) : null;
                        console.log(`Row ${row.rowIndex} [Amount Filter]: Comparing with Min='${minAmount}', Max='${maxAmount}'`); // Log comparison values

                        if (minAmount !== null && rowAmount < minAmount) {
                            console.log(`Row ${row.rowIndex} [Amount Filter]: Hiding - Below Min Amount`); // Log reason for hiding
                            showRow = false;
                        }
                        if (showRow && maxAmount !== null && rowAmount > maxAmount) {
                            console.log(`Row ${row.rowIndex} [Amount Filter]: Hiding - Above Max Amount`); // Log reason for hiding
                            showRow = false;
                        }
                    } else if (amountMinFilter || amountMaxFilter) {
                        console.warn(`Row ${row.rowIndex} [Amount Filter]: Hiding - Could not parse amount: ${amountText}`); // Log parse failure
                        showRow = false;
                    }
                } else {
                    console.warn("Total Amount column index is undefined. Cannot filter by amount.");
                }
            }

            // Signed Date Range Filter (for 'Date and Time Signed' column)
            if (showRow && (signedDateStartFilter || signedDateEndFilter)) {
                if (typeof signedDateIndex !== 'undefined') {
                    const signedDateCellText = cells[signedDateIndex]?.textContent.trim() || '';
                    console.log(`[Signed Date Filter] Row ${row.rowIndex}: Cell Text='${signedDateCellText}', Start Filter='${signedDateStartFilter}', End Filter='${signedDateEndFilter}'`);

                    if (!signedDateCellText || signedDateCellText.toLowerCase() === 'pending' || signedDateCellText.toLowerCase().startsWith('pending signature')) {
                        // If a date filter is set, and the cell is pending/empty, hide it.
                        if (signedDateStartFilter || signedDateEndFilter) {
                            showRow = false;
                        }
                    } else {
                        // Date is expected as 'MM/DD/YYYY HH:MM AM/PM'
                        const datePart = signedDateCellText.split(' ')[0]; // Get 'MM/DD/YYYY'
                        let cellDateYYYYMMDD = '';
                        if (datePart) {
                            const parts = datePart.split('/');
                            if (parts.length === 3) { // MM, DD, YYYY
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
                            // If parsing fails or no valid date found, and a filter is active, hide row.
                            if (signedDateStartFilter || signedDateEndFilter) {
                                showRow = false;
                            }
                        }
                    }
                } else {
                    console.warn("'Date and Time Signed' column index is undefined. Cannot filter by signed date.");
                }
            }

            // Phone Number Filter (Text Includes)
            if (showRow && phoneNumberFilter && typeof phoneNumberIndex !== 'undefined') {
                const originalText = cells[phoneNumberIndex]?.textContent.trim() || '';
                const lowerText = originalText.toLowerCase();
                const comparisonResult = lowerText.includes(phoneNumberFilter);
                console.log(`[Phone Filter] Index: ${phoneNumberIndex}, Filter: '${phoneNumberFilter}', OriginalCell: '${originalText}', LowerCell: '${lowerText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            // Street Address Filter (Text Includes)
            if (showRow && streetAddressFilter && typeof streetAddressIndex !== 'undefined') {
                const originalText = cells[streetAddressIndex]?.textContent.trim() || '';
                const lowerText = originalText.toLowerCase();
                const comparisonResult = lowerText.includes(streetAddressFilter);
                console.log(`[Street Addr Filter] Index: ${streetAddressIndex}, Filter: '${streetAddressFilter}', OriginalCell: '${originalText}', LowerCell: '${lowerText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }
            
            // City Filter (Text Includes)
            if (showRow && cityFilter && typeof cityIndex !== 'undefined') {
                const originalText = cells[cityIndex]?.textContent.trim() || '';
                const lowerText = originalText.toLowerCase();
                const comparisonResult = lowerText.includes(cityFilter);
                console.log(`[City Filter] Index: ${cityIndex}, Filter: '${cityFilter}', OriginalCell: '${originalText}', LowerCell: '${lowerText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            // Zip Code Filter (Text Includes)
            if (showRow && zipCodeFilter && typeof zipCodeIndex !== 'undefined') {
                const originalText = cells[zipCodeIndex]?.textContent.trim() || '';
                const lowerText = originalText.toLowerCase();
                const comparisonResult = lowerText.includes(zipCodeFilter);
                console.log(`[Zip Code Filter] Index: ${zipCodeIndex}, Filter: '${zipCodeFilter}', OriginalCell: '${originalText}', LowerCell: '${lowerText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            // Basis of Claim Filter (Text Includes - from dedicated textbox)
            if (showRow && basisOfClaimFilter && typeof basisIndex !== 'undefined') {
                const originalText = cells[basisIndex]?.textContent.trim() || '';
                const lowerText = originalText.toLowerCase();
                const comparisonResult = lowerText.includes(basisOfClaimFilter);
                console.log(`[Basis Text Filter] Index: ${basisIndex}, Filter: '${basisOfClaimFilter}', OriginalCell: '${originalText}', LowerCell: '${lowerText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            // Nature of Injury Filter (Text Includes - from dedicated textbox)
            if (showRow && natureOfInjuryFilter && typeof injuryIndex !== 'undefined') {
                const originalText = cells[injuryIndex]?.textContent.trim() || '';
                const lowerText = originalText.toLowerCase();
                const comparisonResult = lowerText.includes(natureOfInjuryFilter);
                console.log(`[Injury Text Filter] Index: ${injuryIndex}, Filter: '${natureOfInjuryFilter}', OriginalCell: '${originalText}', LowerCell: '${lowerText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            // Capitol Experience Filter (Text Includes)
            if (showRow && capitolExperienceFilter && typeof capitolExperienceIndex !== 'undefined') {
                const originalText = cells[capitolExperienceIndex]?.textContent.trim() || '';
                const lowerText = originalText.toLowerCase();
                const comparisonResult = lowerText.includes(capitolExperienceFilter);
                console.log(`[Capitol Exp Filter] Index: ${capitolExperienceIndex}, Filter: '${capitolExperienceFilter}', OriginalCell: '${originalText}', LowerCell: '${lowerText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            // Injuries/Damages Filter (Text Includes)
            if (showRow && injuriesDamagesFilter && typeof injuriesDamagesIndex !== 'undefined') {
                const originalText = cells[injuriesDamagesIndex]?.textContent.trim() || '';
                const lowerText = originalText.toLowerCase();
                const comparisonResult = lowerText.includes(injuriesDamagesFilter);
                console.log(`[Inj/Dmg Filter] Index: ${injuriesDamagesIndex}, Filter: '${injuriesDamagesFilter}', OriginalCell: '${originalText}', LowerCell: '${lowerText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            // Entry/Exit Time Filter (Text Includes)
            if (showRow && entryExitTimeFilter && typeof entryExitTimeIndex !== 'undefined') {
                const originalText = cells[entryExitTimeIndex]?.textContent.trim() || '';
                const lowerText = originalText.toLowerCase();
                const comparisonResult = lowerText.includes(entryExitTimeFilter);
                console.log(`[Entry/Exit Filter] Index: ${entryExitTimeIndex}, Filter: '${entryExitTimeFilter}', OriginalCell: '${originalText}', LowerCell: '${lowerText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            // Inside Capitol Details Filter (Text Includes)
            if (showRow && insideCapitolDetailsFilter && typeof insideCapitolDetailsIndex !== 'undefined') {
                const originalText = cells[insideCapitolDetailsIndex]?.textContent.trim() || '';
                const lowerText = originalText.toLowerCase();
                const comparisonResult = lowerText.includes(insideCapitolDetailsFilter);
                console.log(`[Inside Detail Filter] Index: ${insideCapitolDetailsIndex}, Filter: '${insideCapitolDetailsFilter}', OriginalCell: '${originalText}', LowerCell: '${lowerText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }
            
            // Signature Filter (Dropdown Status)
            // This block needs to run BEFORE the text filter block for signature
            if (showRow && signatureStatusFilter !== 'all' && typeof signatureIndex !== 'undefined') {
                const signatureText = cells[signatureIndex]?.textContent?.trim().toLowerCase() || '';
                const isSigned = signatureText !== 'pending signature'; // Simplistic check

                if (signatureStatusFilter === 'pending' && isSigned) {
                    showRow = false; // Hide if filter is 'pending' but cell is signed
                } else if (signatureStatusFilter === 'signed' && !isSigned) {
                    showRow = false; // Hide if filter is 'signed' but cell is pending
                }
                console.log(`[Signature Status Filter] Index: ${signatureIndex}, Filter: '${signatureStatusFilter}', Cell Text: '${signatureText}', IsSigned: ${isSigned}, ShowRow After Status Check: ${showRow}`);
            }

            // Signature Filter (Text Includes - from dedicated textbox)
            if (showRow && signatureTextFilter && typeof signatureIndex !== 'undefined') {
                const originalText = cells[signatureIndex]?.textContent.trim() || '';
                const lowerText = originalText.toLowerCase();
                const comparisonResult = lowerText.includes(signatureTextFilter);
                console.log(`[Signature Text Filter] Index: ${signatureIndex}, Filter: '${signatureTextFilter}', OriginalCell: '${originalText}', LowerCell: '${lowerText}', Matches: ${comparisonResult}`);
                if (!comparisonResult) {
                    showRow = false;
                }
            }

            // Marital Status Filter (Dropdown)
            if (showRow && maritalStatusFilter && typeof maritalStatusIndex !== 'undefined') {
                const cellText = cells[maritalStatusIndex]?.textContent.trim() || '';
                if (cellText !== maritalStatusFilter) {
                    showRow = false;
                }
            }

            // Update row visibility based on the final showRow status
            const currentDisplay = row.style.display;
            const intendedDisplay = showRow ? '' : 'none';
            // console.log(`%cRow ${row.rowIndex}: Setting display to '${intendedDisplay}'. Final showRow is ${showRow}.`, showRow ? 'color: green;' : 'color: red;');
            row.style.display = intendedDisplay;
            
            // Optional: Check computed style AFTER attempting to set it (for debugging focus issues)
            // const computedDisplay = window.getComputedStyle(row).display;
            // if (!showRow && computedDisplay !== 'none') {
            //      console.error(`Row ${row.rowIndex}: FAILED TO HIDE. Inline style set to '${row.style.display}', but computed display is '${computedDisplay}'.`);
            // } else if (showRow && computedDisplay === 'none') {
            //      console.warn(`Row ${row.rowIndex}: FAILED TO SHOW. Inline style set to '${row.style.display}', but computed display is 'none'.`);
            // }
        }); // End of rows.forEach
    } // End of applyFilters function

    // --- Initial Setup ---
    // buildColumnIndexMap(); // Build column index map initially
    applyFilters(); // Apply filters on load to catch any initial default values

    // --- Event Listeners for Filters (Inputs/Selects/Checkboxes) ---
    filterNameInput?.addEventListener('input', applyFilters);
    filterStateSelect?.addEventListener('change', applyFilters);
    filterEmploymentSelect?.addEventListener('change', applyFilters);
    filterEmailInput?.addEventListener('input', applyFilters);
    filterAmountMinInput?.addEventListener('input', applyFilters);
    filterAmountMaxInput?.addEventListener('input', applyFilters);
    filterBasisDeviationCheckbox?.addEventListener('change', applyFilters);
    filterInjuryDeviationCheckbox?.addEventListener('change', applyFilters);

    // Add listeners for NEW amount filters
    filterPropDmgMinInput?.addEventListener('input', applyFilters);
    filterPropDmgMaxInput?.addEventListener('input', applyFilters);
    filterPersInjMinInput?.addEventListener('input', applyFilters);
    filterPersInjMaxInput?.addEventListener('input', applyFilters);
    filterWrongfulDeathMinInput?.addEventListener('input', applyFilters);
    filterWrongfulDeathMaxInput?.addEventListener('input', applyFilters);

    // Add listeners for created date filters
    filterCreatedStartInput?.addEventListener('change', applyFilters);
    filterCreatedEndInput?.addEventListener('change', applyFilters);

    // Add listeners for signed date filters
    filterSignedDateStartInput?.addEventListener('change', applyFilters);
    filterSignedDateEndInput?.addEventListener('change', applyFilters);

    // --- Listeners for NEW Text Filters --- 
    filterPhoneNumberInput?.addEventListener('input', applyFilters);
    filterStreetAddressInput?.addEventListener('input', applyFilters);
    filterCityInput?.addEventListener('input', applyFilters);
    filterZipCodeInput?.addEventListener('input', applyFilters);
    filterBasisOfClaimInput?.addEventListener('input', applyFilters);
    filterNatureOfInjuryInput?.addEventListener('input', applyFilters);
    filterCapitolExperienceInput?.addEventListener('input', applyFilters);
    filterInjuriesDamagesInput?.addEventListener('input', applyFilters);
    filterEntryExitTimeInput?.addEventListener('input', applyFilters);
    filterInsideCapitolDetailsInput?.addEventListener('input', applyFilters);
    filterSignatureTextInput?.addEventListener('input', applyFilters);

    // Add listeners for new dropdowns with synchronization
    filterSignatureStatusDropdown?.addEventListener('change', function() {
        const signatureStatus = this.value;
        // Sync the other dropdown if applicable
        if (signatureStatus === 'pending') {
            filterSignedDateStatusDropdown.value = 'pending_signature_via_date_col_dd';
        } else if (signatureStatus === 'signed') {
            filterSignedDateStatusDropdown.value = 'signed_via_date_col_dd';
        } else { // 'all'
             filterSignedDateStatusDropdown.value = 'all'; // Ensure it syncs back to 'all'
        }
        applyFilters();
    });

    filterSignedDateStatusDropdown?.addEventListener('change', function() {
        const signedDateStatus = this.value;
        // Sync the other dropdown if applicable
        if (signedDateStatus === 'pending_signature_via_date_col_dd') {
            filterSignatureStatusDropdown.value = 'pending';
        } else if (signedDateStatus === 'signed_via_date_col_dd') {
            filterSignatureStatusDropdown.value = 'signed';
        } else { // 'all'
             filterSignatureStatusDropdown.value = 'all'; // Ensure it syncs back to 'all'
        }
        applyFilters();
    });

    filterMaritalStatusDropdown?.addEventListener('change', applyFilters);

    // --- Sorting Logic ---
    headers.forEach(header => {
        const titleSpan = header.querySelector('.column-title'); // Find the title span
        const columnName = header.dataset.columnName; // Get columnName from the parent header

        if (titleSpan && columnName && columnName !== 'Actions') { // Only add listener if the span and columnName exist and it's not 'Actions'
            titleSpan.style.cursor = 'pointer'; // Add pointer cursor to the title only
            titleSpan.addEventListener('click', function() {
                console.log(`Sorting by column: ${columnName}`); // Log sorting action

                const isAscending = sortDirection[columnName] !== 'asc'; // Toggle direction (default to asc if undefined)

                // Get only currently visible rows for sorting
                const rows = Array.from(tbody.querySelectorAll('tr:not([style*="display: none"])'));
                if (rows.length === 0) return; // No visible rows to sort

                rows.sort((a, b) => {
                    // Find the correct cell based on the original header index mapping
                    const headerIndex = columnIndexMap[columnName];
                    if (typeof headerIndex === 'undefined') {
                         console.warn(`Sorting error: Column index for '${columnName}' not found.`);
                         return 0; // Should not happen if buildColumnIndexMap is correct
                    }

                    const aCell = a.children[headerIndex];
                    const bCell = b.children[headerIndex];

                    if (!aCell || !bCell) return 0; // Should not happen

                    const aText = aCell.textContent.trim();
                    const bText = bCell.textContent.trim();
                    let comparison = 0;

                    // Use appropriate comparison based on column type
                    if (columnName.includes('Date')) {
                        const dateA = parseDisplayDate(aText); // Use helper
                        const dateB = parseDisplayDate(bText); // Use helper
                        if (dateA && dateB) {
                            comparison = dateA - dateB;
                        } else if (dateA && !dateB) { // Sort valid dates before invalid/pending
                            comparison = -1;
                        } else if (!dateA && dateB) {
                            comparison = 1;
                        } else { // Both invalid/pending or text
                            comparison = aText.toLowerCase().localeCompare(bText.toLowerCase());
                        }
                    } else if (['Property Damage Amount', 'Personal Injury Amount', 'Wrongful Death Amount', 'Total Claim Amount'].includes(columnName)) {
                        const aNum = parseAmount(aText);
                        const bNum = parseAmount(bText);
                        if (aNum !== null && bNum !== null) {
                            comparison = aNum - bNum;
                        } else if (aNum === null && bNum !== null) { // Sort null/invalid amounts first
                            comparison = -1;
                        } else if (aNum !== null && bNum === null) {
                            comparison = 1;
                        } else { // Both null/invalid
                            comparison = 0;
                        }
                    } else { // Default: case-insensitive string comparison
                        comparison = aText.toLowerCase().localeCompare(bText.toLowerCase());
                    }

                    return isAscending ? comparison : -comparison; // Apply direction
                });

                // Update sort direction state
                sortDirection[columnName] = isAscending ? 'asc' : 'desc';

                // Reset visual indicators on other headers
                headers.forEach(h => {
                    const hColName = h.dataset.columnName;
                    if (hColName && hColName !== 'Actions') { // Check hColName exists
                        h.classList.remove('sort-asc', 'sort-desc');
                    }
                });
                // Add visual indicator to the clicked header
                header.classList.add(isAscending ? 'sort-asc' : 'sort-desc'); // Apply class to the header (th) for potential styling

                // Re-append sorted rows to the tbody
                rows.forEach(row => tbody.appendChild(row));
                console.log(`Sorting finished for ${columnName}. Direction: ${sortDirection[columnName]}`);
            });
        } else if (columnName && columnName !== 'Actions') {
            console.warn(`Could not find title span for header: ${columnName} or it's the Actions column.`);
        }
    });

    // --- Add CSS for Sorting Indicators --- 
    // Check if style already exists to prevent duplicates
    if (!document.getElementById('sorting-styles')) {
        const style = document.createElement('style');
        style.id = 'sorting-styles'; // Add ID for checking
        style.textContent = `
            .column-title[style*="cursor: pointer"]::after {
                content: '\u2195'; /* Up/Down arrow */
                display: inline-block;
                margin-left: 5px;
                opacity: 0.3;
                font-size: 0.8em;
                vertical-align: middle; /* Align arrow better */
            }
            .sort-asc .column-title[style*="cursor: pointer"]::after {
                content: '\u2191'; /* Up arrow */
                opacity: 1;
            }
            .sort-desc .column-title[style*="cursor: pointer"]::after {
                content: '\u2193'; /* Down arrow */
                opacity: 1;
            }
        `;
        document.head.appendChild(style);
        console.log("Sorting indicator styles added.");
    }

}); // End of DOMContentLoaded
