document.addEventListener("DOMContentLoaded", async function () { 
    
    document.getElementById("lagre").addEventListener("click", async () => {
        
        const params = {
            sykehus: document.getElementById(`sykehus`).value,
            post: document.getElementById(`post`).value
        };

        const response = await fetch('/api/go_to_main', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        const result = await response.json();
        if (result.failed) {
            alert("Venligst velg sykehus og post før du fortsetter.")
        }
        if (result.success) {
            alert("Dine valg ble håndtert suksessfullt!");
        }
    })


    document.getElementById("admin").addEventListener("click", async () => {
        
        const params = {
            sykehus: document.getElementById(`sykehus`).value,
            post: document.getElementById(`post`).value
        };

        const response = await fetch('/api/go_to_main', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        const result = await response.json();
        
        if (result.admin) {
        if (result.success) {
            alert("Velkommen Admin. Du kan nå fortsette til bemanningsverktøyet.");
        }} else {
            alert("Du er ikke admin bruker, vennligst velg sykehus og post og lagre dine valg før du fortsetter.");
        }
    })

})