document.addEventListener("DOMContentLoaded", () => {
  const vals   = [100, -50, -50, 100, -50, 0];
  const labels = ["+100", "-50", "-50", "+100", "-50", "0"];
  const colors = ["#43a047", "#e53935", "#e53935", "#1e88e5", "#e53935", "#9e9e9e"];

  const ctx = new Chart(document.getElementById("wheel"), {
    plugins: [ChartDataLabels],
    type: "pie",
    data: { labels, datasets: [{ backgroundColor: colors, data: Array(6).fill(16) }] },
    options: {
      responsive: true,
      animation: { duration: 0 },
      plugins: {
        tooltip: false,
        legend: { display: false },
        datalabels: {
          color: "#000",
          font: { size: 18 },
          formatter: (v, c) => c.chart.data.labels[c.dataIndex]
        }
      }
    }
  });

  const ptsBox   = document.getElementById("points");
  const maskBox  = document.getElementById("display");
  const resBox   = document.getElementById("result");
  const usedBox  = document.getElementById("used");
  const guessBtn = document.getElementById("guess-letter-btn");
  const wordBtn  = document.getElementById("guess-word-btn");
  const inpL     = document.getElementById("letter");
  const inpW     = document.getElementById("whole");

  const used = new Set();
  const updateUsed = () => usedBox.textContent = "Used letters: " + (used.size ? [...used].join(", ").toUpperCase() : "–");

  let spinning = false;
  autoSpin();

  async function post(url, body) {
    return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(r => r.json());
  }

  function end(msg) {
    resBox.textContent = msg;
    guessBtn.disabled = wordBtn.disabled = true;
  }

  function autoSpin() {
    if (spinning) return;
    spinning = true;
    guessBtn.disabled = wordBtn.disabled = true;
    resBox.textContent = "";

    const slice = Math.floor(Math.random() * 6);
    const target = slice * 60 + 30;
    let ang = Math.random() * 360;
    let step = 25;

    const id = setInterval(async () => {
      ang = (ang + step) % 360;
      ctx.options.rotation = ang;
      ctx.update();

      if (step > 2) step -= 0.5;
      if (step <= 2 && Math.abs(ang - target) <= step / 2) {
        clearInterval(id);
        ctx.options.rotation = target;
        ctx.update();

        const delta = vals[slice];
        const r = await post("/spin", { delta });
        ptsBox.textContent = r.points;

        if (r.lost) { end("💀 No points left"); return; }

        spinning = false;
        if (r.allow) {
          guessBtn.disabled = wordBtn.disabled = false;
        } else {
          autoSpin();
        }
      }
    }, 16);
  }

  guessBtn.addEventListener("click", async () => {
    const l = inpL.value.trim().toLowerCase();
    inpL.value = "";
    if (!l.match(/^[a-z]$/) || used.has(l) || spinning) return;
    used.add(l); updateUsed();
    const r = await post("/guess_letter", { letter: l });
    ptsBox.textContent = r.points;
    maskBox.textContent = r.mask;
    if (r.finished) end("🎉 You guessed it!");
    else if (r.lost) end("💀 No points left");
    else autoSpin();
  });

  wordBtn.addEventListener("click", async () => {
    const w = inpW.value.trim().toLowerCase();
    if (!w || spinning) return;
    const r = await post("/guess_word", { attempt: w });
    if (r.status === "used") { alert("full-word try already used"); return; }
    ptsBox.textContent = r.points;
    if (r.display) maskBox.textContent = r.display;
    end(r.status === "win" ? "🎉 Correct!" : "❌ Wrong");
  });
});
