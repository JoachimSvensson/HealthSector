document.addEventListener("DOMContentLoaded", async function () {
    const sheetSelector = document.getElementById("sheetSelector");
    const HOTtableDiv = document.getElementById("hot-container");
    const selectElement1 = document.getElementById("plan-1");
    const selectElement2 = document.getElementById("plan-2");

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


    function clearDisplay(side) {
        const plotImg = document.getElementById(`plot-${side}`);
        const tableDiv = document.getElementById(`table-container-${side}`);

        plotImg.style.display = "none";
        plotImg.src = "";
        tableDiv.innerHTML = "";
    }

    sheetSelector.addEventListener("change", async () => {
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

            const hot = new Handsontable(HOTtableDiv, {
                data: tableData,
                columns: new Array(tableHeaders.length).fill({}),
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

            // addRowButton.addEventListener('click', function () {
            //     hot.alter('insert_row', hot.countRows());
            //     hot.render();
            // });
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
                aggregering: document.getElementById(`aggregering-${side}`).value,
                visualiseringskolonne: document.getElementById(`visualiseringskolonne-${side}`).value,
                skift: document.getElementById(`skift-${side}`).value,
                plan: document.getElementById(`plan-${side}`).value, 
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
