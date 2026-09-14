/* =========================================================
   FITLYFE BMI CALCULATOR
   Uses saved profile data from the Flask/Jinja page.

   IMPORTANT:
   - BMI formula is the same for males and females.
   - Gender affects BMR and calorie estimation.
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       ELEMENTS
    ===================================================== */

    const confirmButton =
        document.getElementById("confirmDetails");

    const buttonText =
        document.getElementById("buttonText");

    const resultSection =
        document.getElementById("resultSection");

    const profileData =
        document.getElementById("profileData");


    /* BMI */

    const bmiValue =
        document.getElementById("bmiValue");

    const bmiCategory =
        document.getElementById("bmiCategory");

    const resultTitle =
        document.getElementById("resultTitle");

    const resultDescription =
        document.getElementById("resultDescription");

    const statusText =
        document.getElementById("statusText");

    const statusBadge =
        document.getElementById("statusBadge");

    const circleProgress =
        document.getElementById("circleProgress");

    const scaleIndicator =
        document.getElementById("scaleIndicator");


    /* CALORIES */

    const maintenanceCalories =
        document.getElementById("maintenanceCalories");

    const weightLossCalories =
        document.getElementById("weightLossCalories");

    const weightGainCalories =
        document.getElementById("weightGainCalories");

    const maintenanceText =
        document.getElementById("maintenanceText");


    /* INSIGHT */

    const insightTitle =
        document.getElementById("insightTitle");

    const insightText =
        document.getElementById("insightText");


    /* =====================================================
       CHECK REQUIRED ELEMENTS
    ===================================================== */

    if (!confirmButton || !profileData) {

        console.error(
            "FitLyfe BMI Calculator: Required elements not found."
        );

        return;
    }


    /* =====================================================
       READ SAVED PROFILE DATA
    ===================================================== */

    const age =
        parseFloat(profileData.dataset.age);

    const height =
        parseFloat(profileData.dataset.height);

    const weight =
        parseFloat(profileData.dataset.weight);

    const activity =
        (profileData.dataset.activity || "")
        .toLowerCase()
        .trim();

    const goal =
        (profileData.dataset.goal || "")
        .toLowerCase()
        .trim();

    const gender =
        (profileData.dataset.gender || "")
        .toLowerCase()
        .trim();


    /* =====================================================
       NORMALIZE GENDER
       
       Supports:
       male
       female
       m
       f
       ===================================================== */

    function getGender() {

        if (
            gender === "male" ||
            gender === "m"
        ) {
            return "male";
        }

        if (
            gender === "female" ||
            gender === "f"
        ) {
            return "female";
        }

        return null;
    }


    /* =====================================================
       ACTIVITY MULTIPLIERS
    ===================================================== */

    function getActivityMultiplier(level) {

        if (!level) {
            return 1.2;
        }


        if (
            level.includes("sedentary") ||
            level.includes("low")
        ) {
            return 1.2;
        }


        if (
            level.includes("light")
        ) {
            return 1.375;
        }


        if (
            level.includes("moderate") ||
            level === "active"
        ) {
            return 1.55;
        }


        if (
            level.includes("very") ||
            level.includes("high")
        ) {
            return 1.725;
        }


        if (
            level.includes("extra")
        ) {
            return 1.9;
        }


        return 1.2;
    }


    /* =====================================================
       CALCULATE BMI

       Standard adult BMI formula:

       BMI = weight / height²

       Weight = kilograms
       Height = metres

       Gender DOES NOT change the BMI formula.
    ===================================================== */

    function calculateBMI() {

        const heightMeters =
            height / 100;


        const bmi =
            weight /
            (heightMeters * heightMeters);


        return bmi;
    }


    /* =====================================================
       GET BMI CATEGORY
    ===================================================== */

    function getBMICategory(bmi) {

        if (bmi < 18.5) {

            return {
                category: "Underweight",

                title:
                    "Below the Healthy Range",

                status:
                    "Underweight",

                description:
                    "Your BMI is below the standard healthy range. Focus on balanced nutrition, strength-building activities and healthy weight gain if appropriate.",

                insightTitle:
                    "Build strength and nourish your body",

                insightText:
                    "A balanced diet with adequate calories and protein, combined with progressive strength training, can support healthy weight development."
            };
        }


        if (bmi < 25) {

            return {
                category:
                    "Healthy Weight",

                title:
                    "You're in the Healthy Range",

                status:
                    "Healthy",

                description:
                    "Your BMI falls within the standard healthy adult range. Maintaining consistent nutrition, activity and recovery can help support your current health.",

                insightTitle:
                    "Keep building healthy habits",

                insightText:
                    "Your current BMI is within the healthy range. Focus on consistency with exercise, balanced meals, hydration and quality sleep."
            };
        }


        if (bmi < 30) {

            return {
                category:
                    "Overweight",

                title:
                    "Above the Healthy Range",

                status:
                    "Overweight",

                description:
                    "Your BMI is above the standard healthy range. Gradual changes to nutrition, physical activity and daily habits may help support healthy weight management.",

                insightTitle:
                    "Focus on gradual progress",

                insightText:
                    "A sustainable calorie deficit combined with regular physical activity can support gradual weight management. Consistency is more important than extreme changes."
            };
        }


        return {
            category:
                "Obesity",

            title:
                "Above the Standard Range",

            status:
                "Obesity",

            description:
                "Your BMI is in the obesity range according to standard adult BMI categories. Consider focusing on sustainable lifestyle changes and professional guidance where appropriate.",

            insightTitle:
                "Focus on sustainable health changes",

            insightText:
                "Prioritize sustainable nutrition, regular movement, adequate sleep and gradual progress rather than aggressive dieting."
        };
    }


    /* =====================================================
       CALCULATE BMR

       Mifflin-St Jeor Equation

       Male:
       BMR = 10W + 6.25H - 5A + 5

       Female:
       BMR = 10W + 6.25H - 5A - 161

       W = weight in kg
       H = height in cm
       A = age
    ===================================================== */

    function calculateBMR() {

        if (
            !Number.isFinite(age) ||
            age <= 0 ||

            !Number.isFinite(height) ||
            height <= 0 ||

            !Number.isFinite(weight) ||
            weight <= 0
        ) {
            return null;
        }


        const currentGender =
            getGender();


        let bmr =
            (10 * weight) +
            (6.25 * height) -
            (5 * age);


        /* ==============================
           MALE
        ============================== */

        if (currentGender === "male") {

            bmr += 5;

        }


        /* ==============================
           FEMALE
        ============================== */

        else if (currentGender === "female") {

            bmr -= 161;

        }


        /* ==============================
           GENDER NOT PROVIDED

           Use midpoint estimate.
        ============================== */

        else {

            bmr -= 78;

        }


        return bmr;
    }


    /* =====================================================
       CALCULATE DAILY CALORIES
    ===================================================== */

    function calculateCalories() {

        const bmr =
            calculateBMR();


        if (!bmr) {
            return null;
        }


        const multiplier =
            getActivityMultiplier(activity);


        const maintenance =
            Math.round(
                bmr * multiplier
            );


        /*
         * Weight loss:
         * approximately 500 kcal below maintenance.
         */

        const weightLoss =
            Math.max(
                1200,
                maintenance - 500
            );


        /*
         * Weight gain:
         * approximately 300 kcal above maintenance.
         */

        const weightGain =
            maintenance + 300;


        return {
            maintenance: maintenance,
            weightLoss: weightLoss,
            weightGain: weightGain
        };
    }


    /* =====================================================
       UPDATE BMI CIRCLE
    ===================================================== */

    function updateBMICircle(bmi) {

        if (!circleProgress) {
            return;
        }


        const circumference =
            2 * Math.PI * 96;


        /*
         * BMI scale for circle:

         * BMI 10 = 0%
         * BMI 40 = 100%
         */

        let percentage =
            (bmi - 10) / 30;


        percentage =
            Math.max(
                0,
                Math.min(
                    1,
                    percentage
                )
            );


        const offset =
            circumference -
            (circumference * percentage);


        circleProgress.style.strokeDasharray =
            circumference;


        circleProgress.style.strokeDashoffset =
            circumference;


        setTimeout(function () {

            circleProgress.style.strokeDashoffset =
                offset;

        }, 100);
    }


    /* =====================================================
       UPDATE BMI SCALE
    ===================================================== */

    function updateScale(bmi) {

        if (!scaleIndicator) {
            return;
        }


        let position;


        /*
         * BMI 10 - 18.5
         */

        if (bmi <= 18.5) {

            position =
                ((bmi - 10) / 8.5) * 25;

        }


        /*
         * BMI 18.5 - 25
         */

        else if (bmi <= 25) {

            position =
                25 +
                ((bmi - 18.5) / 6.5) * 25;

        }


        /*
         * BMI 25 - 30
         */

        else if (bmi <= 30) {

            position =
                50 +
                ((bmi - 25) / 5) * 25;

        }


        /*
         * BMI 30 - 40
         */

        else {

            position =
                75 +
                ((bmi - 30) / 10) * 25;
        }


        position =
            Math.max(
                0,
                Math.min(
                    100,
                    position
                )
            );


        setTimeout(function () {

            scaleIndicator.style.left =
                position + "%";

        }, 150);
    }


    /* =====================================================
       DISPLAY BMI RESULT
    ===================================================== */

    function displayBMI(bmi) {

        const information =
            getBMICategory(bmi);


        /* BMI number */

        if (bmiValue) {

            bmiValue.textContent =
                bmi.toFixed(1);
        }


        /* Category */

        if (bmiCategory) {

            bmiCategory.textContent =
                information.category;
        }


        /* Result title */

        if (resultTitle) {

            resultTitle.textContent =
                information.title;
        }


        /* Description */

        if (resultDescription) {

            resultDescription.textContent =
                information.description;
        }


        /* Status */

        if (statusText) {

            statusText.textContent =
                information.status;
        }


        /* Insight title */

        if (insightTitle) {

            insightTitle.textContent =
                information.insightTitle;
        }


        /* Insight text */

        if (insightText) {

            insightText.textContent =
                information.insightText;
        }


        /* Circle */

        updateBMICircle(bmi);


        /* Scale */

        updateScale(bmi);
    }


    /* =====================================================
       DISPLAY CALORIES
    ===================================================== */

    function displayCalories() {

        const calories =
            calculateCalories();


        if (!calories) {

            if (maintenanceCalories) {

                maintenanceCalories.textContent =
                    "-- kcal";
            }


            if (weightLossCalories) {

                weightLossCalories.textContent =
                    "-- kcal";
            }


            if (weightGainCalories) {

                weightGainCalories.textContent =
                    "-- kcal";
            }


            if (maintenanceText) {

                maintenanceText.textContent =
                    "Profile information required";
            }


            return;
        }


        /* Maintenance */

        if (maintenanceCalories) {

            maintenanceCalories.textContent =
                calories.maintenance.toLocaleString() +
                " kcal";
        }


        /* Weight loss */

        if (weightLossCalories) {

            weightLossCalories.textContent =
                calories.weightLoss.toLocaleString() +
                " kcal";
        }


        /* Weight gain */

        if (weightGainCalories) {

            weightGainCalories.textContent =
                calories.weightGain.toLocaleString() +
                " kcal";
        }


        /* Maintenance description */

        if (maintenanceText) {

            maintenanceText.textContent =
                calories.maintenance.toLocaleString();
        }
    }


    /* =====================================================
       UPDATE CALORIE DESCRIPTION BASED ON GENDER
    ===================================================== */

    function updateGenderCalorieInfo() {

        if (!maintenanceText) {
            return;
        }


        const currentGender =
            getGender();


        /*
         * The calorie estimate uses the
         * Mifflin-St Jeor equation.
         */

        if (currentGender === "male") {

            maintenanceText.setAttribute(
                "title",
                "Estimated using the male Mifflin-St Jeor BMR equation."
            );

        } else if (currentGender === "female") {

            maintenanceText.setAttribute(
                "title",
                "Estimated using the female Mifflin-St Jeor BMR equation."
            );

        } else {

            maintenanceText.setAttribute(
                "title",
                "Estimated using a neutral midpoint BMR estimate."
            );
        }
    }


    /* =====================================================
       SHOW RESULT
    ===================================================== */

    function showResult() {

        if (!resultSection) {
            return;
        }


        resultSection.classList.add("show");


        resultSection.setAttribute(
            "aria-hidden",
            "false"
        );


        setTimeout(function () {

            resultSection.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        }, 250);
    }


    /* =====================================================
       BUTTON CLICK
    ===================================================== */

    confirmButton.addEventListener(
        "click",
        function () {

            /*
             * BMI requires height and weight.
             *
             * Gender is NOT required for BMI.
             *
             * Gender is used for BMR and
             * calorie estimation.
             */

            if (
                !Number.isFinite(height) ||
                height <= 0
            ) {

                console.error(
                    "FitLyfe BMI: Height is missing."
                );


                alert(
                    "Height is required to calculate your BMI. Please update your height in your profile."
                );


                return;
            }


            if (
                !Number.isFinite(weight) ||
                weight <= 0
            ) {

                console.error(
                    "FitLyfe BMI: Weight is missing."
                );


                alert(
                    "Weight is required to calculate your BMI. Please update your weight in your profile."
                );


                return;
            }


            /* Disable button */

            confirmButton.disabled =
                true;


            if (buttonText) {

                buttonText.textContent =
                    "Calculating...";
            }


            /*
             * Small delay for smooth
             * loading animation.
             */

            setTimeout(function () {

                try {

                    /* ==========================
                       CALCULATE BMI
                    ========================== */

                    const bmi =
                        calculateBMI();


                    /* ==========================
                       DISPLAY BMI
                    ========================== */

                    displayBMI(bmi);


                    /* ==========================
                       DISPLAY CALORIES
                    ========================== */

                    displayCalories();


                    /* ==========================
                       UPDATE GENDER INFO
                    ========================== */

                    updateGenderCalorieInfo();


                    /* ==========================
                       SHOW RESULT
                    ========================== */

                    showResult();


                    /* ==========================
                       UPDATE BUTTON
                    ========================== */

                    if (buttonText) {

                        buttonText.textContent =
                            "BMI Details Updated";
                    }


                    /*
                     * Allow recalculation.
                     */

                    setTimeout(function () {

                        confirmButton.disabled =
                            false;


                        if (buttonText) {

                            buttonText.textContent =
                                "Get My BMI Details";
                        }

                    }, 1500);


                } catch (error) {

                    console.error(
                        "FitLyfe BMI calculation error:",
                        error
                    );


                    confirmButton.disabled =
                        false;


                    if (buttonText) {

                        buttonText.textContent =
                            "Get My BMI Details";
                    }


                    alert(
                        "Unable to calculate your BMI. Please check your saved profile details."
                    );
                }

            }, 500);

        }
    );


    /* =====================================================
       INITIAL STATE
       
       We intentionally do NOT calculate automatically.
       
       User must click:
       "Get My BMI Details"
    ===================================================== */

});