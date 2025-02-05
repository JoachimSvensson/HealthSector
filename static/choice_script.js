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
        if (result.success) {
            alert("Dine valg ble håndtert suksessfullt!");
        }
    })
})