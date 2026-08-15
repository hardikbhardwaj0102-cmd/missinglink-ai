const photoInput = document.getElementById("photoInput");

const previewImage = document.getElementById("previewImage");

const uploadBox = document.querySelector(".upload-box");

const progressBar = document.querySelector(".progress-bar");

const qualityText = document.querySelector(".ai-score p");

const statusItems = document.querySelectorAll(".status-item");


// ==============================
// Image Preview
// ==============================

photoInput.addEventListener("change", function () {

    const file = this.files[0];

    if (!file) return;

    previewImage.src = URL.createObjectURL(file);

    previewImage.style.display = "block";

    simulateAI();

});


// ==============================
// Drag & Drop
// ==============================

uploadBox.addEventListener("dragover", function (e) {

    e.preventDefault();

    uploadBox.classList.add("dragover");

});

uploadBox.addEventListener("dragleave", function () {

    uploadBox.classList.remove("dragover");

});

uploadBox.addEventListener("drop", function (e) {

    e.preventDefault();

    uploadBox.classList.remove("dragover");

    const file = e.dataTransfer.files[0];

    if (!file) return;

    const dt = new DataTransfer();

    dt.items.add(file);

    photoInput.files = dt.files;

    previewImage.src = URL.createObjectURL(file);

    previewImage.style.display = "block";

    simulateAI();

});


// ==============================
// Fake AI Analysis
// ==============================

function simulateAI() {

    progressBar.style.width = "0%";

    qualityText.innerHTML = "Analyzing image...";

    statusItems.forEach(item => {

        item.innerHTML = "⏳ Processing...";

        item.style.color = "#d1d5db";

    });

    const score = Math.floor(Math.random() * 8) + 92;

    setTimeout(() => {

        progressBar.style.width = score + "%";

        qualityText.innerHTML =
            "Excellent Photo • " + score + "% Ready for AI Matching";

        statusItems.forEach(item => {

            item.style.color = "#22c55e";

        });

    }, 1000);

}


// ==============================
// Form Validation
// ==============================

const form = document.querySelector("form");

form.addEventListener("submit", function (e) {

    if (!photoInput.files.length) {

        alert("Please upload a photo.");

        e.preventDefault();

    }

});