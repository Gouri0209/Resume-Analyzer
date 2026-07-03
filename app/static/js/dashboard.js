(function () {
  const CIRCUMFERENCE = 2 * Math.PI * 52; // r=52

  function animateScoreCircles() {
    const circles = document.querySelectorAll(".score-circle, .mini-score-circle");
    circles.forEach((el) => {
      const score = parseFloat(el.getAttribute("data-score")) || 0;
      const progress = el.querySelector(".progress");
      if (!progress) return;

      const offset = CIRCUMFERENCE - (Math.min(Math.max(score, 0), 100) / 100) * CIRCUMFERENCE;

      let color = getComputedStyle(document.documentElement).getPropertyValue("--color-danger").trim();
      if (score >= 75) {
        color = getComputedStyle(document.documentElement).getPropertyValue("--color-success").trim();
      } else if (score >= 50) {
        color = getComputedStyle(document.documentElement).getPropertyValue("--color-warning").trim();
      }

      progress.style.stroke = color || "#4f46e5";
      progress.style.strokeDasharray = `${CIRCUMFERENCE}`;
      progress.style.strokeDashoffset = `${CIRCUMFERENCE}`;

      requestAnimationFrame(() => {
        setTimeout(() => {
          progress.style.strokeDashoffset = `${offset}`;
        }, 100);
      });
    });
  }

  function renderSkillsChart() {
    const canvas = document.getElementById("skillsChart");
    if (!canvas || typeof Chart === "undefined" || !window.__ANALYSIS__) return;

    const { matched, missing } = window.__ANALYSIS__;
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const textColor = isDark ? "#f3f4f6" : "#1f2937";

    new Chart(canvas.getContext("2d"), {
      type: "doughnut",
      data: {
        labels: ["Matched Skills", "Missing Skills"],
        datasets: [
          {
            data: [matched, missing],
            backgroundColor: ["#10b981", "#ef4444"],
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: textColor, font: { family: "Inter", weight: "600" } },
          },
        },
        cutout: "65%",
      },
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    animateScoreCircles();
    renderSkillsChart();
  });
})();
