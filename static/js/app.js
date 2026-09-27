(function () {
    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("sidebarOverlay");
    var toggle = document.getElementById("sidebarToggle");
    var closeBtn = document.getElementById("sidebarClose");

    function isMobile() {
        return window.matchMedia("(max-width: 991px)").matches;
    }

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add("open");
        if (overlay) overlay.hidden = false;
        document.body.classList.add("sidebar-open");
    }

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove("open");
        if (overlay) overlay.hidden = true;
        document.body.classList.remove("sidebar-open");
    }

    if (toggle) {
        toggle.addEventListener("click", function () {
            if (sidebar.classList.contains("open")) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    if (closeBtn) closeBtn.addEventListener("click", closeSidebar);
    if (overlay) overlay.addEventListener("click", closeSidebar);

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") closeSidebar();
    });

    if (sidebar) {
        sidebar.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                if (isMobile()) closeSidebar();
            });
        });
    }

    window.addEventListener("resize", function () {
        if (!isMobile()) closeSidebar();
    });
})();
