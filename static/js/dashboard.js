/* =========================================================
   FITLYFE — PREMIUM PERSONAL DASHBOARD
   One authenticated user -> one private data space.
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const $ = (id) => document.getElementById(id);

    const calendarDays = $("calendarDays");
    const calendarMonth = $("calendarMonth");
    const previousMonth = $("previousMonth");
    const nextMonth = $("nextMonth");

    const goalsList = $("goalsList");
    const addGoalButton = $("addGoalButton");
    const addGoalPanel = $("addGoalPanel");
    const closeGoalPanel = $("closeGoalPanel");
    const saveGoalButton = $("saveGoalButton");
    const cancelGoalButton = $("cancelGoalButton");
    const newGoalName = $("newGoalName");
    const newGoalDescription = $("newGoalDescription");
    const goalMessage = $("goalMessage");

    const selectedDateEl = $("selectedDate");
    const selectedDatePercentage = $("selectedDatePercentage");
    const goalDateLabel = $("goalDateLabel");

    const todayProgressCircle = $("todayProgressCircle");
    const todayCompletion = $("todayCompletion");
    const dailyProgressText = $("dailyProgressText");
    const currentStreakEl = $("currentStreak");
    const todayStatus = $("todayStatus");
    const todayPercentage = $("todayPercentage");

    const predictionTrendBadge = $("predictionTrend");
    const weeklyCompletion = $("weeklyCompletion");
    const weeklyProgressFill = $("weeklyProgressFill");
    const weeklyAverage = $("weeklyAverage");
    const activeDaysEl = $("activeDays");
    const bestStreakEl = $("bestStreak");

    const dailyProgressPercentage = $("dailyProgressPercentage");
    const dailyProgressFill = $("dailyProgressFill");
    const dailyInsightList = $("dailyInsightList");

    const totalGoalsCompleted = $("totalGoalsCompleted");
    const achievementStreak = $("achievementStreak");
    const achievementActiveDays = $("achievementActiveDays");
    const achievementBestStreak = $("achievementBestStreak");

    const predictionConfidence = $("predictionConfidence");
    const predictionConfidenceFill = $("predictionConfidenceFill");
    const tomorrowPredictionDetail = $("tomorrowPredictionDetail");
    const nextWeekPredictionDetail = $("nextWeekPredictionDetail");
    const predictionTrendDetail = $("predictionTrendDetail");
    const predictionCircle = $("predictionCircle");
    const tomorrowPrediction = $("tomorrowPrediction");

    const dashboardToast = $("dashboardToast");
    const toastMessage = $("toastMessage");

    // Daily journal
    const logWorkout = $("logWorkout");
    const logCalories = $("logCalories");
    const logWater = $("logWater");
    const logSleep = $("logSleep");
    const logMood = $("logMood");
    const logNotes = $("logNotes");
    const saveDailyLogButton = $("saveDailyLogButton");
    const journalStatus = $("journalStatus");
    const journalDateBadge = $("journalDateBadge");

    if (!goalsList || !calendarDays) {
        console.error("FitLyfe dashboard: required elements are missing.");
        return;
    }

    let selectedDate = startOfDay(new Date());

    let calendarViewDate = new Date(
        selectedDate.getFullYear(),
        selectedDate.getMonth(),
        1
    );

    let currentGoals = [];
    let toastTimer = null;

    initialize();

    async function initialize() {
        setupEvents();
        await loadCalendar();
        await loadDashboard();
    }

    // ---------------------------------------------------------
    // Dates
    // ---------------------------------------------------------

    function startOfDay(value) {
        const d = new Date(value);
        d.setHours(0, 0, 0, 0);
        return d;
    }

    function toDateKey(value) {
        const d = startOfDay(value);

        return [
            d.getFullYear(),
            String(d.getMonth() + 1).padStart(2, "0"),
            String(d.getDate()).padStart(2, "0"),
        ].join("-");
    }

    function fromDateKey(key) {
        const [y, m, d] = String(key).split("-").map(Number);

        return new Date(
            y,
            (m || 1) - 1,
            d || 1
        );
    }

    function isSameDate(a, b) {
        return (
            a.getFullYear() === b.getFullYear() &&
            a.getMonth() === b.getMonth() &&
            a.getDate() === b.getDate()
        );
    }

    function isToday(value) {
        return isSameDate(value, new Date());
    }

    function formatLongDate(value) {
        return value.toLocaleDateString("en-IN", {
            weekday: "long",
            month: "long",
            day: "numeric",
            year: "numeric",
        });
    }

    // ---------------------------------------------------------
    // API
    // ---------------------------------------------------------

    async function apiGet(url) {
        const response = await fetch(url, {
            headers: {
                Accept: "application/json",
            },
            credentials: "same-origin",
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.error || "Request failed."
            );
        }

        return data;
    }

    async function apiSend(url, method, body) {
        const response = await fetch(url, {
            method,
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
            },
            body: body
                ? JSON.stringify(body)
                : undefined,
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.error || "Request failed."
            );
        }

        return data;
    }

    // ---------------------------------------------------------
    // Calendar
    // ---------------------------------------------------------

    async function loadCalendar() {
        try {
            const year =
                calendarViewDate.getFullYear();

            const month =
                calendarViewDate.getMonth() + 1;

            const data = await apiGet(
                `/api/calendar-data?year=${year}&month=${month}`
            );

            renderCalendar(data);
        } catch (error) {
            console.error(
                "FitLyfe calendar error:",
                error
            );

            showToast(
                "Unable to load your calendar.",
                false
            );
        }
    }

    function renderCalendar(data) {
        calendarDays.innerHTML = "";

        const year = Number(data.year);
        const monthIndex = Number(data.month) - 1;

        if (calendarMonth) {
            calendarMonth.textContent =
                new Date(
                    year,
                    monthIndex,
                    1
                ).toLocaleDateString("en-IN", {
                    month: "long",
                    year: "numeric",
                });
        }

        // Monday-first calendar.
        const firstDay =
            new Date(
                year,
                monthIndex,
                1
            ).getDay();

        const leading =
            firstDay === 0
                ? 6
                : firstDay - 1;

        for (let i = 0; i < leading; i += 1) {
            const blank =
                document.createElement("div");

            blank.className =
                "calendar-day empty";

            blank.setAttribute(
                "aria-hidden",
                "true"
            );

            calendarDays.appendChild(blank);
        }

        (data.days || []).forEach((day) => {
            const dayDate =
                new Date(
                    year,
                    monthIndex,
                    Number(day.day)
                );

            const button =
                document.createElement("button");

            button.type = "button";

            button.className =
                "calendar-day current-month";

            button.textContent =
                String(day.day);

            button.setAttribute(
                "aria-label",
                `${formatLongDate(dayDate)} — ${day.percentage || 0}% complete`
            );

            if (day.is_today) {
                button.classList.add("today");
            }

            if (
                isSameDate(
                    dayDate,
                    selectedDate
                )
            ) {
                button.classList.add(
                    "selected"
                );
            }

            if (
                day.state === "completed"
            ) {
                button.classList.add(
                    "completed"
                );
            }

            if (
                day.state === "partial"
            ) {
                button.classList.add(
                    "partial"
                );
            }

            if (
                day.state === "future"
            ) {
                button.classList.add(
                    "future"
                );
            }

            if (
                day.state === "missed"
            ) {
                button.classList.add(
                    "missed"
                );
            }

            // Visual activity indicator.
            const indicator =
                document.createElement("span");

            indicator.className =
                "calendar-activity-dot";

            indicator.setAttribute(
                "aria-hidden",
                "true"
            );

            button.appendChild(indicator);

            button.addEventListener(
                "click",
                async () => {
                    selectedDate =
                        startOfDay(dayDate);

                    updateSelectedCalendarDay();

                    await loadDashboard();
                }
            );

            calendarDays.appendChild(button);
        });
    }

    function updateSelectedCalendarDay() {
        document
            .querySelectorAll(
                ".calendar-day.selected"
            )
            .forEach((node) => {
                node.classList.remove(
                    "selected"
                );
            });

        const buttons =
            calendarDays.querySelectorAll(
                ".calendar-day.current-month"
            );

        buttons.forEach((button) => {
            const number =
                Number(
                    button.textContent.trim()
                );

            if (
                number === selectedDate.getDate() &&
                selectedDate.getMonth() ===
                    calendarViewDate.getMonth() &&
                selectedDate.getFullYear() ===
                    calendarViewDate.getFullYear()
            ) {
                button.classList.add(
                    "selected"
                );
            }
        });
    }

    // ---------------------------------------------------------
    // Dashboard data
    // ---------------------------------------------------------

    async function loadDashboard() {
        try {
            const dateKey =
                toDateKey(selectedDate);

            const data = await apiGet(
                `/api/dashboard-data?date=${encodeURIComponent(dateKey)}`
            );

            currentGoals =
                Array.isArray(data.goals)
                    ? data.goals
                    : [];

            renderGoals();

            renderDailyLog(data.log);

            updateSelectedDateSummary(data);

            updateTodayCard(data);

            updateWeeklyCard(data);

            updateInsights(data);

            updateAchievements(data);

            updatePrediction(
                data.prediction
            );

            renderWeeklyChart(
                data.weekly
            );

            renderTrendChart(
                data.prediction
            );

            if (journalStatus) {
                journalStatus.textContent =
                    "";
            }
        } catch (error) {
            console.error(
                "FitLyfe dashboard error:",
                error
            );

            showToast(
                error.message ||
                    "Unable to load dashboard data.",
                false
            );
        }
    }

    function updateSelectedDateSummary(data) {
        const label =
            isToday(selectedDate)
                ? "Today"
                : formatLongDate(
                    selectedDate
                );

        if (selectedDateEl) {
            selectedDateEl.textContent =
                label;
        }

        if (selectedDatePercentage) {
            selectedDatePercentage.textContent =
                `${data.today?.percentage || 0}%`;
        }

        if (goalDateLabel) {
            goalDateLabel.textContent =
                isToday(selectedDate)
                    ? "Tracking today's goals"
                    : `Tracking goals for ${formatLongDate(
                        selectedDate
                    )}`;
        }

        if (journalDateBadge) {
            journalDateBadge.textContent =
                label;
        }

        const journalTitle =
            $("journalTitle");

        if (journalTitle) {
            journalTitle.textContent =
                isToday(selectedDate)
                    ? "Log your day"
                    : `Log ${selectedDate.toLocaleDateString(
                        "en-IN",
                        {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                        }
                    )}`;
        }
    }

    // ---------------------------------------------------------
    // Goals
    // ---------------------------------------------------------

    function renderGoals() {
        goalsList.innerHTML = "";

        if (!currentGoals.length) {
            goalsList.innerHTML = `
                <div class="empty-goals">
                    <div class="empty-icon">🎯</div>
                    <h3>No goals for this day</h3>
                    <p>Add a goal and make this date count.</p>
                </div>
            `;

            updateGoalProgress();

            return;
        }

        currentGoals.forEach(
            (goal, index) => {
                const item =
                    document.createElement(
                        "div"
                    );

                item.className =
                    "goal-item" +
                    (
                        goal.completed
                            ? " completed"
                            : ""
                    );

                item.dataset.goalId =
                    goal.id;

                item.style.setProperty(
                    "--goal-delay",
                    `${index * 60}ms`
                );

                item.innerHTML = `
                    <button
                        type="button"
                        class="goal-check${
                            goal.completed
                                ? " completed"
                                : ""
                        }"
                        aria-label="Mark ${escapeHTML(
                            goal.title
                        )} as complete"
                        aria-pressed="${
                            goal.completed
                                ? "true"
                                : "false"
                        }"
                    >✓</button>

                    <div class="goal-info">
                        <strong>
                            <span class="goal-spark">✦</span>
                            ${escapeHTML(
                                goal.title
                            )}
                        </strong>

                        <small>
                            ${escapeHTML(
                                goal.description ||
                                    "Personal daily goal"
                            )}
                        </small>

                        <div class="goal-progress">
                            <div
                                class="goal-progress-fill"
                                style="width:${
                                    goal.completed
                                        ? 100
                                        : 0
                                }%"
                            ></div>
                        </div>
                    </div>

                    <button
                        type="button"
                        class="goal-delete remove-goal"
                        title="Remove goal"
                        aria-label="Remove ${escapeHTML(
                            goal.title
                        )}"
                    >×</button>
                `;

                item
                    .querySelector(
                        ".goal-check"
                    )
                    .addEventListener(
                        "click",
                        () =>
                            toggleGoal(
                                goal.id
                            )
                    );

                item
                    .querySelector(
                        ".remove-goal"
                    )
                    .addEventListener(
                        "click",
                        () =>
                            deleteGoal(
                                goal.id,
                                goal.title
                            )
                    );

                goalsList.appendChild(item);
            }
        );

        updateGoalProgress();
    }

    function updateGoalProgress() {
        const total =
            currentGoals.length;

        const completed =
            currentGoals.filter(
                (goal) =>
                    goal.completed
            ).length;

        const percentage =
            total
                ? Math.round(
                    (completed / total) *
                        100
                )
                : 0;

        if (dailyProgressPercentage) {
            dailyProgressPercentage.textContent =
                `${percentage}%`;
        }

        if (dailyProgressFill) {
            requestAnimationFrame(
                () => {
                    dailyProgressFill.style.width =
                        `${percentage}%`;
                }
            );
        }
    }

    async function toggleGoal(goalId) {
        try {
            const result =
                await apiSend(
                    `/api/daily-goals/${goalId}/toggle`,
                    "POST"
                );

            const target =
                currentGoals.find(
                    (goal) =>
                        Number(goal.id) ===
                        Number(goalId)
                );

            if (target) {
                target.completed =
                    Boolean(
                        result.completed
                    );
            }

            renderGoals();

            showToast(
                result.completed
                    ? "Goal completed — excellent work! ✨"
                    : "Goal moved back to pending.",
                true
            );

            await loadCalendar();

            await loadDashboard();
        } catch (error) {
            console.error(
                "Toggle goal error:",
                error
            );

            showToast(
                error.message,
                false
            );
        }
    }

    // ---------------------------------------------------------
    // DELETE GOAL — PREMIUM ANIMATED CONFIRMATION
    // ---------------------------------------------------------

    async function deleteGoal(
        goalId,
        title
    ) {
        const confirmed =
            await showDeleteConfirmation(
                title
            );

        if (!confirmed) {
            return;
        }

        try {
            await apiSend(
                `/api/daily-goals/${goalId}`,
                "DELETE"
            );

            showToast(
                "Goal removed.",
                true
            );

            await loadCalendar();

            await loadDashboard();
        } catch (error) {
            console.error(
                "Delete goal error:",
                error
            );

            showToast(
                error.message,
                false
            );
        }
    }

    // ---------------------------------------------------------
    // PREMIUM DELETE CONFIRMATION MODAL
    // ---------------------------------------------------------

    function showDeleteConfirmation(
        title
    ) {
        return new Promise(
            (resolve) => {
                const existing =
                    document.getElementById(
                        "fitlyfeDeleteModal"
                    );

                if (existing) {
                    existing.remove();
                }

                const modal =
                    document.createElement(
                        "div"
                    );

                modal.id =
                    "fitlyfeDeleteModal";

                modal.className =
                    "fitlyfe-delete-overlay";

                modal.innerHTML = `
                    <div
                        class="fitlyfe-delete-modal"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="fitlyfeDeleteTitle"
                    >

                        <button
                            type="button"
                            class="fitlyfe-delete-close"
                            aria-label="Close"
                        >×</button>

                        <div class="fitlyfe-delete-icon">
                            <span>×</span>
                        </div>

                        <div class="fitlyfe-delete-content">

                            <span class="fitlyfe-delete-label">
                                GOAL MANAGEMENT
                            </span>

                            <h3 id="fitlyfeDeleteTitle">
                                Remove this goal?
                            </h3>

                            <p>
                                You're about to remove
                                <strong>${escapeHTML(
                                    title
                                )}</strong>
                                from your routine.
                            </p>

                            <small>
                                This will remove the goal
                                from this day and future days.
                            </small>

                        </div>

                        <div class="fitlyfe-delete-actions">

                            <button
                                type="button"
                                class="fitlyfe-delete-cancel"
                            >
                                Keep Goal
                            </button>

                            <button
                                type="button"
                                class="fitlyfe-delete-confirm"
                            >
                                Remove Goal
                            </button>

                        </div>

                    </div>
                `;

                document.body.appendChild(
                    modal
                );

                document.body.classList.add(
                    "fitlyfe-delete-open"
                );

                const closeButton =
                    modal.querySelector(
                        ".fitlyfe-delete-close"
                    );

                const cancelButton =
                    modal.querySelector(
                        ".fitlyfe-delete-cancel"
                    );

                const confirmButton =
                    modal.querySelector(
                        ".fitlyfe-delete-confirm"
                    );

                let finished = false;

                function finish(result) {
                    if (finished) {
                        return;
                    }

                    finished = true;

                    modal.classList.add(
                        "closing"
                    );

                    document.body.classList.remove(
                        "fitlyfe-delete-open"
                    );

                    setTimeout(
                        () => {
                            modal.remove();

                            resolve(
                                result
                            );
                        },
                        220
                    );
                }

                closeButton.addEventListener(
                    "click",
                    () => {
                        finish(false);
                    }
                );

                cancelButton.addEventListener(
                    "click",
                    () => {
                        finish(false);
                    }
                );

                confirmButton.addEventListener(
                    "click",
                    () => {
                        confirmButton.disabled =
                            true;

                        confirmButton.innerHTML =
                            '<span class="delete-spinner"></span> Removing...';

                        setTimeout(
                            () => {
                                finish(
                                    true
                                );
                            },
                            350
                        );
                    }
                );

                modal.addEventListener(
                    "click",
                    (event) => {
                        if (
                            event.target ===
                            modal
                        ) {
                            finish(
                                false
                            );
                        }
                    }
                );

                const escapeHandler =
                    (event) => {
                        if (
                            event.key ===
                            "Escape"
                        ) {
                            finish(
                                false
                            );

                            document.removeEventListener(
                                "keydown",
                                escapeHandler
                            );
                        }
                    };

                document.addEventListener(
                    "keydown",
                    escapeHandler
                );

                requestAnimationFrame(
                    () => {
                        modal.classList.add(
                            "show"
                        );
                    }
                );

                setTimeout(
                    () => {
                        cancelButton.focus();
                    },
                    100
                );
            }
        );
    }

    // ---------------------------------------------------------
    // Add goal modal
    // ---------------------------------------------------------

    function openGoalModal() {
        if (!addGoalPanel) {
            return;
        }

        addGoalPanel.classList.add(
            "show"
        );

        addGoalPanel.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "goal-modal-open"
        );

        if (goalMessage) {
            goalMessage.textContent =
                "";

            goalMessage.className =
                "";
        }

        if (newGoalName) {
            newGoalName.value = "";
        }

        if (newGoalDescription) {
            newGoalDescription.value = "";
        }

        window.setTimeout(
            () => {
                if (newGoalName) {
                    newGoalName.focus();
                }
            },
            120
        );
    }

    function closeGoalModal() {
        if (!addGoalPanel) {
            return;
        }

        addGoalPanel.classList.remove(
            "show"
        );

        addGoalPanel.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "goal-modal-open"
        );
    }

    function showGoalMessage(
        message,
        success
    ) {
        if (!goalMessage) {
            return;
        }

        goalMessage.textContent =
            message;

        goalMessage.className =
            success
                ? "goal-message success"
                : "goal-message error";
    }

    async function submitNewGoal() {
        const title =
            (
                newGoalName?.value ||
                ""
            ).trim();

        const description =
            (
                newGoalDescription?.value ||
                ""
            ).trim();

        if (!title) {
            showGoalMessage(
                "Please enter a goal name.",
                false
            );

            if (newGoalName) {
                newGoalName.focus();
            }

            return;
        }

        if (title.length < 2) {
            showGoalMessage(
                "Goal name should contain at least 2 characters.",
                false
            );

            return;
        }

        if (saveGoalButton) {
            saveGoalButton.disabled =
                true;

            saveGoalButton.innerHTML =
                '<span class="button-spinner"></span> Adding...';
        }

        try {
            await apiSend(
                "/api/daily-goals",
                "POST",
                {
                    title,
                    description,
                    goal_date:
                        toDateKey(
                            selectedDate
                        ),
                }
            );

            showGoalMessage(
                "Goal added successfully!",
                true
            );

            showToast(
                "New daily goal added ✨",
                true
            );

            await loadCalendar();

            await loadDashboard();

            window.setTimeout(
                closeGoalModal,
                550
            );
        } catch (error) {
            console.error(
                "Add goal error:",
                error
            );

            showGoalMessage(
                error.message ||
                    "Unable to add goal.",
                false
            );
        } finally {
            if (saveGoalButton) {
                saveGoalButton.disabled =
                    false;

                saveGoalButton.innerHTML =
                    '<span aria-hidden="true">+</span> Add Goal';
            }
        }
    }

    // ---------------------------------------------------------
    // Daily journal
    // ---------------------------------------------------------

    function renderDailyLog(log) {
        if (!log) {
            if (logWorkout) {
                logWorkout.value =
                    "false";
            }

            if (logCalories) {
                logCalories.value =
                    "";
            }

            if (logWater) {
                logWater.value =
                    "";
            }

            if (logSleep) {
                logSleep.value =
                    "";
            }

            if (logMood) {
                logMood.value =
                    "";
            }

            if (logNotes) {
                logNotes.value =
                    "";
            }

            return;
        }

        if (logWorkout) {
            logWorkout.value =
                log.workout_done
                    ? "true"
                    : "false";
        }

        if (logCalories) {
            logCalories.value =
                log.calories_intake ??
                "";
        }

        if (logWater) {
            logWater.value =
                log.water_intake_l ??
                "";
        }

        if (logSleep) {
            logSleep.value =
                log.sleep_hours ??
                "";
        }

        if (logMood) {
            logMood.value =
                log.mood ??
                "";
        }

        if (logNotes) {
            logNotes.value =
                log.notes ||
                "";
        }
    }

    async function saveDailyLog() {
        if (saveDailyLogButton) {
            saveDailyLogButton.disabled =
                true;

            saveDailyLogButton.innerHTML =
                '<span class="button-spinner"></span> Saving...';
        }

        if (journalStatus) {
            journalStatus.textContent =
                "Saving your private check-in...";

            journalStatus.className =
                "journal-status saving";
        }

        try {
            await apiSend(
                "/api/daily-log",
                "POST",
                {
                    log_date:
                        toDateKey(
                            selectedDate
                        ),

                    workout_done:
                        logWorkout?.value ===
                        "true",

                    calories_intake:
                        logCalories?.value ||
                        null,

                    water_intake_l:
                        logWater?.value ||
                        null,

                    sleep_hours:
                        logSleep?.value ||
                        null,

                    mood:
                        logMood?.value ||
                        null,

                    notes:
                        logNotes?.value ||
                        "",
                }
            );

            if (journalStatus) {
                journalStatus.textContent =
                    "Saved ✓";

                journalStatus.className =
                    "journal-status saved";
            }

            showToast(
                `${
                    isToday(selectedDate)
                        ? "Today's"
                        : "Daily"
                } check-in saved.`,
                true
            );

            await loadCalendar();

            await loadDashboard();
        } catch (error) {
            console.error(
                "Daily log error:",
                error
            );

            if (journalStatus) {
                journalStatus.textContent =
                    error.message ||
                    "Unable to save.";

                journalStatus.className =
                    "journal-status error";
            }

            showToast(
                error.message ||
                    "Unable to save daily check-in.",
                false
            );
        } finally {
            if (saveDailyLogButton) {
                saveDailyLogButton.disabled =
                    false;

                saveDailyLogButton.innerHTML =
                    "<span>✓</span> Save Daily Check-in";
            }
        }
    }

    // ---------------------------------------------------------
    // UI updates
    // ---------------------------------------------------------

    function updateTodayCard(data) {
        const today =
            data.today || {
                completed: 0,
                total: 0,
                percentage: 0,
            };

        const percentage =
            Number(today.percentage) ||
            0;

        if (todayCompletion) {
            todayCompletion.textContent =
                `${percentage}%`;
        }

        if (dailyProgressText) {
            dailyProgressText.textContent =
                `${today.completed || 0} / ${
                    today.total || 0
                }`;
        }

        if (currentStreakEl) {
            currentStreakEl.textContent =
                `${data.streak || 0} days`;
        }

        if (todayStatus) {
            todayStatus.textContent =
                percentage >= 100 &&
                today.total > 0
                    ? "Complete"
                    : percentage > 0
                        ? "In Progress"
                        : "Pending";
        }

        if (todayPercentage) {
            todayPercentage.textContent =
                `${percentage}%`;
        }

        if (dailyProgressPercentage) {
            dailyProgressPercentage.textContent =
                `${percentage}%`;
        }

        if (dailyProgressFill) {
            requestAnimationFrame(
                () => {
                    dailyProgressFill.style.width =
                        `${percentage}%`;
                }
            );
        }

        if (todayProgressCircle) {
            const circumference =
                2 * Math.PI * 50;

            todayProgressCircle.style.strokeDasharray =
                `${circumference}`;

            requestAnimationFrame(
                () => {
                    todayProgressCircle.style.strokeDashoffset =
                        `${
                            circumference -
                            (percentage / 100) *
                                circumference
                        }`;
                }
            );
        }
    }

    function updateWeeklyCard(data) {
        const weekly =
            data.weekly || {};

        const average =
            Number(weekly.average) ||
            0;

        if (weeklyCompletion) {
            weeklyCompletion.textContent =
                `${average}%`;
        }

        if (weeklyAverage) {
            weeklyAverage.textContent =
                `${average}%`;
        }

        if (weeklyProgressFill) {
            requestAnimationFrame(
                () => {
                    weeklyProgressFill.style.width =
                        `${average}%`;
                }
            );
        }

        if (activeDaysEl) {
            activeDaysEl.textContent =
                `${data.active_days || 0}`;
        }

        if (bestStreakEl) {
            bestStreakEl.textContent =
                `${data.best_streak || 0}`;
        }
    }

    function updateInsights(data) {
        if (!dailyInsightList) {
            return;
        }

        dailyInsightList.innerHTML =
            "";

        const labels =
            data.weekly?.labels ||
            [];

        const series =
            data.weekly?.series ||
            [];

        labels.forEach(
            (label, index) => {
                const value =
                    Number(
                        series[index]
                    ) || 0;

                const row =
                    document.createElement(
                        "div"
                    );

                row.className =
                    "day-insight";

                row.innerHTML = `
                    <span class="day-name">
                        ${escapeHTML(label)}
                    </span>

                    <div class="day-bar">
                        <div
                            class="day-bar-fill"
                            style="width:${value}%"
                        ></div>
                    </div>

                    <span class="day-value">
                        ${value}%
                    </span>
                `;

                dailyInsightList.appendChild(
                    row
                );
            }
        );
    }

    function updateAchievements(data) {
        if (totalGoalsCompleted) {
            totalGoalsCompleted.textContent =
                data.total_completed ||
                0;
        }

        if (achievementStreak) {
            achievementStreak.textContent =
                `${data.streak || 0} days`;
        }

        if (achievementActiveDays) {
            achievementActiveDays.textContent =
                data.active_days ||
                0;
        }

        if (achievementBestStreak) {
            achievementBestStreak.textContent =
                `${data.best_streak || 0} days`;
        }
    }

    function updatePrediction(
        prediction
    ) {
        if (!prediction) {
            return;
        }

        const tomorrow =
            Number(
                prediction.tomorrow_percentage
            ) || 0;

        const nextWeek =
            Number(
                prediction.next_week_percentage
            ) || 0;

        const confidence =
            Number(
                prediction.confidence_percentage
            ) || 0;

        const trend =
            prediction.trend ||
            "Building";

        if (tomorrowPrediction) {
            tomorrowPrediction.textContent =
                `${tomorrow}%`;
        }

        if (tomorrowPredictionDetail) {
            tomorrowPredictionDetail.textContent =
                `${tomorrow}%`;
        }

        if (nextWeekPredictionDetail) {
            nextWeekPredictionDetail.textContent =
                `${nextWeek}%`;
        }

        if (predictionTrendDetail) {
            predictionTrendDetail.textContent =
                trend;
        }

        if (predictionConfidence) {
            predictionConfidence.textContent =
                `${confidence}%`;
        }

        if (predictionConfidenceFill) {
            requestAnimationFrame(
                () => {
                    predictionConfidenceFill.style.width =
                        `${confidence}%`;
                }
            );
        }

        if (predictionTrendBadge) {
            predictionTrendBadge.textContent =
                trend;

            predictionTrendBadge.className =
                "trend-badge" +
                (
                    trend === "Declining"
                        ? " danger"
                        : trend === "Stable"
                            ? " warning"
                            : ""
                );
        }

        if (predictionCircle) {
            const circumference =
                2 * Math.PI * 58;

            predictionCircle.style.strokeDasharray =
                `${circumference}`;

            requestAnimationFrame(
                () => {
                    predictionCircle.style.strokeDashoffset =
                        `${
                            circumference -
                            (tomorrow / 100) *
                                circumference
                        }`;
                }
            );
        }
    }

    // ---------------------------------------------------------
    // Charts
    // ---------------------------------------------------------

    const plotlyBase = {
        paper_bgcolor:
            "rgba(0,0,0,0)",

        plot_bgcolor:
            "rgba(0,0,0,0)",

        margin: {
            t: 16,
            r: 10,
            b: 35,
            l: 38,
        },

        font: {
            color: "#89928c",
            family:
                "Poppins, sans-serif",
            size: 11,
        },

        xaxis: {
            gridcolor:
                "rgba(255,255,255,0.05)",

            zeroline: false,

            fixedrange: true,
        },

        yaxis: {
            gridcolor:
                "rgba(255,255,255,0.05)",

            zeroline: false,

            range: [0, 100],

            fixedrange: true,
        },

        showlegend: false,

        hoverlabel: {
            bgcolor: "#07100b",

            bordercolor: "#39ff88",

            font: {
                color: "#ffffff",
            },
        },
    };

    function renderWeeklyChart(
        weekly
    ) {
        const container =
            $("weeklyChart");

        if (
            !container ||
            typeof Plotly ===
                "undefined"
        ) {
            return;
        }

        const labels =
            weekly?.labels || [];

        const series =
            weekly?.series || [];

        const trace = {
            x: labels,

            y: series,

            type: "bar",

            marker: {
                color:
                    series.map(
                        (value) => {
                            if (
                                value >=
                                70
                            ) {
                                return "#39ff88";
                            }

                            if (
                                value > 0
                            ) {
                                return "#ffc857";
                            }

                            return "#2d342f";
                        }
                    ),

                line: {
                    width: 0,
                },
            },

            hovertemplate:
                "<b>%{x}</b><br>Completion: %{y}%<extra></extra>",
        };

        Plotly.react(
            container,
            [trace],
            plotlyBase,
            {
                displayModeBar:
                    false,

                responsive: true,
            }
        );
    }

    function renderTrendChart(
        prediction
    ) {
        const container =
            $("overallChart");

        if (
            !container ||
            typeof Plotly ===
                "undefined" ||
            !prediction
        ) {
            return;
        }

        const history =
            Array.isArray(
                prediction.trend_history
            )
                ? prediction.trend_history
                : [];

        if (!history.length) {
            Plotly.purge(
                container
            );

            return;
        }

        const labels =
            history.map(
                (_, index) =>
                    index ===
                    history.length - 1
                        ? "This wk"
                        : `Wk -${
                            history.length -
                            1 -
                            index
                        }`
            );

        labels.push("Next wk");

        const actualTrace = {
            x: labels.slice(
                0,
                history.length
            ),

            y: history,

            type: "scatter",

            mode:
                "lines+markers",

            line: {
                color: "#39ff88",

                width: 3,

                shape: "spline",
            },

            marker: {
                color: "#39ff88",

                size: 7,
            },

            hovertemplate:
                "%{x}<br>%{y}%<extra></extra>",
        };

        const last =
            history[
                history.length - 1
            ] || 0;

        const forecastTrace = {
            x: [
                labels[
                    history.length - 1
                ],
                "Next wk",
            ],

            y: [
                last,

                Number(
                    prediction.next_week_percentage
                ) || 0,
            ],

            type: "scatter",

            mode:
                "lines+markers",

            line: {
                color: "#64b5ff",

                width: 3,

                dash: "dash",
            },

            marker: {
                color: "#64b5ff",

                size: 9,

                symbol: "diamond",
            },

            hovertemplate:
                "%{x}<br>%{y}%<extra></extra>",
        };

        Plotly.react(
            container,
            [
                actualTrace,
                forecastTrace,
            ],
            plotlyBase,
            {
                displayModeBar:
                    false,

                responsive: true,
            }
        );
    }

    // ---------------------------------------------------------
    // Events
    // ---------------------------------------------------------

    function setupEvents() {
        previousMonth?.addEventListener(
            "click",
            async () => {
                calendarViewDate =
                    new Date(
                        calendarViewDate.getFullYear(),
                        calendarViewDate.getMonth() -
                            1,
                        1
                    );

                await loadCalendar();
            }
        );

        nextMonth?.addEventListener(
            "click",
            async () => {
                calendarViewDate =
                    new Date(
                        calendarViewDate.getFullYear(),
                        calendarViewDate.getMonth() +
                            1,
                        1
                    );

                await loadCalendar();
            }
        );

        addGoalButton?.addEventListener(
            "click",
            openGoalModal
        );

        closeGoalPanel?.addEventListener(
            "click",
            closeGoalModal
        );

        cancelGoalButton?.addEventListener(
            "click",
            closeGoalModal
        );

        saveGoalButton?.addEventListener(
            "click",
            submitNewGoal
        );

        saveDailyLogButton?.addEventListener(
            "click",
            saveDailyLog
        );

        addGoalPanel?.addEventListener(
            "click",
            (event) => {
                if (
                    event.target ===
                    addGoalPanel
                ) {
                    closeGoalModal();
                }
            }
        );

        [
            newGoalName,
            newGoalDescription,
        ].forEach(
            (input) => {
                input?.addEventListener(
                    "keydown",
                    (event) => {
                        if (
                            event.key ===
                                "Enter" &&
                            input ===
                                newGoalName
                        ) {
                            event.preventDefault();

                            submitNewGoal();
                        }
                    }
                );
            }
        );

        document.addEventListener(
            "keydown",
            (event) => {
                if (
                    event.key ===
                        "Escape" &&
                    addGoalPanel?.classList.contains(
                        "show"
                    )
                ) {
                    closeGoalModal();
                }
            }
        );
    }

    // ---------------------------------------------------------
    // Toast
    // ---------------------------------------------------------

    function showToast(
        message,
        success = true
    ) {
        if (
            !dashboardToast ||
            !toastMessage
        ) {
            console.log(
                "FitLyfe:",
                message
            );

            return;
        }

        toastMessage.textContent =
            message;

        dashboardToast.className =
            "dashboard-toast show " +
            (
                success
                    ? "success"
                    : "error"
            );

        if (toastTimer) {
            clearTimeout(
                toastTimer
            );
        }

        toastTimer =
            setTimeout(
                () => {
                    dashboardToast.classList.remove(
                        "show"
                    );
                },
                2800
            );
    }

    // ---------------------------------------------------------
    // Security
    // ---------------------------------------------------------

    function escapeHTML(value) {
        const div =
            document.createElement(
                "div"
            );

        div.textContent =
            String(value ?? "");

        return div.innerHTML;
    }

    // ---------------------------------------------------------
    // Public refresh API
    // ---------------------------------------------------------

    window.FitLyfeDashboard = {
        refresh: async () => {
            await loadCalendar();
            await loadDashboard();
        },

        getSelectedDate: () =>
            toDateKey(
                selectedDate
            ),
    };
});