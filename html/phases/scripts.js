$(document).ready(function () {
    function fetchDataAndUpdateTable(url, blocksRange) {
        $.ajax({
            url: url,
            dataType: 'json',
            cache: false,
            success: function (jsonData) {
                var tableData = [];
                var validatorsToDisplay = jsonData.validators;
                validatorsToDisplay.forEach(function (validator, index) {
                    var totalActiveBlocks = validator.total_signed_blocks + validator.total_missed_blocks;

                    if (totalActiveBlocks < 9000) {
                        return;
                    }
                    if (totalActiveBlocks > 0) {
                        var validatorUptime = (validator.total_signed_blocks / totalActiveBlocks * 100).toFixed(2);
                        var oracleUptime = (validator.total_oracle_votes / totalActiveBlocks * 100).toFixed(2);
                    } else {
                        var validatorUptime = 0.00;
                        var oracleUptime = 0.00;
                    }
                    validatorUptime = parseFloat(validatorUptime);
                    oracleUptime = parseFloat(oracleUptime);

                    var totalJails = validator.slashing_info ? validator.slashing_info.length : 0;
                    var tombstoned = validator.tombstoned !== null ? validator.tombstoned ? 'True' : 'False' : 'False';

                    tableData.push([
                        index + 1,
                        validator.moniker,
                        validatorUptime,
                        totalActiveBlocks,
                        validator.total_signed_blocks,
                        validator.total_missed_blocks,
                        validator.total_proposed_blocks,
                        oracleUptime,
                        validator.total_oracle_votes,
                        validator.total_missed_oracle_votes,
                        totalJails,
                        tombstoned,
                        validator.valoper,
                    ]);
                });

                var table = $('#metrics').DataTable({
                    data: tableData,
                    destroy: true,
                    lengthMenu: [[1000], [1000]],
                    order: [],
                    rowCallback: function (row, data, index) {
                        $('td:eq(0)', row).html(index + 1);

                        // Apply color to "Tombstoned" column text
                        var tombstoned = data[11];
                        if (tombstoned === 'True') {
                            $('td:eq(11)', row).html('<span style="color: red;">' + tombstoned + '</span>');
                        } else {
                            $('td:eq(11)', row).html('<span style="color: green;">' + tombstoned + '</span>');
                        }

                        var totalJails = data[10];
                        if (totalJails === 0) {
                            $('td:eq(10)', row).html('<span style="color: green;">' + totalJails + '</span>');
                        } else {
                            $('td:eq(10)', row).html('<span style="color: red;">' + totalJails + '</span>');
                        }
                    },
                    columnDefs: [
                        { targets: [12], orderable: false },
                        { targets: [0], orderable: false }
                    ]
                });

                // Add cursor pointer class on hover for specific cells
                var cellIndices = [1, 10];
                $('#metrics tbody').on('mouseenter mouseleave', '> tr > td', function() {
                    var index = $(this).index(); // Get the 0-based index of the current td
            
                    // Check if the current td index is in the cellIndices array
                    if (cellIndices.includes(index)) {
                        $(this).toggleClass('cursor-pointer');
                    }
                });

                // Initialize variable to store the currently shown row
                var currentShownRow = null;

                // Event listener for 'Moniker' cell to show details
                $('#metrics tbody').on('click', 'td:nth-child(2)', function () {
                    var tr = $(this).closest('tr');
                    var row = table.row(tr);

                    // Close current shown row if it's different from the clicked row
                    if (currentShownRow !== null && currentShownRow.index() !== row.index()) {
                        currentShownRow.child.hide();
                        $(currentShownRow.node()).removeClass('shown');
                    }

                    if (row.child.isShown()) {
                        // This row is already open - close it
                        row.child.hide();
                        tr.removeClass('shown');
                        currentShownRow = null;
                    } else {
                        // Open this row to show detailed information
                        var validatorIndex = row.index();
                        var validatorDetails = validatorsToDisplay[validatorIndex];

                        // Construct HTML for the details
                        var detailsHtml = '<div class="details-container">';
                        detailsHtml += '<p><strong>Moniker:</strong> ' + validatorDetails.moniker + '</p>';
                        detailsHtml += '<p><strong>Valoper:</strong> ' + validatorDetails.valoper + '</p>';
                        detailsHtml += '<p><strong>Consensus Pub Key:</strong> ' + validatorDetails.consensus_pubkey + '</p>';
                        detailsHtml += '<p><strong>Wallet:</strong> ' + validatorDetails.wallet + '</p>';
                        detailsHtml += '<p><strong>Valcons:</strong> ' + validatorDetails.valcons + '</p>';
                        detailsHtml += '</div>';

                        row.child(detailsHtml).show();
                        tr.addClass('shown');
                        currentShownRow = row;
                    }
                });
                
                // Event listener for 'Total Jails' cell
                $('#metrics tbody').on('click', 'td:nth-child(11)', function () {
                    var tr = $(this).closest('tr');
                    var row = table.row(tr);

                    // Close current shown row if it's different from the clicked row
                    if (currentShownRow !== null && currentShownRow.index() !== row.index()) {
                        currentShownRow.child.hide();
                        $(currentShownRow.node()).removeClass('shown');
                    }

                    if (row.child.isShown()) {
                        // This row is already open - close it
                        row.child.hide();
                        tr.removeClass('shown');
                        currentShownRow = null;
                    } else {
                        // Open this row to show slashing info details
                        var validatorIndex = row.index();
                        var slashingInfo = validatorsToDisplay[validatorIndex].slashing_info;

                        // Check if slashingInfo is defined and not null
                        if (slashingInfo && slashingInfo.length > 0) {
                            // Construct HTML for the details
                            var detailsHtml = '<table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;">';
                            detailsHtml += '<tr><th>Height</th><th>Time</th></tr>';

                            // Iterate over the slashing info
                            slashingInfo.forEach(function (info) {
                                var height = info.height;
                                var time = info.time;
                                detailsHtml += '<tr><td>' + height + '</td><td>' + time + '</td></tr>';
                            });

                            detailsHtml += '</table>';

                            // Show the details in a child row
                            row.child(detailsHtml).show();
                            tr.addClass('shown');
                            currentShownRow = row;
                        }
                    }
                });

                // Update blocks range
                $('#blocks-range').text(blocksRange);
            }
        });
    }

    // Event listeners for buttons
    $('.btn').on('click', function () {
        $('.btn').removeClass('active');
        $(this).addClass('active');
    });

    $('#phase-1').on('click', function () {
        fetchDataAndUpdateTable('phase-1-1203400-1401420.json', '1203400-1401420');
    });

    $('#phase-2').on('click', function () {
        fetchDataAndUpdateTable('phase-2-1401576-1622269.json', '1401576-1622269');
    });

    $('#phase-3').on('click', function () {
        fetchDataAndUpdateTable('phase-3-1622244-1836806.json', '1622244-1836806');
    });

    $('#phase-4').on('click', function () {
        fetchDataAndUpdateTable('phase-4-1836783-2051358.json', '1836783-2051358');
    });

    // Initial load
    fetchDataAndUpdateTable('phase-1-1203400-1401420.json', '1203400-1401420');
});