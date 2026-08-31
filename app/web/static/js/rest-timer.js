// Floating rest countdown for the workout detail page. No dependencies.
(function () {
  "use strict";

  var el = document.getElementById("rest-timer");
  if (!el) return;

  var timeEl = document.getElementById("rest-time");
  var toggleEl = document.getElementById("rest-toggle");

  var labels = {};
  try {
    labels = JSON.parse(el.getAttribute("data-labels") || "{}");
  } catch (e) {
    labels = {};
  }

  var MIN = 15;
  var MAX = 600;
  var total = clamp(parseInt(el.getAttribute("data-default"), 10) || 120);
  var remaining = total;
  var handle = null;
  var running = false;

  function clamp(value) {
    return Math.max(MIN, Math.min(MAX, value));
  }

  function format(seconds) {
    var whole = Math.max(0, Math.round(seconds));
    var mins = Math.floor(whole / 60);
    var secs = whole % 60;
    return mins + ":" + (secs < 10 ? "0" : "") + secs;
  }

  function render() {
    timeEl.textContent = format(remaining);
    toggleEl.textContent = running ? labels.pause || "Pause" : labels.start || "Start";
    el.classList.toggle("is-running", running);
    el.classList.toggle("is-done", !running && remaining <= 0);
  }

  function tick() {
    remaining -= 1;
    if (remaining <= 0) {
      remaining = 0;
      stop();
      beep();
    }
    render();
  }

  function start() {
    if (running) return;
    if (remaining <= 0) remaining = total;
    running = true;
    handle = window.setInterval(tick, 1000);
    render();
  }

  function stop() {
    running = false;
    if (handle) window.clearInterval(handle);
    handle = null;
    render();
  }

  function reset() {
    stop();
    remaining = total;
    render();
  }

  function adjust(delta) {
    total = clamp(total + delta);
    remaining = running ? Math.max(0, remaining + delta) : total;
    render();
  }

  function beep() {
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      var ctx = new Ctx();
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = "sine";
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.start();
      osc.stop(ctx.currentTime + 0.4);
    } catch (e) {
      /* audio is a nice-to-have */
    }
  }

  el.addEventListener("click", function (event) {
    var button = event.target.closest("button");
    if (!button) return;
    var action = button.getAttribute("data-rest");
    if (action === "toggle") {
      running ? stop() : start();
    } else if (action === "reset") {
      reset();
    } else if (action === "adjust") {
      adjust(parseInt(button.getAttribute("data-delta"), 10) || 0);
    }
  });

  render();
})();
