document.addEventListener("DOMContentLoaded", async function () {
    const sheetSelector = document.getElementById("sheetSelector");
    const HOTtableDiv = document.getElementById("hot-container");
    const selectElement1 = document.getElementById("plan-1");
    const selectElement2 = document.getElementById("plan-2");
    const selectElementSykehus1 = document.getElementById("sykehus-1");
    const selectElementPost1 = document.getElementById("post-1");
    const selectElementSykehus2 = document.getElementById("sykehus-2");
    const selectElementPost2 = document.getElementById("post-2");
    let hot;

    try {
        const response = await fetch('/api/get_dropdown_values',{
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        const data = await response.json();

        if (data.plan && Array.isArray(data.plan)) {
            selectElement1.innerHTML = '<option value="">Velg en plan</option>';
            selectElement2.innerHTML = '<option value="">Velg en plan</option>';

            new Set(data.plan).forEach(plan => {
                const option = document.createElement("option");
                option.value = plan;
                option.textContent = plan;
                selectElement1.appendChild(option);
            });

            new Set(data.plan).forEach(plan => {
                const option = document.createElement("option");
                option.value = plan;
                option.textContent = plan;
                selectElement2.appendChild(option);
            });


        } else {
            selectElement1.innerHTML = '<option value="">Ingen planer funnet</option>';
            selectElement2.innerHTML = '<option value="">Ingen planer funnet</option>';
        }
    } catch (error) {
        console.error("Feil ved henting av data:", error);
        selectElement1.innerHTML = '<option value="">Kunne ikke laste planer</option>';
        selectElement2.innerHTML = '<option value="">Kunne ikke laste planer</option>';
    }


    try {
        const response = await fetch('/api/get_dropdown_values',{
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        const data = await response.json();

        if (data.sykehus && Array.isArray(data.sykehus)) {
            selectElementSykehus1.innerHTML = '<option value="">Velg et sykehus</option>';
            selectElementSykehus2.innerHTML = '<option value="">Velg et sykehus</option>';

            new Set(data.sykehus).forEach(sykehus => {
                const option = document.createElement("option");
                option.value = sykehus;
                option.textContent = sykehus;
                selectElementSykehus1.appendChild(option);
            });

            new Set(data.sykehus).forEach(sykehus => {
                const option = document.createElement("option");
                option.value = sykehus;
                option.textContent = sykehus;
                selectElementSykehus2.appendChild(option);
            });


        } else {
            selectElementSykehus1.innerHTML = '<option value="">Ingen sykehus funnet</option>';
            selectElementSykehus2.innerHTML = '<option value="">Ingen sykehus funnet</option>';
        }
    } catch (error) {
        console.error("Feil ved henting av data:", error);
        selectElementSykehus1.innerHTML = '<option value="">Kunne ikke laste sykehus</option>';
        selectElementSykehus2.innerHTML = '<option value="">Kunne ikke laste sykehus</option>';
    }



    try {
        const response = await fetch('/api/get_dropdown_values',{
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        const data = await response.json();

        if (data.post && Array.isArray(data.post)) {
            selectElementPost1.innerHTML = '<option value="">Velg en post</option>';
            selectElementPost2.innerHTML = '<option value="">Velg en post</option>';

            new Set(data.post).forEach(post => {
                const option = document.createElement("option");
                option.value = post;
                option.textContent = post;
                selectElementPost1.appendChild(option);
            });

            new Set(data.post).forEach(post => {
                const option = document.createElement("option");
                option.value = post;
                option.textContent = post;
                selectElementPost2.appendChild(option);
            });


        } else {
            selectElementPost1.innerHTML = '<option value="">Ingen post funnet</option>';
            selectElementPost2.innerHTML = '<option value="">Ingen post funnet</option>';
        }
    } catch (error) {
        console.error("Feil ved henting av data:", error);
        selectElementPost1.innerHTML = '<option value="">Kunne ikke laste post</option>';
        selectElementPost2.innerHTML = '<option value="">Kunne ikke laste post</option>';
    }


    function clearDisplay(side) {
        const plotImg = document.getElementById(`plot-${side}`);
        const tableDiv = document.getElementById(`table-container-${side}`);

        plotImg.style.display = "none";
        plotImg.src = "";
        tableDiv.innerHTML = "";
    }
    sheetSelector.addEventListener("click", async () => {
        const option = {sheet_name : sheetSelector.value};
        const response = await fetch('/api/get_table', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(option)
        });
        const data = await response.json();
    
        // clearDisplay();
    
        if (data.table) { 
            const tableData = data.table.data; 
            const tableHeaders = data.table.headers; 
    
            if (hot) {
                hot.destroy();
            }
    
            const Times = [
                "00:00:00.000000",
                "00:15:00.000000",
                "00:30:00.000000",
                "00:45:00.000000",
                "01:00:00.000000",
                "01:15:00.000000",
                "01:30:00.000000",
                "01:45:00.000000",
                "02:00:00.000000",
                "02:15:00.000000",
                "02:30:00.000000",
                "02:45:00.000000",
                "03:00:00.000000",
                "03:15:00.000000",
                "03:30:00.000000",
                "03:45:00.000000",
                "04:00:00.000000",
                "04:15:00.000000",
                "04:30:00.000000",
                "04:45:00.000000",
                "05:00:00.000000",
                "05:15:00.000000",
                "05:30:00.000000",
                "05:45:00.000000",
                "06:00:00.000000",
                "06:15:00.000000",
                "06:30:00.000000",
                "06:45:00.000000",
                "07:00:00.000000",
                "07:15:00.000000",
                "07:30:00.000000",
                "07:45:00.000000",
                "08:00:00.000000",
                "08:15:00.000000",
                "08:30:00.000000",
                "08:45:00.000000",
                "09:00:00.000000",
                "09:15:00.000000",
                "09:30:00.000000",
                "09:45:00.000000",
                "10:00:00.000000",
                "10:15:00.000000",
                "10:30:00.000000",
                "10:45:00.000000",
                "11:00:00.000000",
                "11:15:00.000000",
                "11:30:00.000000",
                "11:45:00.000000",
                "12:00:00.000000",
                "12:15:00.000000",
                "12:30:00.000000",
                "12:45:00.000000",
                "13:00:00.000000",
                "13:15:00.000000",
                "13:30:00.000000",
                "13:45:00.000000",
                "14:00:00.000000",
                "14:15:00.000000",
                "14:30:00.000000",
                "14:45:00.000000",
                "15:00:00.000000",
                "15:15:00.000000",
                "15:30:00.000000",
                "15:45:00.000000",
                "16:00:00.000000",
                "16:15:00.000000",
                "16:30:00.000000",
                "16:45:00.000000",
                "17:00:00.000000",
                "17:15:00.000000",
                "17:30:00.000000",
                "17:45:00.000000",
                "18:00:00.000000",
                "18:15:00.000000",
                "18:30:00.000000",
                "18:45:00.000000",
                "19:00:00.000000",
                "19:15:00.000000",
                "19:30:00.000000",
                "19:45:00.000000",
                "20:00:00.000000",
                "20:15:00.000000",
                "20:30:00.000000",
                "20:45:00.000000",
                "21:00:00.000000",
                "21:15:00.000000",
                "21:30:00.000000",
                "21:45:00.000000",
                "22:00:00.000000",
                "22:15:00.000000",
                "22:30:00.000000",
                "22:45:00.000000",
                "23:00:00.000000",
                "23:15:00.000000",
                "23:30:00.000000",
                "23:45:00.000000",
            ];
    
            const NumVals = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50'];
    
            let ColumnConfig;
    
            if (tableHeaders.length > 12) {
                ColumnConfig = [
                    {type: 'numeric'},
                    {type: 'dropdown', source: Times},
                    {type: 'dropdown', source: Times},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {}, {}, {}, {},
                ];
            } else {
                ColumnConfig = [
                    {type: 'numeric'},
                    {type: 'dropdown', source: Times},
                    {type: 'dropdown', source: Times},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {type: 'dropdown', source: NumVals},
                    {}, {},
                ];
            }
    
            hot = new Handsontable(HOTtableDiv, {
                data: tableData,
                columns: ColumnConfig,
                colHeaders: tableHeaders,
                rowHeaders: true,
                width: '100%',
                height: 400,
                stretchH: 'all',
                licenseKey: 'non-commercial-and-evaluation', // Kreves for gratisversjonen av Handsontable
                contextMenu: true,
                editor: 'text',
                allowInsertRow: true,
            });
        }
    });

    addRowButton.addEventListener('click', function () {
        hot.updateSettings({
            data: [...hot.getData(), []]  
        });
    });
    





    document.getElementById("saveChanges").addEventListener("click", async function () {
        const hotData = hot.getData();  
        const tableHeaders = hot.getColHeader();
        const formattedData = hotData.map(row => {
            let rowData = {};
            tableHeaders.forEach((header, index) => {
                rowData[header] = row[index];
            });
            return rowData;
        });
    
        const response = await fetch('/update_table', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sheet: sheetSelector.value, rows: formattedData })
        });
    
        const result = await response.json();
        if (result.success) {
            alert("Tabellen ble lagret!");
        
            try {
                const response = await fetch('/api/get_dropdown_values',{
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                });
                const data = await response.json();
        
                if (data.plan && Array.isArray(data.plan)) {
                    selectElement1.innerHTML = '<option value="">Velg en plan</option>';
                    selectElement2.innerHTML = '<option value="">Velg en plan</option>';
        
                    new Set(data.plan).forEach(plan => {
                        const option = document.createElement("option");
                        option.value = plan;
                        option.textContent = plan;
                        selectElement1.appendChild(option);
                    });
        
                    new Set(data.plan).forEach(plan => {
                        const option = document.createElement("option");
                        option.value = plan;
                        option.textContent = plan;
                        selectElement2.appendChild(option);
                    });
        
        
                } else {
                    selectElement1.innerHTML = '<option value="">Ingen planer funnet</option>';
                    selectElement2.innerHTML = '<option value="">Ingen planer funnet</option>';
                }
            } catch (error) {
                console.error("Feil ved henting av data:", error);
                selectElement1.innerHTML = '<option value="">Kunne ikke laste planer</option>';
                selectElement2.innerHTML = '<option value="">Kunne ikke laste planer</option>';
            }



            try {
                const response = await fetch('/api/get_dropdown_values',{
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                });
                const data = await response.json();
        
                if (data.sykehus && Array.isArray(data.sykehus)) {
                    selectElementSykehus1.innerHTML = '<option value="">Velg et sykehus</option>';
                    selectElementSykehus2.innerHTML = '<option value="">Velg et sykehus</option>';
        
                    new Set(data.sykehus).forEach(sykehus => {
                        const option = document.createElement("option");
                        option.value = sykehus;
                        option.textContent = sykehus;
                        selectElementSykehus1.appendChild(option);
                    });
        
                    new Set(data.sykehus).forEach(sykehus => {
                        const option = document.createElement("option");
                        option.value = sykehus;
                        option.textContent = sykehus;
                        selectElementSykehus2.appendChild(option);
                    });
        
        
                } else {
                    selectElementSykehus1.innerHTML = '<option value="">Ingen sykehus funnet</option>';
                    selectElementSykehus2.innerHTML = '<option value="">Ingen sykehus funnet</option>';
                }
            } catch (error) {
                console.error("Feil ved henting av data:", error);
                selectElementSykehus1.innerHTML = '<option value="">Kunne ikke laste sykehus</option>';
                selectElementSykehus2.innerHTML = '<option value="">Kunne ikke laste sykehus</option>';
            }
        
        
        
            try {
                const response = await fetch('/api/get_dropdown_values',{
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                });
                const data = await response.json();
        
                if (data.post && Array.isArray(data.post)) {
                    selectElementPost1.innerHTML = '<option value="">Velg en post</option>';
                    selectElementPost2.innerHTML = '<option value="">Velg en post</option>';
        
                    new Set(data.post).forEach(post => {
                        const option = document.createElement("option");
                        option.value = post;
                        option.textContent = post;
                        selectElementPost1.appendChild(option);
                    });
        
                    new Set(data.post).forEach(post => {
                        const option = document.createElement("option");
                        option.value = post;
                        option.textContent = post;
                        selectElementPost2.appendChild(option);
                    });
        
        
                } else {
                    selectElementPost1.innerHTML = '<option value="">Ingen post funnet</option>';
                    selectElementPost2.innerHTML = '<option value="">Ingen post funnet</option>';
                }
            } catch (error) {
                console.error("Feil ved henting av data:", error);
                selectElementPost1.innerHTML = '<option value="">Kunne ikke laste post</option>';
                selectElementPost2.innerHTML = '<option value="">Kunne ikke laste post</option>';
            }
        
        
        
        } else {
            alert("Feil ved lagring: " + result.message);
        }
    });





    
    function setupPlotSection(side) {
        const tidsperiode = document.getElementById(`tidsperiode-${side}`);
        const datoerDiv = document.getElementById(`datoer-${side}`);
        const plotBtn = document.getElementById(`plot-btn-${side}`);
        const plotImg = document.getElementById(`plot-${side}`);
        const tableDiv = document.getElementById(`table-container-${side}`);

        tidsperiode.addEventListener("change", () => {
            if (tidsperiode.value === "custom") {
                datoerDiv.style.display = "block";
            } else {
                datoerDiv.style.display = "none";
            }
        });

 

        plotBtn.addEventListener("click", async () => {
            const params = {
                tidsperiode: tidsperiode.value,
                dag: document.getElementById(`dag-${side}`).value,
                aggregering: document.getElementById(`aggregering-${side}`).value,
                visualiseringskolonne: document.getElementById(`visualiseringskolonne-${side}`).value,
                skift: document.getElementById(`skift-${side}`).value,
                plan: document.getElementById(`plan-${side}`).value, 
                sykehus: document.getElementById(`sykehus-${side}`).value, 
                post: document.getElementById(`post-${side}`).value, 
                start_dato: document.getElementById(`start-dato-${side}`).value,
                slutt_dato: document.getElementById(`slutt-dato-${side}`).value
            };


            try {
                const response = await fetch('/api/get_plot_data', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params)
                });
                const data = await response.json();

                clearDisplay(side); 
                if (data.failed) {
                    alert("Kombinasjonen av plan, sykehus og post finnes ikke. Velg en ny kombinasjon.");
                }
                if (data.plot) {
                    plotImg.src = `data:image/png;base64,${data.plot}`;
                    plotImg.style.display = 'block';
                }

                if (data.table) {
                    tableDiv.innerHTML = data.table;                
                }
            } catch (error) {
                console.error("Feil ved henting av data:", error);
            }
        });
    }
    setupPlotSection("1");
    setupPlotSection("2");

});
