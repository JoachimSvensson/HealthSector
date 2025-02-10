document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("fileInput");
    const uploadBox = document.querySelector(".upload-box");
    const uploadText = uploadBox.querySelector("span");
    const uploadForm = document.getElementById("uploadForm");

    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            uploadText.textContent = `Valgt fil: ${fileInput.files[0].name}`;
        }
    });


    uploadBox.addEventListener("dragover", function (event) {
        event.preventDefault(); 
        uploadBox.classList.add("dragging");
    });


    uploadBox.addEventListener("drop", function (event) {
        event.preventDefault(); 
        uploadBox.classList.remove("dragging");

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            uploadText.textContent = `Valgt fil: ${files[0].name}`;
        }
    });

    uploadBox.addEventListener("dragleave", function () {
        uploadBox.classList.remove("dragging");
    });



    uploadForm.addEventListener("submit", function (event) {
        event.preventDefault(); 

        const file = fileInput.files[0];
        if (!file) {
            alert("Vennligst velg en fil!");
            return;
        }


        const formData = new FormData();
        formData.append("file", file);

        fetch("/api/recalculate_hospital_data", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            alert("Fil lastet opp: " + data.message);
        })
        .catch(error => {
            console.error("Feil ved opplasting:", error);
            alert("Noe gikk galt ved opplasting.");
        });
        if (response.success) {
            alert("Ny data lagret!")};
    });

});
