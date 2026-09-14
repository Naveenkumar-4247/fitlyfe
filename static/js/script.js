/* =========================================================
   FITLYFE
   script.js
   GLOBAL + LANDING PAGE JAVASCRIPT
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       1. BOOTSTRAP NAVBAR
       Bootstrap 5 handles the mobile navbar.
       No custom navbar toggle required.
    ===================================================== */


    /* =====================================================
       2. BUTTON RIPPLE EFFECT
       Does NOT affect navbar toggler.
    ===================================================== */

    const buttons = document.querySelectorAll(
        "button:not(.modal-close):not(.navbar-toggler)"
    );

    buttons.forEach(function (button) {

        button.addEventListener("click", function (event) {

            const ripple = document.createElement("span");

            ripple.classList.add("button-ripple");

            const rect = button.getBoundingClientRect();

            const size = Math.max(
                rect.width,
                rect.height
            );

            ripple.style.width = size + "px";
            ripple.style.height = size + "px";

            ripple.style.left =
                (event.clientX - rect.left - size / 2) + "px";

            ripple.style.top =
                (event.clientY - rect.top - size / 2) + "px";

            button.appendChild(ripple);

            setTimeout(function () {

                if (ripple.parentElement) {
                    ripple.remove();
                }

            }, 700);

        });

    });


    /* =====================================================
       3. GLOBAL FADE-IN
       Used by other pages if they have .fade-in
    ===================================================== */

    const fadeElements =
        document.querySelectorAll(".fade-in");

    if (
        fadeElements.length > 0 &&
        "IntersectionObserver" in window
    ) {

        const fadeObserver =
            new IntersectionObserver(
                function (entries) {

                    entries.forEach(function (entry) {

                        if (entry.isIntersecting) {

                            entry.target.classList.add(
                                "visible"
                            );

                            fadeObserver.unobserve(
                                entry.target
                            );

                        }

                    });

                },
                {
                    threshold: 0.15
                }
            );

        fadeElements.forEach(function (element) {
            fadeObserver.observe(element);
        });

    } else {

        fadeElements.forEach(function (element) {
            element.classList.add("visible");
        });

    }


    /* =====================================================
       4. FLASH / TOAST MESSAGES
    ===================================================== */

    const toastMessages =
        document.querySelectorAll(".toast");

    toastMessages.forEach(function (toast) {

        /* Auto hide after 4 seconds */

        const hideToast = function () {

            if (!toast.parentElement) {
                return;
            }

            toast.style.opacity = "0";

            toast.style.transform =
                "translateX(50px)";

            setTimeout(function () {

                if (toast.parentElement) {
                    toast.remove();
                }

            }, 300);

        };

        setTimeout(hideToast, 4000);


        /* Manual close */

        const closeBtn =
            toast.querySelector(".toast-close");

        if (closeBtn) {

            closeBtn.addEventListener(
                "click",
                hideToast
            );

        }

    });


    /* =====================================================
       5. GLOBAL SCROLL TO TOP
       Works on every page
    ===================================================== */

    const backToTop =
        document.querySelector(
            "#scrollTopBtn, .scroll-top-btn, .back-to-top"
        );

    if (backToTop) {

        function updateBackToTop() {

            if (window.scrollY > 400) {

                backToTop.classList.add("show");

            } else {

                backToTop.classList.remove("show");

            }

        }


        /* Check immediately */

        updateBackToTop();


        /* Check while scrolling */

        window.addEventListener(
            "scroll",
            updateBackToTop,
            {
                passive: true
            }
        );


        /* Scroll to top */

        backToTop.addEventListener(
            "click",
            function () {

                window.scrollTo({

                    top: 0,

                    behavior: "smooth"

                });

            }
        );

    }


    /* =====================================================
       6. PREVENT DOUBLE FORM SUBMISSION
    ===================================================== */

    const forms =
        document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.addEventListener(
            "submit",
            function () {

                const submitButtons =
                    form.querySelectorAll(
                        'button[type="submit"], input[type="submit"]'
                    );

                submitButtons.forEach(
                    function (button) {

                        if (button.disabled) {
                            return;
                        }

                        button.dataset.originalText =
                            button.innerHTML ||
                            button.value;

                        if (button.tagName === "INPUT") {

                            button.value =
                                "Saving...";

                        } else {

                            button.innerHTML =
                                "Saving...";

                        }

                        button.disabled = true;

                    }
                );

            }
        );

    });


    /* =====================================================
       7. FITLYFE LANDING PAGE
       HERO SLIDER

       IMPORTANT:
       All landing classes start with "landing-"
       so they will NOT interfere with other pages.
    ===================================================== */

    const landingSlider =
        document.querySelector(
            ".landing-slider"
        );

    const landingSlides =
        document.querySelectorAll(
            ".landing-slider .landing-slide"
        );

    const landingPrev =
        document.querySelector(
            ".landing-slider .landing-prev"
        );

    const landingNext =
        document.querySelector(
            ".landing-slider .landing-next"
        );

    const landingDots =
        document.querySelectorAll(
            ".landing-slider .landing-dot"
        );


    /* Only run slider if landing page exists */

    if (
        landingSlider &&
        landingSlides.length > 0
    ) {

        let currentLandingSlide = 0;

        let autoSlide = null;

        let isAnimating = false;


        /* =================================================
           UPDATE DOTS
        ================================================= */

        function updateLandingDots() {

            landingDots.forEach(
                function (dot, index) {

                    dot.classList.toggle(
                        "landing-dot-active",
                        index === currentLandingSlide
                    );

                    dot.setAttribute(
                        "aria-current",
                        index === currentLandingSlide
                            ? "true"
                            : "false"
                    );

                }
            );

        }


        /* =================================================
           SHOW LANDING SLIDE
        ================================================= */

        function showLandingSlide(index) {

            if (isAnimating) {
                return;
            }

            if (index >= landingSlides.length) {
                index = 0;
            }

            if (index < 0) {
                index =
                    landingSlides.length - 1;
            }

            if (index === currentLandingSlide) {

                updateLandingDots();

                return;
            }

            isAnimating = true;


            /* Remove active class */

            landingSlides.forEach(
                function (slide) {

                    slide.classList.remove(
                        "landing-slide-active"
                    );

                    slide.classList.remove(
                        "landing-slide-previous"
                    );

                }
            );


            /* Current slide */

            const previousSlide =
                landingSlides[currentLandingSlide];

            previousSlide.classList.add(
                "landing-slide-previous"
            );


            /* Update current */

            currentLandingSlide = index;


            /* Activate new slide */

            landingSlides[currentLandingSlide]
                .classList.add(
                    "landing-slide-active"
                );


            updateLandingDots();


            /* Allow next animation */

            setTimeout(
                function () {

                    landingSlides.forEach(
                        function (slide) {

                            slide.classList.remove(
                                "landing-slide-previous"
                            );

                        }
                    );

                    isAnimating = false;

                },
                900
            );

        }


        /* =================================================
           NEXT SLIDE
        ================================================= */

        function nextLandingSlide() {

            showLandingSlide(
                currentLandingSlide + 1
            );

        }


        /* =================================================
           PREVIOUS SLIDE
        ================================================= */

        function previousLandingSlide() {

            showLandingSlide(
                currentLandingSlide - 1
            );

        }


        /* =================================================
           AUTO SLIDER
        ================================================= */

        function startLandingAutoSlide() {

            clearInterval(autoSlide);

            autoSlide = setInterval(
                function () {

                    nextLandingSlide();

                },
                6000
            );

        }


        function stopLandingAutoSlide() {

            clearInterval(autoSlide);

            autoSlide = null;

        }


        function restartLandingAutoSlide() {

            stopLandingAutoSlide();

            startLandingAutoSlide();

        }


        /* =================================================
           NEXT BUTTON
        ================================================= */

        if (landingNext) {

            landingNext.addEventListener(
                "click",
                function () {

                    nextLandingSlide();

                    restartLandingAutoSlide();

                }
            );

        }


        /* =================================================
           PREVIOUS BUTTON
        ================================================= */

        if (landingPrev) {

            landingPrev.addEventListener(
                "click",
                function () {

                    previousLandingSlide();

                    restartLandingAutoSlide();

                }
            );

        }


        /* =================================================
           DOT NAVIGATION
        ================================================= */

        landingDots.forEach(
            function (dot, index) {

                dot.addEventListener(
                    "click",
                    function () {

                        showLandingSlide(index);

                        restartLandingAutoSlide();

                    }
                );

            }
        );


        /* =================================================
           PAUSE ON MOUSE ENTER
        ================================================= */

        landingSlider.addEventListener(
            "mouseenter",
            function () {

                stopLandingAutoSlide();

            }
        );


        /* =================================================
           RESUME ON MOUSE LEAVE
        ================================================= */

        landingSlider.addEventListener(
            "mouseleave",
            function () {

                startLandingAutoSlide();

            }
        );


        /* =================================================
           KEYBOARD CONTROLS
        ================================================= */

        document.addEventListener(
            "keydown",
            function (event) {

                /*
                 * Don't control slider while user
                 * is typing in an input.
                 */

                const activeElement =
                    document.activeElement;

                if (
                    activeElement &&
                    (
                        activeElement.tagName === "INPUT" ||
                        activeElement.tagName === "TEXTAREA" ||
                        activeElement.tagName === "SELECT"
                    )
                ) {

                    return;

                }


                if (
                    event.key === "ArrowRight"
                ) {

                    nextLandingSlide();

                    restartLandingAutoSlide();

                }


                if (
                    event.key === "ArrowLeft"
                ) {

                    previousLandingSlide();

                    restartLandingAutoSlide();

                }

            }
        );


        /* =================================================
           TOUCH / SWIPE SUPPORT
        ================================================= */

        let touchStartX = 0;

        let touchEndX = 0;


        landingSlider.addEventListener(
            "touchstart",
            function (event) {

                touchStartX =
                    event.changedTouches[0].screenX;

            },
            {
                passive: true
            }
        );


        landingSlider.addEventListener(
            "touchend",
            function (event) {

                touchEndX =
                    event.changedTouches[0].screenX;

                const difference =
                    touchStartX - touchEndX;


                /* Swipe left */

                if (difference > 50) {

                    nextLandingSlide();

                    restartLandingAutoSlide();

                }


                /* Swipe right */

                if (difference < -50) {

                    previousLandingSlide();

                    restartLandingAutoSlide();

                }

            },
            {
                passive: true
            }
        );


        /* =================================================
           INITIALIZE
        ================================================= */

        landingSlides.forEach(
            function (slide) {

                slide.classList.remove(
                    "landing-slide-active"
                );

            }
        );


        currentLandingSlide = 0;


        landingSlides[0].classList.add(
            "landing-slide-active"
        );


        updateLandingDots();

        startLandingAutoSlide();

    }


    /* =====================================================
       8. LANDING PAGE SCROLL REVEAL
    ===================================================== */

    const landingRevealElements =
        document.querySelectorAll(
            ".landing-reveal"
        );


    if (
        landingRevealElements.length > 0 &&
        "IntersectionObserver" in window
    ) {

        const landingRevealObserver =
            new IntersectionObserver(
                function (entries) {

                    entries.forEach(
                        function (entry) {

                            if (
                                entry.isIntersecting
                            ) {

                                entry.target.classList.add(
                                    "landing-reveal-visible"
                                );

                                landingRevealObserver.unobserve(
                                    entry.target
                                );

                            }

                        }
                    );

                },
                {
                    threshold: 0.15,

                    rootMargin:
                        "0px 0px -50px 0px"
                }
            );


        landingRevealElements.forEach(
            function (element) {

                landingRevealObserver.observe(
                    element
                );

            }
        );

    } else {

        landingRevealElements.forEach(
            function (element) {

                element.classList.add(
                    "landing-reveal-visible"
                );

            }
        );

    }


    /* =====================================================
       9. LANDING PAGE PARALLAX

       Lightweight effect.
       Does not affect other pages.
    ===================================================== */

    const landingHero =
        document.querySelector(
            ".landing-hero"
        );


    if (landingHero) {

        let ticking = false;


        function updateLandingParallax() {

            const scrollPosition =
                window.scrollY;


            if (
                scrollPosition <
                window.innerHeight
            ) {

                landingHero.style.setProperty(
                    "--landing-scroll",
                    scrollPosition
                );

            }

            ticking = false;

        }


        window.addEventListener(
            "scroll",
            function () {

                if (!ticking) {

                    window.requestAnimationFrame(
                        updateLandingParallax
                    );

                    ticking = true;

                }

            },
            {
                passive: true
            }
        );

    }


    /* =====================================================
       10. LANDING PAGE BUTTON MICRO ANIMATION
    ===================================================== */

    const landingButtons =
        document.querySelectorAll(
            ".landing-button"
        );


    landingButtons.forEach(
        function (button) {

            button.addEventListener(
                "mouseenter",
                function () {

                    button.classList.add(
                        "landing-button-hover"
                    );

                }
            );


            button.addEventListener(
                "mouseleave",
                function () {

                    button.classList.remove(
                        "landing-button-hover"
                    );

                }
            );

        }
    );


    /* =====================================================
       11. LANDING PAGE IMAGE TILT

       Only elements using .landing-tilt
    ===================================================== */

    const landingTiltElements =
        document.querySelectorAll(
            ".landing-tilt"
        );


    landingTiltElements.forEach(
        function (element) {

            element.addEventListener(
                "mousemove",
                function (event) {

                    const rect =
                        element.getBoundingClientRect();

                    const x =
                        event.clientX - rect.left;

                    const y =
                        event.clientY - rect.top;


                    const centerX =
                        rect.width / 2;

                    const centerY =
                        rect.height / 2;


                    const rotateX =
                        ((y - centerY) /
                            centerY) * -3;

                    const rotateY =
                        ((x - centerX) /
                            centerX) * 3;


                    element.style.transform =
                        "perspective(1000px) " +
                        "rotateX(" +
                        rotateX +
                        "deg) rotateY(" +
                        rotateY +
                        "deg) translateY(-5px)";

                }
            );


            element.addEventListener(
                "mouseleave",
                function () {

                    element.style.transform =
                        "";

                }
            );

        }
    );


    /* =====================================================
       12. REDUCE ANIMATION FOR ACCESSIBILITY
    ===================================================== */

    const prefersReducedMotion =
        window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        );


    if (prefersReducedMotion.matches) {

        document.documentElement.classList.add(
            "reduced-motion"
        );

    }

});


/* =========================================================
   FITLYFE 2.0 — SCROLL REVEALS + MICRO INTERACTIONS
========================================================= */

(() => {

    const targets = document.querySelectorAll(
        ".landing-slide-content, " +
        ".landing-feature-card, " +
        ".main-module, " +
        ".dashboard-card, " +
        ".meal-card, " +
        ".bmi-card, " +
        ".profile-setup-card, " +
        ".login-panel, " +
        ".register-panel, " +
        "section > h1, " +
        "section > h2"
    );


    targets.forEach(el =>
        el.classList.add("fy-reveal")
    );


    if ("IntersectionObserver" in window) {

        const io =
            new IntersectionObserver(
                entries => {

                    entries.forEach(entry => {

                        if (entry.isIntersecting) {

                            entry.target.classList.add(
                                "fy-visible"
                            );

                            io.unobserve(
                                entry.target
                            );

                        }

                    });

                },
                {
                    threshold: 0.08
                }
            );


        targets.forEach(el =>
            io.observe(el)
        );

    } else {

        targets.forEach(el =>
            el.classList.add("fy-visible")
        );

    }

})();


/* =========================================================
   ABOUT PAGE
   "MEET MY TEAM" BUTTON SUPPORT

   IMPORTANT:
   The main team open/close animation is handled by
   the inline JavaScript inside about.html.

   This section only adds a small safety enhancement:
   when the About page is opened directly with #team,
   the team section is opened automatically.
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const meetTeamButton =
        document.querySelector("#meetTeamButton");

    const teamSection =
        document.querySelector("#team");


    if (
        meetTeamButton &&
        teamSection &&
        window.location.hash === "#team"
    ) {

        /*
         * Give about.html's own script a moment
         * to initialize first.
         */

        setTimeout(function () {

            if (
                !teamSection.classList.contains(
                    "team-open"
                )
            ) {

                meetTeamButton.click();

            }

        }, 150);

    }

});