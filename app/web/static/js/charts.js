// Shared Chart.js theme + helpers. Individual pages read a JSON island and
// call the builders below.
(function () {
  "use strict";
  if (!window.Chart) return;

  var root = getComputedStyle(document.documentElement);
  function token(name, fallback) {
    return (root.getPropertyValue(name) || "").trim() || fallback;
  }

  var palette = {
    ink: token("--text", "#e6edf3"),
    muted: token("--text-muted", "#9aa7b4"),
    grid: token("--border", "#2a313c"),
    accent: token("--accent", "#f5a623"),
    accentStrong: token("--accent-strong", "#ff7a18"),
    series: ["#f5a623", "#4a90d9", "#3fb8a6", "#a884e0", "#e0645a", "#6ac36a"],
  };

  Chart.defaults.color = palette.muted;
  Chart.defaults.borderColor = palette.grid;
  Chart.defaults.font.family = (getComputedStyle(document.body).fontFamily) || "system-ui";
  Chart.defaults.maintainAspectRatio = false;
  Chart.defaults.plugins.legend.labels.color = palette.ink;

  function json(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }

  function lineChart(canvasId, labels, datasets) {
    var el = document.getElementById(canvasId);
    if (!el) return;
    new Chart(el, {
      type: "line",
      data: { labels: labels, datasets: datasets },
      options: {
        spanGaps: true,
        interaction: { mode: "index", intersect: false },
        scales: {
          x: { grid: { color: palette.grid } },
          y: { grid: { color: palette.grid }, beginAtZero: false },
        },
      },
    });
  }

  function barChart(canvasId, labels, label, values, color, opts) {
    var el = document.getElementById(canvasId);
    if (!el) return;
    var yTicks = (opts && opts.integer) ? { precision: 0, stepSize: 1 } : {};
    new Chart(el, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{ label: label, data: values, backgroundColor: color || palette.accent }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: palette.grid }, beginAtZero: true, ticks: yTicks },
        },
      },
    });
  }

  function doughnutChart(canvasId, labels, values) {
    var el = document.getElementById(canvasId);
    if (!el) return;
    new Chart(el, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{ data: values, backgroundColor: palette.series, borderColor: palette.grid }],
      },
      options: { plugins: { legend: { position: "right" } } },
    });
  }

  window.gymCharts = {
    palette: palette,
    json: json,
    line: lineChart,
    bar: barChart,
    doughnut: doughnutChart,
  };
})();
