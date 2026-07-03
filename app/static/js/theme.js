(function () {
  const root = document.documentElement;
  const toggleBtn = document.getElementById("theme-toggle");
  const sunIcon = document.getElementById("icon-sun");
  const moonIcon = document.getElementById("icon-moon");

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    if (sunIcon && moonIcon) {
      sunIcon.style.display = theme === "dark" ? "none" : "block";
      moonIcon.style.display = theme === "dark" ? "block" : "none";
    }
  }

  const stored = localStorage.getItem("theme");
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(stored || (prefersDark ? "dark" : "light"));

  if (toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      const current = root.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      localStorage.setItem("theme", next);
    });
  }
})();
