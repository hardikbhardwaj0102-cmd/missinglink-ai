document.addEventListener("DOMContentLoaded", function () {

    /* =========================================================
       ELEMENTS
    ========================================================= */

    const form = document.getElementById("missingReportForm");

    const photoInput = document.getElementById("photoInput");

    const previewImage = document.getElementById("previewImage");

    const uploadBox = document.getElementById("uploadBox");

    const uploadPlaceholder =
        document.getElementById("uploadPlaceholder");

    const progressBar =
        document.getElementById("progressBar");

    const qualityText =
        document.getElementById("qualityText");

    const qualityPercentage =
        document.getElementById("qualityPercentage");

    const stepCounter =
        document.getElementById("stepCounter");


    /* =========================================================
       CURRENT STEP
    ========================================================= */

    let currentStep = 1;


    /* =========================================================
       SHOW STEP
    ========================================================= */

    function showStep(stepNumber) {

        const allSteps =
            document.querySelectorAll(".wizard-step");


        allSteps.forEach(function (step) {

            step.classList.remove("active-step");

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


        /* UPDATE INDICATORS */

        for (let i = 1; i <= 3; i++) {

            const indicator =
                document.getElementById(
                    "stepIndicator" + i
                );


            if (!indicator) {
                continue;
            }


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


        /* UPDATE PROGRESS LINES */

        const lines =
            document.querySelectorAll(".step-line");


        lines.forEach(function (line, index) {

            line.classList.remove("completed");


            if (index < stepNumber - 1) {

                line.classList.add(
                    "completed"
                );

            }

        });


        /* UPDATE COUNTER */

        if (stepCounter) {

            stepCounter.textContent =
                "Step " +
                stepNumber +
                " of 3";

        }


        currentStep = stepNumber;


        /* SCROLL */

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

    }


    /* =========================================================
       VALIDATE CURRENT STEP
    ========================================================= */

    function validateStep(stepNumber) {

        const step =
            document.getElementById(
                "step" + stepNumber
            );


        if (!step) {
            return false;
        }


        /* STEP 1 PHOTO */

        if (stepNumber === 1) {

            if (!photoInput.files.length) {

                alert(
                    "Please upload a photo before continuing."
                );

                return false;

            }

        }


        /* STANDARD REQUIRED FIELDS */

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


        /* LOCATION VALIDATION */

        if (stepNumber === 2) {

            const locationValue =
                document.getElementById(
                    "lastSeenLocationValue"
                );


            if (
                !locationValue ||
                !locationValue.value.trim()
            ) {

                showLocationError(
                    "Please search and select the last seen location."
                );

                return false;

            }

        }


        return true;

    }


    /* =========================================================
       NAVIGATION BUTTONS
    ========================================================= */

    const step1Next =
        document.getElementById("step1Next");


    const step2Next =
        document.getElementById("step2Next");


    const step2Back =
        document.getElementById("step2Back");


    const step3Back =
        document.getElementById("step3Back");


    if (step1Next) {

        step1Next.addEventListener(
            "click",
            function () {

                if (validateStep(1)) {

                    showStep(2);

                }

            }
        );

    }


    if (step2Next) {

        step2Next.addEventListener(
            "click",
            function () {

                if (validateStep(2)) {

                    showStep(3);

                }

            }
        );

    }


    if (step2Back) {

        step2Back.addEventListener(
            "click",
            function () {

                showStep(1);

            }
        );

    }


    if (step3Back) {

        step3Back.addEventListener(
            "click",
            function () {

                showStep(2);

            }
        );

    }


    /* =========================================================
       PHOTO PREVIEW
    ========================================================= */

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


        const imageURL =
            URL.createObjectURL(file);


        previewImage.src =
            imageURL;


        previewImage.style.display =
            "block";


        uploadPlaceholder.style.display =
            "none";


        simulateAIQuality();

    }


    if (photoInput) {

        photoInput.addEventListener(
            "change",
            function () {

                const file =
                    this.files[0];


                handlePhoto(file);

            }
        );

    }


    /* =========================================================
       DRAG AND DROP
    ========================================================= */

    if (uploadBox) {

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

    }


    /* =========================================================
       PHOTO QUALITY
    ========================================================= */

    function simulateAIQuality() {

        progressBar.style.width =
            "0%";


        qualityText.textContent =
            "Analyzing image...";


        qualityPercentage.textContent =
            "--";


        const score =
            Math.floor(
                Math.random() * 18
            ) + 82;


        setTimeout(function () {

            progressBar.style.width =
                score + "%";


            qualityPercentage.textContent =
                score + "%";


            if (score >= 95) {

                qualityText.textContent =
                    "Excellent photo quality";

            }
            else if (score >= 90) {

                qualityText.textContent =
                    "Very good photo quality";

            }
            else {

                qualityText.textContent =
                    "Good photo quality";

            }

        }, 700);

    }


    /* =========================================================
       LAST SEEN DATE
    ========================================================= */

    const lastSeenDate =
        document.getElementById(
            "lastSeenDate"
        );


    if (lastSeenDate) {

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


        lastSeenDate.max =
            year +
            "-" +
            month +
            "-" +
            day;

    }


    /* =========================================================
       LOCATION SEARCH
       OpenStreetMap Nominatim
    ========================================================= */

    const locationSearch =
        document.getElementById(
            "lastSeenLocationSearch"
        );


    const locationResults =
        document.getElementById(
            "lastSeenLocationResults"
        );


    const locationValue =
        document.getElementById(
            "lastSeenLocationValue"
        );


    const latitudeInput =
        document.getElementById(
            "lastSeenLatitude"
        );


    const longitudeInput =
        document.getElementById(
            "lastSeenLongitude"
        );


    const locationSelected =
        document.getElementById(
            "lastSeenLocationSelected"
        );


    const locationName =
        document.getElementById(
            "lastSeenLocationName"
        );


    const coordinates =
        document.getElementById(
            "lastSeenCoordinates"
        );


    const mapPlaceholder =
        document.getElementById(
            "mapPlaceholder"
        );


    const mapSelectedInfo =
        document.getElementById(
            "mapSelectedInfo"
        );


    const mapLocationTitle =
        document.getElementById(
            "mapLocationTitle"
        );


    const mapCoordinatesText =
        document.getElementById(
            "mapCoordinatesText"
        );


    let searchTimeout;


    if (locationSearch) {

        locationSearch.addEventListener(
            "input",
            function () {

                clearTimeout(
                    searchTimeout
                );


                const query =
                    locationSearch.value.trim();


                locationResults.innerHTML =
                    "";


                if (query.length < 3) {
                    return;
                }


                searchTimeout =
                    setTimeout(
                        function () {

                            searchLocation(
                                query
                            );

                        },
                        500
                    );

            }
        );

    }


    function searchLocation(query) {

        fetch(
            "https://nominatim.openstreetmap.org/search?" +
            new URLSearchParams({
                q: query,
                format: "json",
                limit: 5
            }),
            {
                headers: {
                    "Accept":
                        "application/json"
                }
            }
        )

            .then(function (response) {

                return response.json();

            })

            .then(function (results) {

                locationResults.innerHTML =
                    "";


                if (!results.length) {

                    const empty =
                        document.createElement("div");


                    empty.className =
                        "location-result-item";


                    empty.textContent =
                        "No locations found.";


                    locationResults.appendChild(
                        empty
                    );


                    return;

                }


                results.forEach(
                    function (result) {

                        const item =
                            document.createElement(
                                "div"
                            );


                        item.className =
                            "location-result-item";


                        item.textContent =
                            result.display_name;


                        item.addEventListener(
                            "click",
                            function () {

                                selectLocation(
                                    result.display_name,
                                    result.lat,
                                    result.lon
                                );


                                locationResults.innerHTML =
                                    "";

                            }
                        );


                        locationResults.appendChild(
                            item
                        );

                    }
                );

            })

            .catch(function () {

                locationResults.innerHTML =
                    "";

                showLocationError(
                    "Unable to search for locations. Please try again."
                );

            });

    }


    /* =========================================================
       SELECT LOCATION
    ========================================================= */

    function selectLocation(
        name,
        latitude,
        longitude
    ) {

        locationValue.value =
            name;


        latitudeInput.value =
            latitude;


        longitudeInput.value =
            longitude;


        locationSearch.value =
            name;


        locationName.textContent =
            name;


        const coordinateText =
            "Latitude: " +
            Number(latitude).toFixed(6) +
            " • Longitude: " +
            Number(longitude).toFixed(6);


        coordinates.textContent =
            coordinateText;


        locationSelected.classList.add(
            "active"
        );


        if (mapPlaceholder) {

            mapPlaceholder.style.display =
                "none";

        }


        if (mapSelectedInfo) {

            mapSelectedInfo.classList.add(
                "active"
            );

        }


        if (mapLocationTitle) {

            mapLocationTitle.textContent =
                name;

        }


        if (mapCoordinatesText) {

            mapCoordinatesText.textContent =
                coordinateText;

        }


        clearLocationError();

    }


    /* =========================================================
       CURRENT LOCATION
    ========================================================= */

    const currentLocationButton =
        document.getElementById(
            "lastSeenCurrentLocation"
        );


    if (currentLocationButton) {

        currentLocationButton.addEventListener(
            "click",
            function () {

                if (!navigator.geolocation) {

                    showLocationError(
                        "Geolocation is not supported by this browser."
                    );

                    return;

                }


                currentLocationButton.disabled =
                    true;


                currentLocationButton.textContent =
                    "Getting location...";


                navigator.geolocation.getCurrentPosition(

                    function (position) {

                        const latitude =
                            position.coords.latitude;


                        const longitude =
                            position.coords.longitude;


                        reverseGeocode(
                            latitude,
                            longitude
                        );


                        currentLocationButton.disabled =
                            false;


                        currentLocationButton.innerHTML =
                            "<span>⌖</span>" +
                            "<span>Use My Current Location</span>";

                    },

                    function () {

                        showLocationError(
                            "Unable to access your current location."
                        );


                        currentLocationButton.disabled =
                            false;


                        currentLocationButton.innerHTML =
                            "<span>⌖</span>" +
                            "<span>Use My Current Location</span>";

                    }

                );

            }
        );

    }


    /* =========================================================
       REVERSE GEOCODING
    ========================================================= */

    function reverseGeocode(
        latitude,
        longitude
    ) {

        fetch(
            "https://nominatim.openstreetmap.org/reverse?" +
            new URLSearchParams({
                lat: latitude,
                lon: longitude,
                format: "json"
            }),
            {
                headers: {
                    "Accept":
                        "application/json"
                }
            }
        )

            .then(function (response) {

                return response.json();

            })

            .then(function (result) {

                const name =
                    result.display_name ||
                    "Current Location";


                selectLocation(
                    name,
                    latitude,
                    longitude
                );

            })

            .catch(function () {

                selectLocation(
                    "Current Location",
                    latitude,
                    longitude
                );

            });

    }


    /* =========================================================
       LOCATION ERROR
    ========================================================= */

    function showLocationError(message) {

        const error =
            document.getElementById(
                "lastSeenLocationError"
            );


        if (!error) {
            return;
        }


        error.textContent =
            message;


        error.classList.add(
            "active"
        );

    }


    function clearLocationError() {

        const error =
            document.getElementById(
                "lastSeenLocationError"
            );


        if (!error) {
            return;
        }


        error.textContent =
            "";


        error.classList.remove(
            "active"
        );

    }


    /* =========================================================
       FORM SUBMIT VALIDATION
    ========================================================= */

    form.addEventListener(
        "submit",
        function (event) {

            if (!validateStep(1)) {

                event.preventDefault();

                showStep(1);

                return;

            }


            if (
                !locationValue ||
                !locationValue.value.trim()
            ) {

                event.preventDefault();

                showStep(2);

                showLocationError(
                    "Please select the last seen location."
                );

                return;

            }


            const requiredReporterFields =
                document
                    .getElementById("step3")
                    .querySelectorAll(
                        "input[required]"
                    );


            for (
                const input of requiredReporterFields
            ) {

                if (!input.checkValidity()) {

                    event.preventDefault();

                    showStep(3);

                    input.reportValidity();

                    return;

                }

            }

        }
    );


    /* =========================================================
       INITIAL STATE
    ========================================================= */

    showStep(1);

});