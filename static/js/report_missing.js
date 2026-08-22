/* =========================================================
   MissingLink AI
   Report Missing - Multi Step Wizard
========================================================= */


/* =========================================================
   ELEMENTS
========================================================= */

const form =
    document.getElementById("missingReportForm");

const photoInput =
    document.getElementById("photoInput");

const previewImage =
    document.getElementById("previewImage");

const uploadBox =
    document.querySelector(".upload-box");

const progressBar =
    document.querySelector(".progress-bar");

const qualityText =
    document.querySelector(".ai-quality-text");

const reviewImage =
    document.getElementById("reviewImage");



/* =========================================================
   CURRENT STEP
========================================================= */

let currentStep = 1;

const totalSteps = 4;



/* =========================================================
   STEP ELEMENTS
========================================================= */

const steps =
    document.querySelectorAll(".wizard-step");

const progressSteps =
    document.querySelectorAll(".progress-step");

const progressLineFill =
    document.getElementById(
        "progressLineFill"
    );



/* =========================================================
   SHOW STEP
========================================================= */

function showStep(stepNumber) {

    currentStep = stepNumber;


    /* ================================================
       CONTENT
    ================================================ */

    steps.forEach(function (step) {

        const stepValue =
            Number(
                step.dataset.step
            );

        step.classList.toggle(
            "active",
            stepValue === stepNumber
        );

    });


    /* ================================================
       PROGRESS
    ================================================ */

    progressSteps.forEach(function (step) {

        const stepValue =
            Number(
                step.dataset.step
            );


        step.classList.remove(
            "active"
        );

        step.classList.remove(
            "completed"
        );


        if (stepValue === stepNumber) {

            step.classList.add(
                "active"
            );

        }


        if (stepValue < stepNumber) {

            step.classList.add(
                "completed"
            );

        }

    });


    /* ================================================
       PROGRESS LINE
    ================================================ */

    const progressPercentage =
        ((stepNumber - 1) / (totalSteps - 1)) * 100;


    if (progressLineFill) {

        progressLineFill.style.width =
            progressPercentage + "%";

    }


    /* ================================================
       UPDATE REVIEW
    ================================================ */

    if (stepNumber === 4) {

        updateReview();

    }


    /* ================================================
       SCROLL
    ================================================ */

    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

}



/* =========================================================
   GET FIELD VALUE
========================================================= */

function getValue(id) {

    const element =
        document.getElementById(id);

    if (!element) {

        return "";

    }

    return element.value.trim();

}



/* =========================================================
   VALIDATE STEP
========================================================= */

function validateStep(stepNumber) {

    const step =
        document.querySelector(
            `.wizard-step[data-step="${stepNumber}"]`
        );


    if (!step) {

        return true;

    }


    const requiredFields =
        step.querySelectorAll(
            "input[required], select[required], textarea[required]"
        );


    for (
        const field
        of requiredFields
    ) {

        if (!field.checkValidity()) {

            field.reportValidity();

            return false;

        }

    }


    /* ================================================
       LOCATION VALIDATION
    ================================================ */

    if (stepNumber === 2) {

        const location =
            document.getElementById(
                "lastSeenLocationValue"
            );

        const latitude =
            document.getElementById(
                "lastSeenLatitude"
            );

        const longitude =
            document.getElementById(
                "lastSeenLongitude"
            );


        if (
            !location ||
            !location.value.trim()
        ) {

            alert(
                "Please select the last seen location before continuing."
            );

            return false;

        }


        if (
            !latitude ||
            !latitude.value ||
            !longitude ||
            !longitude.value
        ) {

            alert(
                "Please select a location from the suggestions so its coordinates can be captured."
            );

            return false;

        }

    }


    return true;

}



/* =========================================================
   NEXT BUTTONS
========================================================= */

document
    .querySelectorAll("[data-next]")
    .forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                const nextStep =
                    Number(
                        this.dataset.next
                    );


                if (
                    validateStep(
                        currentStep
                    )
                ) {

                    showStep(
                        nextStep
                    );

                }

            }
        );

    });



/* =========================================================
   BACK BUTTONS
========================================================= */

document
    .querySelectorAll("[data-back]")
    .forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                const backStep =
                    Number(
                        this.dataset.back
                    );


                showStep(
                    backStep
                );

            }
        );

    });



/* =========================================================
   EDIT BUTTONS
========================================================= */

document
    .querySelectorAll("[data-edit]")
    .forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                const editStep =
                    Number(
                        this.dataset.edit
                    );


                showStep(
                    editStep
                );

            }
        );

    });



/* =========================================================
   IMAGE PREVIEW
========================================================= */

if (photoInput) {

    photoInput.addEventListener(
        "change",
        function () {

            const file =
                this.files[0];


            if (!file) {

                return;

            }


            if (
                !file.type.startsWith(
                    "image/"
                )
            ) {

                alert(
                    "Please select a valid image file."
                );

                this.value = "";

                return;

            }


            const imageURL =
                URL.createObjectURL(
                    file
                );


            if (previewImage) {

                previewImage.src =
                    imageURL;

            }


            if (reviewImage) {

                reviewImage.src =
                    imageURL;

            }


            simulateAIQuality();

        }
    );

}



/* =========================================================
   DRAG & DROP
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


            const files =
                event.dataTransfer.files;


            if (
                !files ||
                !files.length
            ) {

                return;

            }


            const file =
                files[0];


            if (
                !file.type.startsWith(
                    "image/"
                )
            ) {

                alert(
                    "Please drop a valid image file."
                );

                return;

            }


            try {

                photoInput.files =
                    files;

            }

            catch (error) {

                console.error(
                    "Unable to assign dropped file:",
                    error
                );

            }


            const imageURL =
                URL.createObjectURL(
                    file
                );


            if (previewImage) {

                previewImage.src =
                    imageURL;

            }


            if (reviewImage) {

                reviewImage.src =
                    imageURL;

            }


            simulateAIQuality();

        }
    );

}



/* =========================================================
   AI PHOTO QUALITY SIMULATION
========================================================= */

function simulateAIQuality() {

    if (!progressBar || !qualityText) {

        return;

    }


    progressBar.style.width =
        "0%";


    qualityText.textContent =
        "Analyzing image...";


    const score =
        Math.floor(
            Math.random() * 18
        ) + 82;


    setTimeout(
        function () {

            progressBar.style.width =
                score + "%";


            if (score > 95) {

                qualityText.textContent =
                    "Excellent Photo • " +
                    score +
                    "% AI Match Quality";

            }

            else if (score > 90) {

                qualityText.textContent =
                    "Very Good Photo • " +
                    score +
                    "% AI Match Quality";

            }

            else {

                qualityText.textContent =
                    "Good Photo • " +
                    score +
                    "% AI Match Quality";

            }

        },
        800
    );

}



/* =========================================================
   FORMAT DATE
========================================================= */

function formatDate(dateValue) {

    if (!dateValue) {

        return "Not provided";

    }


    const date =
        new Date(
            dateValue + "T00:00:00"
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return dateValue;

    }


    return date.toLocaleDateString(
        "en-IN",
        {
            day: "numeric",
            month: "short",
            year: "numeric"
        }
    );

}



/* =========================================================
   SAFE DISPLAY
========================================================= */

function displayOrDash(value) {

    if (
        value === null ||
        value === undefined ||
        String(value).trim() === ""
    ) {

        return "Not provided";

    }


    return value;

}



/* =========================================================
   UPDATE REVIEW
========================================================= */

function updateReview() {

    const name =
        getValue("name");

    const age =
        getValue("age");

    const gender =
        getValue("gender");

    const height =
        getValue("height");

    const clothing =
        getValue("clothing");


    const date =
        getValue("lastSeenDate");

    const location =
        getValue(
            "lastSeenLocationValue"
        );

    const latitude =
        getValue(
            "lastSeenLatitude"
        );

    const longitude =
        getValue(
            "lastSeenLongitude"
        );


    const reporter =
        getValue("reporterName");

    const relationship =
        getValue("relationship");

    const phone =
        getValue("phone");

    const email =
        getValue("email");


    /* ================================================
       PERSON
    ================================================ */

    setText(
        "reviewName",
        displayOrDash(name)
    );


    setText(
        "reviewAge",
        age
            ? age + " years"
            : "Not provided"
    );


    setText(
        "reviewGender",
        displayOrDash(gender)
    );


    setText(
        "reviewHeight",
        displayOrDash(height)
    );


    setText(
        "reviewClothing",
        displayOrDash(clothing)
    );


    /* ================================================
       HEADER
    ================================================ */

    setText(
        "reviewPersonName",
        displayOrDash(name)
    );


    let basicInfo = "";


    if (age) {

        basicInfo +=
            age + " years";

    }


    if (gender) {

        if (basicInfo) {

            basicInfo +=
                " • ";

        }


        basicInfo +=
            gender;

    }


    setText(
        "reviewPersonBasic",
        basicInfo ||
        "Personal details not provided"
    );


    /* ================================================
       LAST SEEN
    ================================================ */

    setText(
        "reviewDate",
        formatDate(date)
    );


    setText(
        "reviewLocation",
        displayOrDash(location)
    );


    let coordinates =
        "Not provided";


    if (
        latitude &&
        longitude
    ) {

        coordinates =
            latitude +
            " • " +
            longitude;

    }


    setText(
        "reviewCoordinates",
        coordinates
    );


    /* ================================================
       REPORTER
    ================================================ */

    setText(
        "reviewReporter",
        displayOrDash(reporter)
    );


    setText(
        "reviewRelationship",
        displayOrDash(relationship)
    );


    setText(
        "reviewPhone",
        displayOrDash(phone)
    );


    setText(
        "reviewEmail",
        displayOrDash(email)
    );


    /* ================================================
       IMAGE
    ================================================ */

    if (
        photoInput &&
        photoInput.files &&
        photoInput.files[0]
    ) {

        const imageURL =
            URL.createObjectURL(
                photoInput.files[0]
            );


        if (reviewImage) {

            reviewImage.src =
                imageURL;

        }

    }

}



/* =========================================================
   SET TEXT
========================================================= */

function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {

        return;

    }


    element.textContent =
        value;

}



/* =========================================================
   FORM SUBMIT
========================================================= */

if (form) {

    form.addEventListener(
        "submit",
        function (event) {

            /* ============================================
               FINAL VALIDATION
            ============================================ */

            if (
                !validateStep(1) ||
                !validateStep(2) ||
                !validateStep(3)
            ) {

                event.preventDefault();

                return;

            }


            if (
                !photoInput ||
                !photoInput.files.length
            ) {

                alert(
                    "Please upload a photo."
                );

                event.preventDefault();

                showStep(1);

                return;

            }


            /* ============================================
               LOCATION CHECK
            ============================================ */

            const location =
                document.getElementById(
                    "lastSeenLocationValue"
                );


            if (
                !location ||
                !location.value.trim()
            ) {

                alert(
                    "Please select the last seen location."
                );

                event.preventDefault();

                showStep(2);

                return;

            }


            /* ============================================
               SUBMIT STATE
            ============================================ */

            const submitButton =
                document.getElementById(
                    "submitReportBtn"
                );


            if (submitButton) {

                submitButton.disabled =
                    true;


                submitButton.innerHTML =
                    `
                    <span class="submit-spinner"></span>
                    Submitting...
                    `;

            }

        }
    );

}



/* =========================================================
   LAST SEEN DATE
   Only allow dates before today
========================================================= */

const lastSeenDate =
    document.getElementById(
        "lastSeenDate"
    );


if (lastSeenDate) {

    const yesterday =
        new Date();


    yesterday.setDate(
        yesterday.getDate() - 1
    );


    const year =
        yesterday.getFullYear();


    const month =
        String(
            yesterday.getMonth() + 1
        ).padStart(
            2,
            "0"
        );


    const day =
        String(
            yesterday.getDate()
        ).padStart(
            2,
            "0"
        );


    lastSeenDate.max =
        `${year}-${month}-${day}`;

}



/* =========================================================
   INITIALIZE
========================================================= */

showStep(1);