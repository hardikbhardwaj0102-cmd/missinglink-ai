document.addEventListener("DOMContentLoaded", function () {

    /* =========================================
       ELEMENTS
    ========================================== */

    const form =
        document.getElementById(
            "foundReportForm"
        );

    const photoInput =
        document.getElementById(
            "photoInput"
        );

    const previewImage =
        document.getElementById(
            "previewImage"
        );

    const uploadBox =
        document.getElementById(
            "uploadBox"
        );

    const uploadPlaceholder =
        document.getElementById(
            "uploadPlaceholder"
        );

    const progressBar =
        document.getElementById(
            "progressBar"
        );

    const qualityText =
        document.getElementById(
            "qualityText"
        );

    const qualityPercentage =
        document.getElementById(
            "qualityPercentage"
        );

    const stepCounter =
        document.getElementById(
            "stepCounter"
        );


    /* =========================================
       CURRENT STEP
    ========================================== */

    let currentStep = 1;


    /* =========================================
       SHOW STEP
    ========================================== */

    function showStep(stepNumber) {

        const steps =
            document.querySelectorAll(
                ".wizard-step"
            );


        steps.forEach(function (step) {

            step.classList.remove(
                "active-step"
            );

        });


        const selectedStep =
            document.getElementById(
                "step" + stepNumber
            );


        if (selectedStep) {

            selectedStep.classList.add(
                "active-step"
            );

        }


        /* UPDATE STEP INDICATORS */

        for (let i = 1; i <= 3; i++) {

            const indicator =
                document.getElementById(
                    "stepIndicator" + i
                );


            indicator.classList.remove(
                "active",
                "completed"
            );


            if (i < stepNumber) {

                indicator.classList.add(
                    "completed"
                );

            }

            else if (i === stepNumber) {

                indicator.classList.add(
                    "active"
                );

            }

        }


        /* UPDATE LINES */

        const lines =
            document.querySelectorAll(
                ".step-line"
            );


        lines.forEach(function (line, index) {

            line.classList.remove(
                "completed"
            );


            if (index < stepNumber - 1) {

                line.classList.add(
                    "completed"
                );

            }

        });


        /* COUNTER */

        if (stepCounter) {

            stepCounter.textContent =
                "Step " +
                stepNumber +
                " of 3";

        }


        currentStep = stepNumber;


        window.scrollTo({

            top: 0,

            behavior: "smooth"

        });

    }


    /* =========================================
       VALIDATE STEP
    ========================================== */

    function validateStep(stepNumber) {

        const step =
            document.getElementById(
                "step" + stepNumber
            );


        if (!step) {

            return false;

        }


        /* PHOTO */

        if (stepNumber === 1) {

            if (!photoInput.files.length) {

                alert(
                    "Please upload a photo before continuing."
                );

                return false;

            }

        }


        /* REQUIRED FIELDS */

        const requiredInputs =
            step.querySelectorAll(
                "input[required], select[required], textarea[required]"
            );


        for (const input of requiredInputs) {

            if (!input.checkValidity()) {

                input.reportValidity();

                return false;

            }

        }


        /* LOCATION */

        if (stepNumber === 2) {

            const locationValue =
                document.getElementById(
                    "foundLocationValue"
                );


            if (
                !locationValue ||
                !locationValue.value.trim()
            ) {

                showLocationError(
                    "Please select the location where the person was found."
                );

                return false;

            }

        }


        return true;

    }


    /* =========================================
       BUTTONS
    ========================================== */

    document
        .getElementById("step1Next")
        .addEventListener(
            "click",
            function () {

                if (validateStep(1)) {

                    showStep(2);

                }

            }
        );


    document
        .getElementById("step2Next")
        .addEventListener(
            "click",
            function () {

                if (validateStep(2)) {

                    showStep(3);

                }

            }
        );


    document
        .getElementById("step2Back")
        .addEventListener(
            "click",
            function () {

                showStep(1);

            }
        );


    document
        .getElementById("step3Back")
        .addEventListener(
            "click",
            function () {

                showStep(2);

            }
        );


    /* =========================================
       PHOTO
    ========================================== */

    function handlePhoto(file) {

        if (!file) {
            return;
        }


        if (!file.type.startsWith("image/")) {

            alert(
                "Please select a valid image file."
            );

            return;

        }


        previewImage.src =
            URL.createObjectURL(file);


        previewImage.style.display =
            "block";


        uploadPlaceholder.style.display =
            "none";


        simulateAI();

    }


    photoInput.addEventListener(
        "change",
        function () {

            handlePhoto(
                this.files[0]
            );

        }
    );


    /* =========================================
       DRAG AND DROP
    ========================================== */

    uploadBox.addEventListener(
        "dragover",
        function (event) {

            event.preventDefault();

            uploadBox.classList.add(
                "dragover"
            );

        }
    );


    uploadBox.addEventListener(
        "dragleave",
        function () {

            uploadBox.classList.remove(
                "dragover"
            );

        }
    );


    uploadBox.addEventListener(
        "drop",
        function (event) {

            event.preventDefault();

            uploadBox.classList.remove(
                "dragover"
            );


            const file =
                event.dataTransfer.files[0];


            if (!file) {
                return;
            }


            const dataTransfer =
                new DataTransfer();


            dataTransfer.items.add(
                file
            );


            photoInput.files =
                dataTransfer.files;


            handlePhoto(file);

        }
    );


    /* =========================================
       AI QUALITY
    ========================================== */

    function simulateAI() {

        progressBar.style.width =
            "0%";


        qualityText.textContent =
            "Analyzing image...";


        qualityPercentage.textContent =
            "--";


        const score =
            Math.floor(
                Math.random() * 8
            ) + 92;


        setTimeout(function () {

            progressBar.style.width =
                score + "%";


            qualityPercentage.textContent =
                score + "%";


            qualityText.textContent =
                "Excellent photo • Ready for AI matching";

        }, 800);

    }


    /* =========================================
       FOUND DATE
    ========================================== */

    const foundDate =
        document.getElementById(
            "foundDate"
        );


    if (foundDate) {

        const today =
            new Date();


        const year =
            today.getFullYear();


        const month =
            String(
                today.getMonth() + 1
            ).padStart(
                2,
                "0"
            );


        const day =
            String(
                today.getDate()
            ).padStart(
                2,
                "0"
            );


        foundDate.max =
            year +
            "-" +
            month +
            "-" +
            day;

    }


    /* =========================================
       LOCATION ERROR
    ========================================== */

    function showLocationError(message) {

        const error =
            document.getElementById(
                "foundLocationError"
            );


        error.textContent =
            message;


        error.classList.add(
            "active"
        );

    }


    /* =========================================
       SUBMIT
    ========================================== */

    form.addEventListener(
        "submit",
        function (event) {

            if (!validateStep(1)) {

                event.preventDefault();

                showStep(1);

                return;

            }


            const locationValue =
                document.getElementById(
                    "foundLocationValue"
                );


            if (
                !locationValue.value.trim()
            ) {

                event.preventDefault();

                showStep(2);

                showLocationError(
                    "Please select the found location."
                );

                return;

            }


            const step3 =
                document.getElementById(
                    "step3"
                );


            const requiredInputs =
                step3.querySelectorAll(
                    "input[required]"
                );


            for (const input of requiredInputs) {

                if (!input.checkValidity()) {

                    event.preventDefault();

                    showStep(3);

                    input.reportValidity();

                    return;

                }

            }

        }
    );


    /* =========================================
       INITIAL
    ========================================== */

    showStep(1);

});