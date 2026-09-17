/* =========================================================
   FITLYFE — AI WORKOUT STUDIO
   Gemini-powered workout generation
   ---------------------------------------------------------
   Frontend responsibilities:
   • Collect user's workout focus
   • Call Flask /api/workout/generate
   • Render AI-generated workout
   • Handle regeneration
   • Handle training split / muscle selection
   • Never pretend browser history is the source of truth

   Backend responsibilities:
   • User authentication
   • Profile validation
   • Gemini generation
   • Workout variation
   • Generation numbering
   • Database persistence
   • Previous-workout history
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    /* =====================================================
       ELEMENT HELPERS
       ===================================================== */

    const $ = (id) => document.getElementById(id);

    const workoutInput = $("workoutInput");
    const generateButton = $("generateButton");

    const splitCard = $("splitCard");
    const targetCard = $("targetCard");

    const splitSection = $("splitSection");
    const targetSection = $("targetSection");

    const closeSplit = $("closeSplit");
    const closeTarget = $("closeTarget");

    const loadingSection = $("loadingSection");
    const resultSection = $("resultSection");
    const welcomeSection = $("welcomeSection");

    const resultTitle = $("resultTitle");
    const resultDescription = $("resultDescription");

    const exerciseCount = $("exerciseCount");
    const setCount = $("setCount");

    const workoutIntensity = $("workoutIntensity");
    const workoutDuration = $("workoutDuration");

    const exerciseList = $("exerciseList");

    const regenerateButton = $("regenerateButton");
    const newWorkoutButton = $("newWorkoutButton");


    /* =====================================================
       STATE
       ===================================================== */

    let currentWorkoutKey = null;
    let currentFocus = null;

    /*
       This is only UI state.

       The backend/database remains authoritative for:
       • generation number
       • previous workouts
       • variation
       • persistence
    */
    let generationNumber = 0;

    let currentWorkout = null;

    let isGenerating = false;

    let generationTimer = null;


    /* =====================================================
       NORMALIZE TEXT
       ===================================================== */

    function normalizeText(value) {
        return String(value || "")
            .trim()
            .toLowerCase()
            .replace(/[_-]+/g, " ")
            .replace(/\s+/g, " ");
    }


    /* =====================================================
       FIND TRAINING FOCUS
       ===================================================== */

    function findWorkout(value) {
        const text = normalizeText(value);

        if (!text) {
            return null;
        }

        /*
           Check compound workout types first.
        */

        if (
            text.includes("full body") ||
            text.includes("fullbody") ||
            text.includes("whole body")
        ) {
            return "Full Body";
        }

        if (text.includes("push")) {
            return "Push";
        }

        if (text.includes("pull")) {
            return "Pull";
        }

        if (text.includes("chest")) {
            return "Chest";
        }

        if (text.includes("lat")) {
            return "Lats";
        }

        if (text.includes("back")) {
            return "Back";
        }

        if (text.includes("shoulder")) {
            return "Shoulders";
        }

        if (text.includes("bicep")) {
            return "Biceps";
        }

        if (text.includes("tricep")) {
            return "Triceps";
        }

        if (text.includes("leg")) {
            return "Legs";
        }

        if (text.includes("glute")) {
            return "Glutes";
        }

        if (text.includes("forearm")) {
            return "Forearms";
        }

        if (
            text.includes("core") ||
            text.includes("abs") ||
            text.includes("abdominal")
        ) {
            return "Core";
        }

        return null;
    }


    /* =====================================================
       HIDE ELEMENT
       ===================================================== */

    function hideElement(element) {
        if (!element) {
            return;
        }

        element.classList.add("hidden");
    }


    /* =====================================================
       SHOW ELEMENT
       ===================================================== */

    function showElement(element) {
        if (!element) {
            return;
        }

        element.classList.remove("hidden");
    }


    /* =====================================================
       SCROLL TO ELEMENT
       ===================================================== */

    function scrollToElement(element) {
        if (!element) {
            return;
        }

        window.setTimeout(() => {
            element.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }, 80);
    }


    /* =====================================================
       CLOSE SELECTION PANELS
       ===================================================== */

    function closeSelections() {
        hideElement(splitSection);
        hideElement(targetSection);
    }


    /* =====================================================
       CLEAR GENERATION TIMER
       ===================================================== */

    function clearGenerationTimer() {
        if (generationTimer) {
            clearTimeout(generationTimer);
            generationTimer = null;
        }
    }


    /* =====================================================
       RESET WORKOUT SESSION
       ===================================================== */

    function resetWorkoutSession() {
        clearGenerationTimer();

        generationNumber = 0;

        currentWorkout = null;
        currentWorkoutKey = null;
        currentFocus = null;

        hideElement(resultSection);
        hideElement(loadingSection);

        showElement(welcomeSection);

        if (exerciseList) {
            exerciseList.innerHTML = "";
        }

        updateLoadingText(
            "Building your personalized workout..."
        );
    }


    /* =====================================================
       BUILD API REQUEST
       ===================================================== */

    function buildRequest(focus) {
        /*
           IMPORTANT:

           Do NOT send:
           • generation_number
           • previous_workouts

           The Flask backend already calculates those
           from the authenticated user's database history.

           This prevents the browser from becoming a
           second source of truth.
        */

        return {
            focus: focus,

            workout_type: "gym",

            equipment: "gym",

            duration: 60,

            fitness_level: "moderate"
        };
    }


    /* =====================================================
       SET GENERATING UI STATE
       ===================================================== */

    function setGeneratingState(generating) {
        isGenerating = generating;

        if (generateButton) {
            generateButton.disabled = generating;

            generateButton.setAttribute(
                "aria-busy",
                generating ? "true" : "false"
            );

            if (generating) {
                generateButton.classList.add("is-loading");
            } else {
                generateButton.classList.remove("is-loading");
            }
        }

        if (regenerateButton) {
            regenerateButton.disabled = generating;
        }

        /*
           Keep selection buttons from firing multiple
           simultaneous AI requests.
        */

        document
            .querySelectorAll(
                ".quick-tag, .muscle-button, .split-option"
            )
            .forEach((button) => {
                button.disabled = generating;
            });
    }


    /* =====================================================
       GENERATE WORKOUT
       ===================================================== */

    async function generateWorkout(workoutKey, options = {}) {
        if (isGenerating) {
            return;
        }

        const isRegeneration =
            options.regenerate === true;

        const focus =
            workoutKey || "Full Body";

        currentWorkoutKey = focus;
        currentFocus = focus;

        setGeneratingState(true);

        closeSelections();

        hideElement(welcomeSection);
        hideElement(resultSection);

        showElement(loadingSection);

        updateLoadingText(
            isRegeneration
                ? "Creating a fresh workout..."
                : "Building your personalized workout..."
        );

        scrollToElement(loadingSection);

        const requestData =
            buildRequest(focus);

        try {
            /*
               ------------------------------------------------
               MAIN AI REQUEST
               ------------------------------------------------
            */

            const response = await fetch(
                "/api/workout/generate",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    credentials: "same-origin",

                    body:
                        JSON.stringify(
                            requestData
                        )
                }
            );

            /*
               ------------------------------------------------
               Parse server response safely
               ------------------------------------------------
            */

            let data = null;

            try {
                data = await response.json();
            } catch (jsonError) {
                console.error(
                    "Workout JSON parse error:",
                    jsonError
                );

                throw new Error(
                    "The server returned an invalid response."
                );
            }

            /*
               ------------------------------------------------
               Server error
               ------------------------------------------------
            */

            if (
                !response.ok ||
                !data ||
                data.success !== true
            ) {
                throw new Error(
                    data?.error ||
                    data?.message ||
                    `Unable to generate workout (${response.status}).`
                );
            }

            /*
               ------------------------------------------------
               Extract workout
               ------------------------------------------------
            */

            const workout =
                data.workout;

            if (
                !workout ||
                typeof workout !== "object"
            ) {
                throw new Error(
                    "The AI returned an empty workout."
                );
            }

            /*
               ------------------------------------------------
               Save current workout in UI state
               ------------------------------------------------
            */

            currentWorkout =
                workout;

            /*
               ------------------------------------------------
               IMPORTANT:

               Backend generation number is authoritative.
               ------------------------------------------------
            */

            if (
                data.generation_number !== undefined &&
                data.generation_number !== null
            ) {
                const parsedGeneration =
                    parseInt(
                        data.generation_number,
                        10
                    );

                if (
                    Number.isFinite(
                        parsedGeneration
                    )
                ) {
                    generationNumber =
                        parsedGeneration;
                }
            }

            /*
               ------------------------------------------------
               Render AI result
               ------------------------------------------------
            */

            renderWorkout(
                workout,
                data
            );

            hideElement(
                loadingSection
            );

            showElement(
                resultSection
            );

            /*
               Add reveal class so CSS animation can trigger.
            */

            resultSection.classList.remove(
                "result-visible"
            );

            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    resultSection.classList.add(
                        "result-visible"
                    );
                });
            });

            scrollToElement(
                resultSection
            );

        } catch (error) {
            console.error(
                "FITLYFE WORKOUT ERROR:",
                error
            );

            hideElement(
                loadingSection
            );

            /*
               If there was a previous result, keep it hidden
               rather than displaying a broken/partial workout.
            */

            hideElement(
                resultSection
            );

            showElement(
                welcomeSection
            );

            showGenerationError(
                error?.message ||
                "Unable to generate your workout."
            );

        } finally {
            setGeneratingState(false);
        }
    }


    /* =====================================================
       LOADING TEXT
       ===================================================== */

    function updateLoadingText(message) {
        if (!loadingSection) {
            return;
        }

        const title =
            loadingSection.querySelector("h3");

        const description =
            loadingSection.querySelector("p");

        if (title) {
            title.textContent =
                message;
        }

        if (description) {
            description.textContent =
                "FitLyfe AI is selecting exercises, sets, reps and rest for you.";
        }
    }


    /* =====================================================
       ERROR DISPLAY
       ===================================================== */

    function showGenerationError(message) {
        const text =
            String(message || "")
                .replace(/\s+/g, " ")
                .trim();

        if (
            typeof window.showToast ===
            "function"
        ) {
            window.showToast(
                text ||
                "Workout generation failed.",
                "error"
            );

            return;
        }

        alert(
            text ||
            "Workout generation failed."
        );
    }


    /* =====================================================
       EXTRACT EXERCISES FROM DIFFERENT AI STRUCTURES
       ===================================================== */

    function getExerciseArray(workout) {
        if (!workout) {
            return [];
        }

        /*
           Standard FitLyfe schema
        */

        if (
            Array.isArray(
                workout.exercises
            )
        ) {
            return workout.exercises;
        }

        /*
           Some AI responses may use workout_plan.
        */

        if (
            Array.isArray(
                workout.workout_plan
            )
        ) {
            return workout.workout_plan;
        }

        /*
           Some responses may use exercises_list.
        */

        if (
            Array.isArray(
                workout.exercises_list
            )
        ) {
            return workout.exercises_list;
        }

        /*
           Some responses may return a nested plan.
        */

        if (
            workout.plan &&
            typeof workout.plan === "object"
        ) {
            if (
                Array.isArray(
                    workout.plan.exercises
                )
            ) {
                return workout.plan.exercises;
            }

            if (
                Array.isArray(
                    workout.plan.workout_plan
                )
            ) {
                return workout.plan.workout_plan;
            }
        }

        return [];
    }


    /* =====================================================
       EXTRACT EXERCISE NAMES
       ===================================================== */

    function extractExerciseNames(workout) {
        const names = [];

        const exercises =
            getExerciseArray(
                workout
            );

        exercises.forEach((exercise) => {
            if (
                typeof exercise ===
                "string"
            ) {
                const name =
                    exercise.trim();

                if (name) {
                    names.push(name);
                }

                return;
            }

            if (
                !exercise ||
                typeof exercise !==
                "object"
            ) {
                return;
            }

            const name =
                exercise.exercise ||
                exercise.exercise_name ||
                exercise.name ||
                exercise.movement;

            if (name) {
                names.push(
                    String(name)
                        .trim()
                );
            }
        });

        return [
            ...new Set(
                names.filter(Boolean)
            )
        ];
    }


    /* =====================================================
       NORMALIZE EXERCISE
       ===================================================== */

    function normalizeExercise(exercise) {
        /*
           String response
        */

        if (
            typeof exercise ===
            "string"
        ) {
            return {
                exercise:
                    exercise.trim(),

                sets:
                    3,

                reps:
                    "8-12",

                rest:
                    "60-90 sec",

                notes:
                    "Perform with controlled form."
            };
        }

        /*
           Invalid response
        */

        if (
            !exercise ||
            typeof exercise !==
            "object"
        ) {
            return {
                exercise:
                    "Exercise",

                sets:
                    3,

                reps:
                    "8-12",

                rest:
                    "60-90 sec",

                notes:
                    "Perform with controlled form."
            };
        }

        /*
           Support multiple field names.
        */

        const name =
            exercise.exercise ||
            exercise.exercise_name ||
            exercise.name ||
            exercise.movement ||
            exercise.title ||
            "Exercise";

        const sets =
            exercise.sets ??
            exercise.set ??
            3;

        const reps =
            exercise.reps ??
            exercise.repetitions ??
            "8-12";

        const rest =
            exercise.rest ??
            exercise.rest_time ??
            exercise.rest_seconds ??
            "60-90 sec";

        const notes =
            exercise.notes ||
            exercise.description ||
            exercise.instructions ||
            "Perform with controlled form.";

        return {
            exercise:
                String(name).trim(),

            sets:
                sets,

            reps:
                reps,

            rest:
                normalizeRestValue(
                    rest
                ),

            notes:
                String(
                    notes
                ).trim()
        };
    }


    /* =====================================================
       NORMALIZE REST VALUE
       ===================================================== */

    function normalizeRestValue(value) {
        if (
            value === null ||
            value === undefined ||
            value === ""
        ) {
            return "60-90 sec";
        }

        /*
           Numeric rest is assumed to be seconds.
        */

        if (
            typeof value ===
            "number"
        ) {
            return `${value} sec`;
        }

        return String(value);
    }


    /* =====================================================
       CALCULATE TOTAL SETS
       ===================================================== */

    function calculateTotalSets(exercises) {
        return exercises.reduce(
            (total, exercise) => {
                const sets =
                    parseInt(
                        exercise.sets,
                        10
                    );

                return total +
                    (
                        Number.isFinite(
                            sets
                        )
                            ? sets
                            : 0
                    );
            },
            0
        );
    }


    /* =====================================================
       ESTIMATE DURATION
       ===================================================== */

    function calculateDuration(exercises) {
        if (!exercises.length) {
            return 0;
        }

        /*
           Approximate:
           • 5 min warm-up / transition
           • 3.5 min per set
        */

        let totalMinutes = 5;

        exercises.forEach(
            (exercise) => {
                const sets =
                    parseInt(
                        exercise.sets,
                        10
                    ) || 3;

                totalMinutes +=
                    sets * 3.5;
            }
        );

        return Math.round(
            totalMinutes
        );
    }


    /* =====================================================
       GET AI DURATION
       ===================================================== */

    function getWorkoutDuration(workout) {
        if (!workout) {
            return null;
        }

        const possibleValues = [
            workout.duration_minutes,
            workout.duration,
            workout.estimated_duration,
            workout.estimated_duration_minutes
        ];

        for (
            const value of possibleValues
        ) {
            if (
                value === null ||
                value === undefined ||
                value === ""
            ) {
                continue;
            }

            const numeric =
                parseInt(
                    value,
                    10
                );

            if (
                Number.isFinite(
                    numeric
                ) &&
                numeric > 0
            ) {
                return numeric;
            }
        }

        return null;
    }


    /* =====================================================
       RENDER WORKOUT
       ===================================================== */

    function renderWorkout(
        workout,
        apiData
    ) {
        if (!workout) {
            return;
        }

        const rawExercises =
            getExerciseArray(
                workout
            );

        const exercises =
            rawExercises.map(
                normalizeExercise
            );

        /*
           --------------------------------------------------
           TITLE
           --------------------------------------------------
        */

        if (resultTitle) {
            resultTitle.textContent =
                workout.title ||
                workout.name ||
                `${currentFocus || "Full Body"} Workout`;
        }

        /*
           --------------------------------------------------
           DESCRIPTION
           --------------------------------------------------
        */

        if (resultDescription) {
            resultDescription.textContent =
                workout.description ||
                workout.summary ||
                "A personalized workout created by FitLyfe AI.";
        }

        /*
           --------------------------------------------------
           EXERCISE COUNT
           --------------------------------------------------
        */

        if (exerciseCount) {
            exerciseCount.textContent =
                `${exercises.length} ${
                    exercises.length === 1
                        ? "Exercise"
                        : "Exercises"
                }`;
        }

        /*
           --------------------------------------------------
           TOTAL SETS
           --------------------------------------------------
        */

        if (setCount) {
            const totalSets =
                calculateTotalSets(
                    exercises
                );

            setCount.textContent =
                `${totalSets} ${
                    totalSets === 1
                        ? "Set"
                        : "Sets"
                }`;
        }

        /*
           --------------------------------------------------
           INTENSITY
           --------------------------------------------------
        */

        if (workoutIntensity) {
            workoutIntensity.textContent =
                workout.intensity ||
                workout.training_intensity ||
                workout.difficulty ||
                "Personalized";
        }

        /*
           --------------------------------------------------
           DURATION
           --------------------------------------------------
        */

        if (workoutDuration) {
            const aiDuration =
                getWorkoutDuration(
                    workout
                );

            const duration =
                aiDuration !== null
                    ? aiDuration
                    : calculateDuration(
                        exercises
                    );

            workoutDuration.textContent =
                `${duration} min`;
        }

        /*
           --------------------------------------------------
           EXERCISE LIST
           --------------------------------------------------
        */

        if (!exerciseList) {
            return;
        }

        exerciseList.innerHTML = "";

        if (!exercises.length) {
            exerciseList.innerHTML = `
                <div class="exercise-empty">
                    <i class="fa-solid fa-dumbbell"></i>
                    <p>
                        No exercises were returned by the AI.
                    </p>
                </div>
            `;

            return;
        }

        /*
           --------------------------------------------------
           Render each exercise
           --------------------------------------------------
        */

        exercises.forEach(
            (
                exercise,
                index
            ) => {
                const card =
                    createExerciseCard(
                        exercise,
                        index
                    );

                exerciseList.appendChild(
                    card
                );

                /*
                   Staggered entrance.
                */

                const delay =
                    index * 90;

                requestAnimationFrame(
                    () => {
                        window.setTimeout(
                            () => {
                                card.classList.add(
                                    "exercise-visible"
                                );
                            },
                            delay
                        );
                    }
                );
            }
        );

        /*
           --------------------------------------------------
           Optional fallback detection
           --------------------------------------------------
        */

        if (
            apiData &&
            apiData.ai_generated === false
        ) {
            console.warn(
                "FitLyfe AI was unavailable. A fallback workout was used.",
                apiData.ai_error || ""
            );
        }

        /*
           --------------------------------------------------
           Store exercise names locally for UI/debugging.
           The database remains authoritative.
           --------------------------------------------------
        */

        const names =
            extractExerciseNames(
                workout
            );

        console.info(
            "FITLYFE WORKOUT GENERATED",
            {
                focus:
                    currentFocus,

                generation:
                    apiData?.generation_number ??
                    generationNumber,

                workout_id:
                    apiData?.workout_id ??
                    null,

                exercises:
                    names
            }
        );
    }


    /* =====================================================
       CREATE EXERCISE CARD
       ===================================================== */

    function createExerciseCard(
        exercise,
        index
    ) {
        const card =
            document.createElement(
                "article"
            );

        card.className =
            "exercise-card ai-exercise-card";

        card.style.setProperty(
            "--exercise-index",
            index
        );

        const number =
            String(
                index + 1
            ).padStart(
                2,
                "0"
            );

        const sets =
            escapeHTML(
                String(
                    exercise.sets
                )
            );

        const reps =
            escapeHTML(
                String(
                    exercise.reps
                )
            );

        const rest =
            escapeHTML(
                String(
                    exercise.rest
                )
            );

        const name =
            escapeHTML(
                String(
                    exercise.exercise
                )
            );

        const notes =
            escapeHTML(
                String(
                    exercise.notes ||
                    ""
                )
            );

        card.innerHTML = `
            <div class="exercise-number">
                ${number}
            </div>

            <div class="exercise-main">

                <div class="exercise-heading">

                    <div class="exercise-icon">
                        <i class="fa-solid fa-dumbbell"></i>
                    </div>

                    <div>
                        <span class="exercise-label">
                            EXERCISE ${number}
                        </span>

                        <h3>
                            ${name}
                        </h3>
                    </div>

                </div>

                <p class="exercise-notes">
                    ${notes}
                </p>

            </div>

            <div class="exercise-stats">

                <div class="exercise-stat">
                    <span class="stat-label">
                        SETS
                    </span>

                    <strong>
                        ${sets}
                    </strong>
                </div>

                <div class="exercise-stat">
                    <span class="stat-label">
                        REPS
                    </span>

                    <strong>
                        ${reps}
                    </strong>
                </div>

                <div class="exercise-stat">
                    <span class="stat-label">
                        REST
                    </span>

                    <strong>
                        ${rest}
                    </strong>
                </div>

            </div>
        `;

        return card;
    }


    /* =====================================================
       HTML ESCAPE
       ===================================================== */

    function escapeHTML(value) {
        return String(
            value ?? ""
        )
            .replace(
                /&/g,
                "&amp;"
            )
            .replace(
                /</g,
                "&lt;"
            )
            .replace(
                />/g,
                "&gt;"
            )
            .replace(
                /"/g,
                "&quot;"
            )
            .replace(
                /'/g,
                "&#039;"
            );
    }


    /* =====================================================
       SET INPUT VALUE
       ===================================================== */

    function setWorkoutInput(workout) {
        if (!workoutInput || !workout) {
            return;
        }

        workoutInput.value =
            `Give me a ${workout} workout`;
    }


    /* =====================================================
       QUICK TAGS
       ===================================================== */

    document
        .querySelectorAll(
            ".quick-tag"
        )
        .forEach(
            (button) => {
                button.addEventListener(
                    "click",
                    () => {
                        if (isGenerating) {
                            return;
                        }

                        const workout =
                            button.dataset.workout;

                        if (!workout) {
                            return;
                        }

                        setWorkoutInput(
                            workout
                        );

                        generateWorkout(
                            workout
                        );
                    }
                );
            }
        );


    /* =====================================================
       MUSCLE BUTTONS
       ===================================================== */

    document
        .querySelectorAll(
            ".muscle-button"
        )
        .forEach(
            (button) => {
                button.addEventListener(
                    "click",
                    () => {
                        if (isGenerating) {
                            return;
                        }

                        const workout =
                            button.dataset.workout;

                        if (!workout) {
                            return;
                        }

                        setWorkoutInput(
                            workout
                        );

                        generateWorkout(
                            workout
                        );
                    }
                );
            }
        );


    /* =====================================================
       SPLIT OPTIONS
       ===================================================== */

    document
        .querySelectorAll(
            ".split-option"
        )
        .forEach(
            (button) => {
                button.addEventListener(
                    "click",
                    () => {
                        if (isGenerating) {
                            return;
                        }

                        const workout =
                            button.dataset.workout;

                        if (!workout) {
                            return;
                        }

                        setWorkoutInput(
                            workout
                        );

                        generateWorkout(
                            workout
                        );
                    }
                );
            }
        );


    /* =====================================================
       TRAINING SPLIT CARD
       ===================================================== */

    if (splitCard) {
        splitCard.addEventListener(
            "click",
            () => {
                if (isGenerating) {
                    return;
                }

                hideElement(
                    targetSection
                );

                showElement(
                    splitSection
                );

                scrollToElement(
                    splitSection
                );
            }
        );

        splitCard.addEventListener(
            "keydown",
            (event) => {
                if (
                    event.key === "Enter" ||
                    event.key === " "
                ) {
                    event.preventDefault();

                    splitCard.click();
                }
            }
        );
    }


    /* =====================================================
       TARGET TRAINING CARD
       ===================================================== */

    if (targetCard) {
        targetCard.addEventListener(
            "click",
            () => {
                if (isGenerating) {
                    return;
                }

                hideElement(
                    splitSection
                );

                showElement(
                    targetSection
                );

                scrollToElement(
                    targetSection
                );
            }
        );

        targetCard.addEventListener(
            "keydown",
            (event) => {
                if (
                    event.key === "Enter" ||
                    event.key === " "
                ) {
                    event.preventDefault();

                    targetCard.click();
                }
            }
        );
    }


    /* =====================================================
       CLOSE SPLIT
       ===================================================== */

    if (closeSplit) {
        closeSplit.addEventListener(
            "click",
            () => {
                hideElement(
                    splitSection
                );
            }
        );
    }


    /* =====================================================
       CLOSE TARGET
       ===================================================== */

    if (closeTarget) {
        closeTarget.addEventListener(
            "click",
            () => {
                hideElement(
                    targetSection
                );
            }
        );
    }


    /* =====================================================
       SEARCH / GENERATE BUTTON
       ===================================================== */

    if (generateButton) {
        generateButton.addEventListener(
            "click",
            () => {
                if (isGenerating) {
                    return;
                }

                const input =
                    workoutInput
                        ? workoutInput.value.trim()
                        : "";

                const workout =
                    findWorkout(
                        input
                    );

                if (!workout) {
                    showGenerationError(
                        "Tell FitLyfe what you want to train. Try Chest, Lats, Push, Pull, Legs or another muscle group."
                    );

                    if (workoutInput) {
                        workoutInput.focus();

                        workoutInput.classList.add(
                            "input-error"
                        );

                        window.setTimeout(
                            () => {
                                workoutInput.classList.remove(
                                    "input-error"
                                );
                            },
                            500
                        );
                    }

                    return;
                }

                generateWorkout(
                    workout
                );
            }
        );
    }


    /* =====================================================
       ENTER KEY SEARCH
       ===================================================== */

    if (workoutInput) {
        workoutInput.addEventListener(
            "keydown",
            (event) => {
                if (
                    event.key === "Enter"
                ) {
                    event.preventDefault();

                    if (
                        !isGenerating
                    ) {
                        generateButton?.click();
                    }
                }
            }
        );
    }


    /* =====================================================
       SEARCH FOCUS ANIMATION
       ===================================================== */

    if (workoutInput) {
        workoutInput.addEventListener(
            "focus",
            () => {
                workoutInput.classList.add(
                    "search-focused"
                );
            }
        );

        workoutInput.addEventListener(
            "blur",
            () => {
                workoutInput.classList.remove(
                    "search-focused"
                );
            }
        );
    }


    /* =====================================================
       TRY ANOTHER PLAN
       ===================================================== */

    if (regenerateButton) {
        regenerateButton.addEventListener(
            "click",
            async () => {
                if (
                    !currentWorkoutKey ||
                    isGenerating
                ) {
                    return;
                }

                regenerateButton.classList.add(
                    "rotating"
                );

                /*
                   IMPORTANT:

                   We do NOT manually increment the
                   generation number.

                   Flask calculates the next generation
                   from WorkoutPlan records in PostgreSQL.
                */

                try {
                    await generateWorkout(
                        currentWorkoutKey,
                        {
                            regenerate:
                                true
                        }
                    );
                } finally {
                    window.setTimeout(
                        () => {
                            regenerateButton.classList.remove(
                                "rotating"
                            );
                        },
                        350
                    );
                }
            }
        );
    }


    /* =====================================================
       NEW WORKOUT
       ===================================================== */

    if (newWorkoutButton) {
        newWorkoutButton.addEventListener(
            "click",
            () => {
                if (isGenerating) {
                    return;
                }

                resetWorkoutSession();

                closeSelections();

                if (workoutInput) {
                    workoutInput.value = "";
                }

                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });
            }
        );
    }


    /* =====================================================
       OPTIONAL LOAD LATEST WORKOUT
       -----------------------------------------------------
       We intentionally do NOT automatically display the
       latest workout.

       The Workout Studio opens in a clean state.

       The endpoint is still available through Flask for
       future history / restore functionality.
       ===================================================== */

    async function loadLatestWorkout() {
        try {
            const response =
                await fetch(
                    "/api/workout/latest",
                    {
                        method: "GET",

                        headers: {
                            "Accept":
                                "application/json"
                        },

                        credentials:
                            "same-origin"
                    }
                );

            if (!response.ok) {
                return null;
            }

            const data =
                await response.json();

            if (
                !data ||
                data.success !== true
            ) {
                return null;
            }

            return data.workout ||
                data.plan ||
                null;

        } catch (error) {
            console.warn(
                "Unable to load latest workout:",
                error
            );

            return null;
        }
    }


    /* =====================================================
       REDUCED MOTION
       ===================================================== */

    try {
        if (
            window.matchMedia(
                "(prefers-reduced-motion: reduce)"
            ).matches
        ) {
            document.documentElement.classList.add(
                "reduce-motion"
            );
        }
    } catch (error) {
        console.warn(
            "Reduced motion detection unavailable.",
            error
        );
    }


    /* =====================================================
       INITIAL STATE
       ===================================================== */

    closeSelections();

    hideElement(
        loadingSection
    );

    hideElement(
        resultSection
    );

    showElement(
        welcomeSection
    );

    /*
       Make sure buttons start enabled.
    */

    setGeneratingState(false);


    /* =====================================================
       CLEANUP
       ===================================================== */

    window.addEventListener(
        "beforeunload",
        () => {
            clearGenerationTimer();
        }
    );


    /* =====================================================
       DEBUG HELPER
       -----------------------------------------------------
       Useful from browser console:

       FitLyfeWorkout.generate("Chest")
       ===================================================== */

    window.FitLyfeWorkout = {
        generate: (
            focus
        ) => {
            const workout =
                findWorkout(
                    focus
                );

            if (!workout) {
                console.warn(
                    "Unknown workout focus:",
                    focus
                );

                return;
            }

            setWorkoutInput(
                workout
            );

            return generateWorkout(
                workout
            );
        },

        regenerate: () => {
            if (
                currentWorkoutKey &&
                !isGenerating
            ) {
                return generateWorkout(
                    currentWorkoutKey,
                    {
                        regenerate:
                            true
                    }
                );
            }

            return null;
        },

        getCurrentWorkout: () => {
            return currentWorkout;
        },

        getCurrentFocus: () => {
            return currentFocus;
        },

        getGenerationNumber: () => {
            return generationNumber;
        }
    };

});