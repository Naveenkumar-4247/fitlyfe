/* =========================================================
   FITLYFE DETAIL PAGE
   PROFILE MODAL + PREMIUM INTERACTIONS
========================================================= */

document.addEventListener("DOMContentLoaded", function () {


    /* =====================================================
       PROFILE MODAL
    ====================================================== */

    const profileButton =
        document.getElementById("openProfileModal");

    const profileModal =
        document.getElementById("profileModal");

    const modalBackdrop =
        document.getElementById("modalBackdrop");

    const modalClose =
        document.getElementById("modalClose");


    /* =====================================================
       OPEN MODAL
    ====================================================== */

    function openProfile() {

        if (!profileModal) {
            return;
        }

        profileModal.classList.add("active");

        profileModal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "profile-modal-open"
        );

        document.body.style.overflow = "hidden";


        /* Small animation for detail boxes */

        const details =
            profileModal.querySelectorAll(
                ".popup-detail"
            );

        details.forEach(function (detail, index) {

            detail.style.opacity = "0";

            detail.style.transform =
                "translateY(10px)";

            setTimeout(function () {

                detail.style.transition =
                    "opacity 0.35s ease, transform 0.35s ease";

                detail.style.opacity = "1";

                detail.style.transform =
                    "translateY(0)";

            }, 100 + (index * 45));

        });

    }


    /* =====================================================
       CLOSE MODAL
    ====================================================== */

    function closeProfile() {

        if (!profileModal) {
            return;
        }

        profileModal.classList.remove("active");

        profileModal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "profile-modal-open"
        );

        document.body.style.overflow = "";

    }


    /* =====================================================
       PROFILE BUTTON
    ====================================================== */

    if (profileButton) {

        profileButton.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                openProfile();

            }
        );

    }


    /* =====================================================
       CLOSE BUTTON
    ====================================================== */

    if (modalClose) {

        modalClose.addEventListener(
            "click",
            function () {

                closeProfile();

            }
        );

    }


    /* =====================================================
       BACKDROP CLOSE
    ====================================================== */

    if (modalBackdrop) {

        modalBackdrop.addEventListener(
            "click",
            function () {

                closeProfile();

            }
        );

    }


    /* =====================================================
       ESCAPE KEY
    ====================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape" &&
                profileModal &&
                profileModal.classList.contains("active")
            ) {

                closeProfile();

            }

        }
    );



    /* =====================================================
       MODULE CARD MOUSE GLOW
    ====================================================== */

    const moduleCards =
        document.querySelectorAll(
            ".main-module"
        );


    moduleCards.forEach(function (card) {

        card.addEventListener(
            "mousemove",
            function (event) {

                const rect =
                    card.getBoundingClientRect();

                const x =
                    event.clientX - rect.left;

                const y =
                    event.clientY - rect.top;


                const xPercent =
                    (x / rect.width) * 100;

                const yPercent =
                    (y / rect.height) * 100;


                card.style.background =
                    `
                    radial-gradient(
                        circle at
                        ${xPercent}% ${yPercent}%,
                        rgba(99, 230, 163, 0.10),
                        transparent 38%
                    ),
                    linear-gradient(
                        145deg,
                        rgba(10, 25, 17, 0.94),
                        rgba(3, 10, 7, 0.95)
                    )
                    `;

            }
        );


        card.addEventListener(
            "mouseleave",
            function () {

                card.style.background = "";

            }
        );

    });



    /* =====================================================
       PROFILE CARD SUBTLE TILT
    ====================================================== */

    if (profileButton) {

        profileButton.addEventListener(
            "mousemove",
            function (event) {

                const rect =
                    profileButton.getBoundingClientRect();

                const x =
                    event.clientX - rect.left;

                const y =
                    event.clientY - rect.top;


                const rotateY =
                    ((x - rect.width / 2) /
                        rect.width) * 3;

                const rotateX =
                    ((y - rect.height / 2) /
                        rect.height) * -3;


                profileButton.style.transform =
                    `
                    perspective(700px)
                    rotateX(${rotateX}deg)
                    rotateY(${rotateY}deg)
                    translateY(-4px)
                    `;

            }
        );


        profileButton.addEventListener(
            "mouseleave",
            function () {

                profileButton.style.transform =
                    "";

            }
        );

    }



    /* =====================================================
       SCROLL REVEAL
    ====================================================== */

    const revealElements =
        document.querySelectorAll(
            ".module-heading, .detail-bottom"
        );


    if (
        revealElements.length &&
        "IntersectionObserver" in window
    ) {

        const observer =
            new IntersectionObserver(
                function (entries) {

                    entries.forEach(
                        function (entry) {

                            if (
                                entry.isIntersecting
                            ) {

                                entry.target.classList.add(
                                    "revealed"
                                );

                                observer.unobserve(
                                    entry.target
                                );

                            }

                        }
                    );

                },
                {
                    threshold: 0.15
                }
            );


        revealElements.forEach(
            function (element) {

                observer.observe(element);

            }
        );

    }



    /* =====================================================
       PREVENT CARD DOUBLE CLICK EFFECT
    ====================================================== */

    moduleCards.forEach(function (card) {

        card.addEventListener(
            "click",
            function () {

                card.classList.add(
                    "module-clicked"
                );

                setTimeout(
                    function () {

                        card.classList.remove(
                            "module-clicked"
                        );

                    },
                    500
                );

            }
        );

    });


});