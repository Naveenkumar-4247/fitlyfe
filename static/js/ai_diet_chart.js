(() => {
    "use strict";

    const form = document.getElementById("dietForm");
    const generateBtn = document.getElementById("generateBtn");
    const formError = document.getElementById("formError");
    const resultSection = document.getElementById("dietResultSection");
    const emptyState = document.getElementById("emptyState");
    const planOutput = document.getElementById("planOutput");
    const planTitle = document.getElementById("planTitle");
    const planSummary = document.getElementById("planSummary");
    const mealGrid = document.getElementById("mealGrid");
    const tipsList = document.getElementById("tipsList");

    const caloriesValue = document.getElementById("caloriesValue");
    const proteinValue = document.getElementById("proteinValue");
    const carbsValue = document.getElementById("carbsValue");
    const fatValue = document.getElementById("fatValue");
    const waterValue = document.getElementById("waterValue");
    const hydrationText = document.getElementById("hydrationText");
    const safetyNote = document.getElementById("safetyNote");

    const printPlanBtn = document.getElementById("printPlanBtn");
    const newPlanBtn = document.getElementById("newPlanBtn");

    function setLoading(isLoading) {
        generateBtn.disabled = isLoading;
        generateBtn.classList.toggle("loading", isLoading);
    }

    function showError(message) {
        formError.textContent = message || "";
    }

    function escapeHtml(value) {
        const div = document.createElement("div");
        div.textContent = value ?? "";
        return div.innerHTML;
    }

    function renderPlan(plan) {
        const nutrition = plan.nutrition || {};

        planTitle.textContent = plan.title || "Your Personalized Diet Plan";
        planSummary.textContent = plan.summary || "";

        caloriesValue.textContent = nutrition.calories ?? "--";
        proteinValue.textContent = nutrition.protein_g ?? "--";
        carbsValue.textContent = nutrition.carbs_g ?? "--";
        fatValue.textContent = nutrition.fat_g ?? "--";
        waterValue.textContent = nutrition.water_l ?? "--";

        mealGrid.innerHTML = "";

        (plan.meals || []).forEach((meal, index) => {
            const foods = (meal.foods || [])
                .map(food => `<li>${escapeHtml(food)}</li>`)
                .join("");

            mealGrid.insertAdjacentHTML(
                "beforeend",
                `
                <article class="meal-card">
                    <div class="meal-number">${String(index + 1).padStart(2, "0")}</div>
                    <div class="meal-main">
                        <div class="meal-top">
                            <div>
                                <span class="meal-time">${escapeHtml(meal.time)}</span>
                                <h4>${escapeHtml(meal.name)}</h4>
                            </div>
                            <span class="meal-calories">${escapeHtml(meal.calories)} kcal</span>
                        </div>
                        <ul>${foods}</ul>
                        <span class="meal-protein">${escapeHtml(meal.protein_g)} g protein</span>
                    </div>
                </article>
                `
            );
        });

        hydrationText.textContent = plan.hydration || "";

        tipsList.innerHTML = "";
        (plan.tips || []).forEach(tip => {
            tipsList.insertAdjacentHTML(
                "beforeend",
                `<li>${escapeHtml(tip)}</li>`
            );
        });

        safetyNote.textContent = plan.safety_note || "";

        emptyState.classList.add("hidden");
        planOutput.classList.remove("hidden");
        resultSection.classList.add("has-plan");

        resultSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    async function generatePlan() {
        showError("");
        setLoading(true);

        const formData = new FormData(form);
        const payload = Object.fromEntries(formData.entries());

        try {
            const response = await fetch("/api/diet-plan/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || "Unable to generate the diet plan."
                );
            }

            renderPlan(data.plan);
        } catch (error) {
            console.error(error);
            showError(error.message || "Something went wrong.");
        } finally {
            setLoading(false);
        }
    }

    form.addEventListener("submit", event => {
        event.preventDefault();
        generatePlan();
    });

    printPlanBtn.addEventListener("click", () => {
        if (planOutput.classList.contains("hidden")) {
            showError("Generate a plan before printing.");
            return;
        }
        window.print();
    });

    newPlanBtn.addEventListener("click", () => {
        document.getElementById("dietForm").scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    });
})();
