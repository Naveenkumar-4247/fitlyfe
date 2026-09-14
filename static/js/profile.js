document.addEventListener("DOMContentLoaded", function () {

    // ============================================================
    // FITLYFE PROFILE - ELEMENTS
    // ============================================================

    const steps = document.querySelectorAll(".form-step");
    const nextBtns = document.querySelectorAll(".btn-next");
    const backBtns = document.querySelectorAll(".btn-back");

    const quoteEl = document.getElementById("profile-quote");
    const progressFill = document.getElementById("progress-fill");
    const progressDots = document.querySelectorAll(".progress-dot");

    const form = document.getElementById("profileForm");
    const nextInput = document.getElementById("profileNext");


    // ============================================================
    // CHECK REQUIRED ELEMENTS
    // ============================================================

    if (!steps.length || !form) {
        console.error("FitLyfe Profile: Required elements not found.");
        return;
    }


    // ============================================================
    // PRESERVE REDIRECT DESTINATION
    // ============================================================

    /*
     * Priority:
     *
     * 1. Existing hidden input
     * 2. URL ?next=...
     *
     * This is important for:
     *
     * /profile?next=/bmi-calculator
     *
     * and:
     *
     * /profile?next=/detail
     */

    if (nextInput) {

        const urlParams = new URLSearchParams(
            window.location.search
        );

        const urlNext = urlParams.get("next");

        /*
         * IMPORTANT FIX:
         *
         * The hidden input may EXIST but have an EMPTY value.
         *
         * Therefore we must check its VALUE,
         * not only whether the element exists.
         */

        if (
            (!nextInput.value || nextInput.value.trim() === "") &&
            urlNext
        ) {

            nextInput.value = urlNext;

            console.log(
                "FitLyfe: Redirect destination restored:",
                nextInput.value
            );
        }
    }


    // ============================================================
    // CURRENT STEP
    // ============================================================

    let currentStep = 0;


    // ============================================================
    // PROFILE QUOTES
    // ============================================================

    const quotes = [
        '"Your body achieves what your mind believes."',
        '"Discipline is the bridge between goals and achievement."',
        '"Age is just a number, strength is timeless."',
        '"Know yourself, fuel yourself."',
        '"Stand tall, live strong."',
        '"Every pound tells a story."',
        '"Consistency beats intensity."',
        '"Set goals, crush limits."'
    ];


    // ============================================================
    // UPDATE PROGRESS
    // ============================================================

    function updateProgress(index) {

        const totalSteps = steps.length;

        let progress = 0;

        if (totalSteps > 1) {
            progress = (index / (totalSteps - 1)) * 100;
        }


        // Progress bar
        if (progressFill) {
            progressFill.style.width = progress + "%";
        }


        // Progress dots
        progressDots.forEach(function (dot, dotIndex) {

            dot.classList.remove("active");
            dot.classList.remove("completed");

            if (dotIndex < index) {

                dot.classList.add("completed");

            } else if (dotIndex === index) {

                dot.classList.add("active");

            }

        });
    }


    // ============================================================
    // SHOW STEP
    // ============================================================

    function showStep(index) {

        if (index < 0) {
            index = 0;
        }

        if (index >= steps.length) {
            index = steps.length - 1;
        }

        currentStep = index;


        // Remove active class
        steps.forEach(function (step) {

            step.classList.remove("active");

        });


        // Show current step
        steps[index].classList.add("active");


        // ========================================================
        // UPDATE QUOTE
        // ========================================================

        if (quoteEl && quotes[index]) {

            quoteEl.classList.remove("quote-changing");

            void quoteEl.offsetWidth;

            quoteEl.textContent = quotes[index];

            quoteEl.classList.add("quote-changing");
        }


        // ========================================================
        // UPDATE PROGRESS
        // ========================================================

        updateProgress(index);


        // ========================================================
        // AUTO FOCUS
        // ========================================================

        const firstInput = steps[index].querySelector(
            "input, select"
        );

        if (firstInput) {

            setTimeout(function () {

                firstInput.focus();

            }, 300);
        }
    }


    // ============================================================
    // VALIDATE CURRENT STEP
    // ============================================================

    function validateCurrentStep() {

        const currentFormStep = steps[currentStep];

        if (!currentFormStep) {
            return false;
        }


        const inputs = currentFormStep.querySelectorAll(
            "input, select"
        );

        let valid = true;


        inputs.forEach(function (input) {

            if (
                input.type === "hidden" ||
                input.disabled
            ) {
                return;
            }


            if (!input.checkValidity()) {

                input.reportValidity();

                valid = false;
            }

        });


        return valid;
    }


    // ============================================================
    // NEXT BUTTONS
    // ============================================================

    nextBtns.forEach(function (button) {

        button.addEventListener("click", function (event) {

            event.preventDefault();


            if (!validateCurrentStep()) {
                return;
            }


            button.classList.remove("button-click");

            void button.offsetWidth;

            button.classList.add("button-click");


            if (currentStep < steps.length - 1) {

                currentStep++;

                showStep(currentStep);
            }

        });

    });


    // ============================================================
    // BACK BUTTONS
    // ============================================================

    backBtns.forEach(function (button) {

        button.addEventListener("click", function (event) {

            event.preventDefault();


            button.classList.remove("button-click");

            void button.offsetWidth;

            button.classList.add("button-click");


            if (currentStep > 0) {

                currentStep--;

                showStep(currentStep);
            }

        });

    });


    // ============================================================
    // FORM SUBMIT
    // ============================================================

    form.addEventListener("submit", function (event) {

        if (!validateCurrentStep()) {

            event.preventDefault();

            return;
        }


        // ========================================================
        // RESTORE NEXT VALUE ONE MORE TIME BEFORE SUBMIT
        // ========================================================

        if (nextInput) {

            const urlParams = new URLSearchParams(
                window.location.search
            );

            const urlNext = urlParams.get("next");


            /*
             * If hidden field is empty but URL has next,
             * copy it into the form before submission.
             */

            if (
                (!nextInput.value || nextInput.value.trim() === "") &&
                urlNext
            ) {

                nextInput.value = urlNext;
            }


            console.log(
                "FitLyfe profile submitting. Redirect:",
                nextInput.value || "default"
            );
        }


        // ========================================================
        // SAVE BUTTON
        // ========================================================

        const saveButton = form.querySelector(
            ".btn-profile"
        );

        if (saveButton) {

            saveButton.disabled = true;

            saveButton.innerHTML =
                '<span class="save-spinner"></span> Saving...';
        }


        /*
         * DO NOT use preventDefault().
         *
         * Flask will handle the redirect.
         */
    });


    // ============================================================
    // INPUT FOCUS EFFECT
    // ============================================================

    const formInputs = document.querySelectorAll(
        ".form-step input, .form-step select"
    );


    formInputs.forEach(function (input) {

        input.addEventListener("focus", function () {

            input.classList.add("input-focus");

        });


        input.addEventListener("blur", function () {

            input.classList.remove("input-focus");

        });

    });


    // ============================================================
    // ENTER KEY SUPPORT
    // ============================================================

    formInputs.forEach(function (input) {

        input.addEventListener("keydown", function (event) {

            if (
                event.key === "Enter" &&
                input.tagName !== "SELECT"
            ) {

                const currentStepElement =
                    steps[currentStep];

                const nextButton =
                    currentStepElement.querySelector(
                        ".btn-next"
                    );


                if (nextButton) {

                    event.preventDefault();

                    nextButton.click();
                }

            }

        });

    });


    // ============================================================
    // INITIALIZE PROFILE
    // ============================================================

    showStep(0);

});