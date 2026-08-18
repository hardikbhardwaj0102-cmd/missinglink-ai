/* =========================================================
   MISSINGLINK AI
   LOCATION SEARCH
   No map required
========================================================= */


/* =========================================================
   NOMINATIM SEARCH
========================================================= */

async function searchLocation(query) {

    const url =
        "https://nominatim.openstreetmap.org/search" +
        "?format=jsonv2" +
        "&addressdetails=1" +
        "&limit=5" +
        "&countrycodes=in" +
        "&q=" +
        encodeURIComponent(query);


    const response = await fetch(
        url,
        {
            headers: {
                "Accept": "application/json"
            }
        }
    );


    if (!response.ok) {

        throw new Error(
            "Location search failed"
        );

    }


    return await response.json();

}


/* =========================================================
   CURRENT LOCATION → ADDRESS
========================================================= */

async function reverseLocation(
    latitude,
    longitude
) {

    const url =
        "https://nominatim.openstreetmap.org/reverse" +
        "?format=jsonv2" +
        "&addressdetails=1" +
        "&lat=" +
        encodeURIComponent(latitude) +
        "&lon=" +
        encodeURIComponent(longitude);


    const response = await fetch(
        url,
        {
            headers: {
                "Accept": "application/json"
            }
        }
    );


    if (!response.ok) {

        throw new Error(
            "Unable to identify location"
        );

    }


    return await response.json();

}


/* =========================================================
   LOCATION PICKER
========================================================= */

function setupLocationPicker(config) {

    const searchInput =
        document.getElementById(
            config.searchInput
        );


    const resultsBox =
        document.getElementById(
            config.resultsBox
        );


    const selectedBox =
        document.getElementById(
            config.selectedBox
        );


    const selectedName =
        document.getElementById(
            config.selectedName
        );


    const coordinatesBox =
        document.getElementById(
            config.coordinatesBox
        );


    const errorBox =
        document.getElementById(
            config.errorBox
        );


    const locationValue =
        document.getElementById(
            config.locationValue
        );


    const latitudeValue =
        document.getElementById(
            config.latitudeValue
        );


    const longitudeValue =
        document.getElementById(
            config.longitudeValue
        );


    const currentButton =
        document.getElementById(
            config.currentButton
        );


    let searchTimer = null;


    /* =====================================================
       ERROR
    ===================================================== */

    function showError(message) {

        if (!errorBox) {
            return;
        }


        errorBox.textContent =
            message;


        errorBox.classList.add(
            "active"
        );

    }


    function clearError() {

        if (!errorBox) {
            return;
        }


        errorBox.textContent =
            "";


        errorBox.classList.remove(
            "active"
        );

    }


    /* =====================================================
       CLEAR RESULTS
    ===================================================== */

    function clearResults() {

        if (resultsBox) {

            resultsBox.innerHTML =
                "";

        }

    }


    /* =====================================================
       SELECT LOCATION
    ===================================================== */

    function selectLocation(result) {

        clearError();


        const latitude =
            parseFloat(result.lat);


        const longitude =
            parseFloat(result.lon);


        const address =
            result.display_name;


        /* ================================================
           SAVE VALUES
        ================================================ */

        if (locationValue) {

            locationValue.value =
                address;

        }


        if (latitudeValue) {

            latitudeValue.value =
                latitude.toFixed(6);

        }


        if (longitudeValue) {

            longitudeValue.value =
                longitude.toFixed(6);

        }


        /* ================================================
           SEARCH FIELD
        ================================================ */

        if (searchInput) {

            searchInput.value =
                address;

        }


        /* ================================================
           SELECTED LOCATION
        ================================================ */

        if (selectedName) {

            selectedName.textContent =
                address;

        }


        if (coordinatesBox) {

            coordinatesBox.textContent =
                "Latitude: " +
                latitude.toFixed(6) +
                "  •  Longitude: " +
                longitude.toFixed(6);

        }


        if (selectedBox) {

            selectedBox.classList.add(
                "active"
            );

        }


        clearResults();

    }


    /* =====================================================
       DISPLAY SEARCH RESULTS
    ===================================================== */

    function displayResults(results) {

        clearResults();


        if (!resultsBox) {
            return;
        }


        if (
            !results ||
            results.length === 0
        ) {

            const empty =
                document.createElement(
                    "div"
                );


            empty.className =
                "location-result empty";


            empty.textContent =
                "No locations found";


            resultsBox.appendChild(
                empty
            );


            return;

        }


        results.forEach(
            function (result) {

                const item =
                    document.createElement(
                        "button"
                    );


                item.type =
                    "button";


                item.className =
                    "location-result";


                item.innerHTML = `

                    <span class="location-result-icon">
                        📍
                    </span>

                    <span class="location-result-text">

                        <strong>
                            ${escapeHtml(
                    getMainName(result)
                )}
                        </strong>

                        <small>
                            ${escapeHtml(
                    result.display_name
                )}
                        </small>

                    </span>

                `;


                item.addEventListener(
                    "click",
                    function () {

                        selectLocation(
                            result
                        );

                    }
                );


                resultsBox.appendChild(
                    item
                );

            }
        );

    }


    /* =====================================================
       SEARCH INPUT
    ===================================================== */

    if (searchInput) {

        searchInput.addEventListener(
            "input",
            function () {

                const query =
                    this.value.trim();


                clearError();


                clearTimeout(
                    searchTimer
                );


                if (
                    query.length < 3
                ) {

                    clearResults();

                    if (selectedBox) {

                        selectedBox.classList.remove(
                            "active"
                        );

                    }

                    return;

                }


                /* =========================================
                   WAIT BEFORE REQUEST
                ========================================= */

                searchTimer =
                    setTimeout(
                        async function () {

                            try {

                                resultsBox.innerHTML = `

                                    <div class="location-searching">
                                        Searching locations...
                                    </div>

                                `;


                                const results =
                                    await searchLocation(
                                        query
                                    );


                                displayResults(
                                    results
                                );

                            }

                            catch (error) {

                                console.error(
                                    error
                                );


                                clearResults();


                                showError(
                                    "Unable to search locations. Please try again."
                                );

                            }

                        },
                        700
                    );

            }
        );

    }


    /* =====================================================
       CURRENT LOCATION
    ===================================================== */

    if (currentButton) {

        currentButton.addEventListener(
            "click",
            function () {

                clearError();


                if (
                    !navigator.geolocation
                ) {

                    showError(
                        "Your browser does not support location services."
                    );

                    return;

                }


                currentButton.disabled =
                    true;


                currentButton.textContent =
                    "◎ Detecting your location...";


                navigator.geolocation.getCurrentPosition(

                    async function (position) {

                        try {

                            const latitude =
                                position.coords.latitude;


                            const longitude =
                                position.coords.longitude;


                            const result =
                                await reverseLocation(
                                    latitude,
                                    longitude
                                );


                            selectLocation({

                                lat:
                                    latitude,

                                lon:
                                    longitude,

                                display_name:
                                    result.display_name ||
                                    (
                                        latitude.toFixed(6) +
                                        ", " +
                                        longitude.toFixed(6)
                                    )

                            });

                        }

                        catch (error) {

                            console.error(
                                error
                            );


                            showError(
                                "Unable to identify your current location."
                            );

                        }

                        finally {

                            currentButton.disabled =
                                false;


                            currentButton.textContent =
                                "◎ Use My Current Location";

                        }

                    },


                    function (error) {

                        console.error(
                            error
                        );


                        let message =
                            "Unable to get your current location.";


                        if (
                            error.code ===
                            error.PERMISSION_DENIED
                        ) {

                            message =
                                "Location permission was denied. Please allow location access.";

                        }


                        if (
                            error.code ===
                            error.POSITION_UNAVAILABLE
                        ) {

                            message =
                                "Your current location is unavailable.";

                        }


                        if (
                            error.code ===
                            error.TIMEOUT
                        ) {

                            message =
                                "Location request timed out.";

                        }


                        showError(
                            message
                        );


                        currentButton.disabled =
                            false;


                        currentButton.textContent =
                            "◎ Use My Current Location";

                    },

                    {
                        enableHighAccuracy: true,

                        timeout: 10000,

                        maximumAge: 30000
                    }

                );

            }
        );

    }


    /* =====================================================
       CLICK OUTSIDE
    ===================================================== */

    document.addEventListener(
        "click",
        function (event) {

            if (
                !event.target.closest(
                    ".location-search-wrapper"
                )
            ) {

                clearResults();

            }

        }
    );

}


/* =========================================================
   MAIN NAME
========================================================= */

function getMainName(result) {

    if (
        result.address
    ) {

        return (
            result.address.amenity ||
            result.address.building ||
            result.address.road ||
            result.address.suburb ||
            result.address.city ||
            result.address.town ||
            result.address.village ||
            "Selected Location"
        );

    }


    return "Selected Location";

}


/* =========================================================
   HTML ESCAPE
========================================================= */

function escapeHtml(value) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        value || "";


    return div.innerHTML;

}


/* =========================================================
   INITIALIZE MISSING LOCATION
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        if (
            document.getElementById(
                "lastSeenLocationSearch"
            )
        ) {

            setupLocationPicker({

                searchInput:
                    "lastSeenLocationSearch",

                resultsBox:
                    "lastSeenLocationResults",

                selectedBox:
                    "lastSeenLocationSelected",

                selectedName:
                    "lastSeenLocationName",

                coordinatesBox:
                    "lastSeenCoordinates",

                errorBox:
                    "lastSeenLocationError",

                locationValue:
                    "lastSeenLocationValue",

                latitudeValue:
                    "lastSeenLatitude",

                longitudeValue:
                    "lastSeenLongitude",

                currentButton:
                    "lastSeenCurrentLocation"

            });

        }


        /* =================================================
           INITIALIZE FOUND LOCATION
        ================================================= */

        if (
            document.getElementById(
                "foundLocationSearch"
            )
        ) {

            setupLocationPicker({

                searchInput:
                    "foundLocationSearch",

                resultsBox:
                    "foundLocationResults",

                selectedBox:
                    "foundLocationSelected",

                selectedName:
                    "foundLocationName",

                coordinatesBox:
                    "foundCoordinates",

                errorBox:
                    "foundLocationError",

                locationValue:
                    "foundLocationValue",

                latitudeValue:
                    "foundLatitude",

                longitudeValue:
                    "foundLongitude",

                currentButton:
                    "foundCurrentLocation"

            });

        }

    }
);