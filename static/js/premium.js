/* FitLyfe global micro-interactions */
document.addEventListener("DOMContentLoaded", () => {
    const progress = document.getElementById("pageProgress");

    function updateProgress() {
        if (!progress) return;
        const max = document.documentElement.scrollHeight - window.innerHeight;
        const value = max > 0 ? (window.scrollY / max) * 100 : 0;
        progress.style.width = `${Math.min(100, Math.max(0, value))}%`;
    }

    window.addEventListener("scroll", updateProgress, { passive: true });
    updateProgress();

    // Add a lightweight reveal effect without requiring page-specific JS.
    const revealTargets = document.querySelectorAll(
        ".dashboard-card, .tool-card, .main-module, .feature-card, " +
        ".profile-setup-card, .login-card, .register-panel, .bmi-card, " +
        ".meal-card, .detail-bottom"
    );

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add("fit-revealed");
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.08 });

        revealTargets.forEach((node) => {
            node.classList.add("fit-reveal");
            observer.observe(node);
        });
    }
});
