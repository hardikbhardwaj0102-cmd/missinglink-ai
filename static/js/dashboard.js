// ===============================
// MissingLink AI Loader
// ===============================

document.addEventListener("DOMContentLoaded", () => {

    const steps = [
        " Uploading image...",
        " Detecting face...",
        " Generating face embedding...",
        " Searching database...",
        " Calculating similarity...",
        " Preparing results..."
    ];

    const links = document.querySelectorAll(".ai-loader-link");

    links.forEach(link => {

        link.addEventListener("click", function (e) {

            e.preventDefault();

            const loader = document.getElementById("aiLoader");
            const loaderText = document.getElementById("loaderText");
            const progressBar = document.getElementById("progressBar");

            if (!loader || !loaderText || !progressBar) {
                window.location.href = link.href;
                return;
            }

            loader.classList.add("show");

            let currentStep = 0;

            function updateLoader() {

                loaderText.textContent = steps[currentStep];

                const progress = ((currentStep + 1) / steps.length) * 100;
                progressBar.style.width = progress + "%";

                currentStep++;

                if (currentStep < steps.length) {

                    setTimeout(updateLoader, 500);

                } else {

                    setTimeout(() => {

                        window.location.href = link.href;

                    }, 600);
                }
            }

            updateLoader();

        });

    });

});