const photoInput = document.getElementById("photoInput");

const previewImage = document.getElementById("previewImage");

const uploadBox = document.querySelector(".upload-box");

const progressBar = document.querySelector(".progress-bar");

const qualityText = document.querySelector(".ai-score p");



// ----------------------------
// Image Preview
// ----------------------------

photoInput.addEventListener("change", function () {

    const file = this.files[0];

    if (!file) return;

    previewImage.src = URL.createObjectURL(file);

    simulateAIQuality();

});



// ----------------------------
// Drag & Drop
// ----------------------------

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

    photoInput.files = e.dataTransfer.files;

    previewImage.src = URL.createObjectURL(file);

    simulateAIQuality();

});



// ----------------------------
// Fake AI Quality Score
// ----------------------------

function simulateAIQuality() {

    progressBar.style.width = "0%";

    qualityText.innerHTML = "Analyzing image...";

    let score = Math.floor(Math.random() * 18) + 82;

    setTimeout(() => {

        progressBar.style.width = score + "%";

        if (score > 95) {

            qualityText.innerHTML =
                "Excellent Photo • " + score + "% AI Match Quality";

        }

        else if (score > 90) {

            qualityText.innerHTML =
                "Very Good Photo • " + score + "% AI Match Quality";

        }

        else {

            qualityText.innerHTML =
                "Good Photo • " + score + "% AI Match Quality";

        }

    }, 800);

}



// ----------------------------
// Form Validation
// ----------------------------

const form = document.querySelector("form");

form.addEventListener("submit", function (e) {

    if (!photoInput.files.length) {

        alert("Please upload a photo.");

        e.preventDefault();

        return;

    }

});