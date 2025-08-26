const SUPPORTED_LANGS = {
  en: "English",
  hi: "Hindi",
  kn: "Kannada",
  te: "Telugu",
  ta: "Tamil",
  ml: "Malayalam",
  mr: "Marathi",
  gu: "Gujarati",
  bn: "Bengali",
  pa: "Punjabi",
  or: "Odia",
  ur: "Urdu",
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const uploadForm = $("#uploadForm");
const fileInput = $("#fileInput");
const statusBox = $("#status");
const playerSection = $("#playerSection");
const videoEl = $("#player");
const searchInput = $("#searchInput");
const searchBtn = $("#searchBtn");
const langSelect = $("#langSelect");
const hitsList = $("#hitsList");
const langsDiv = $("#langs");

let current = { video_id: null, tracks: [], video_url: null };

// Populate language toggles
for (const [code, name] of Object.entries(SUPPORTED_LANGS)) {
  const label = document.createElement("label");
  label.innerHTML = `<input type="checkbox" data-lang="${code}" checked /> ${name}`;
  langsDiv.appendChild(label);
}

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = fileInput.files[0];
  if (!file) return;

  const selected = $$('input[type="checkbox"][data-lang]:checked').map(cb => cb.getAttribute("data-lang"));
  const allChecked = $$('input[data-lang="all"]')[0]?.checked;
  const langs = allChecked ? "" : selected.join(",");

  const fd = new FormData();
  fd.append("file", file);

  statusBox.textContent = "Uploading and transcribing… This may take a few minutes depending on video length.";
  try {
    const res = await fetch(`/api/upload${langs ? `?langs=${encodeURIComponent(langs)}` : ""}`, {
      method: "POST",
      body: fd,
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    current = data;
    setupPlayer(data);
    statusBox.textContent = "Done. Use the search to jump to keywords.";
  } catch (err) {
    console.error(err);
    statusBox.textContent = "Upload failed: " + (err.message || err);
  }
});

function setupPlayer(data) {
  playerSection.classList.remove("hidden");
  videoEl.src = data.video_url;
  // Remove old tracks
  $$("#player track").forEach(t => t.remove());
  // Add tracks
  langSelect.innerHTML = "";
  for (const t of data.tracks) {
    const trackEl = document.createElement("track");
    trackEl.setAttribute("kind", "subtitles");
    trackEl.setAttribute("srclang", t.lang);
    trackEl.setAttribute("label", t.label);
    trackEl.setAttribute("src", t.url);
    trackEl.default = t.lang === "en";
    videoEl.appendChild(trackEl);

    const opt = document.createElement("option");
    opt.value = t.lang;
    opt.textContent = t.label;
    langSelect.appendChild(opt);
  }
}

function formatTime(sec) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  const hh = String(h).padStart(2,"0");
  const mm = String(m).padStart(2,"0");
  const ss = String(s).padStart(2,"0");
  return `${hh}:${mm}:${ss}`;
}

searchBtn.addEventListener("click", async () => {
  const q = searchInput.value.trim();
  if (!q || !current.video_id) return;
  const lang = langSelect.value || "en";
  $("#searchInfo").textContent = "Searching…";
  hitsList.innerHTML = "";
  try {
    const res = await fetch(`/api/search?video_id=${encodeURIComponent(current.video_id)}&lang=${encodeURIComponent(lang)}&q=${encodeURIComponent(q)}`);
    const data = await res.json();
    const hits = data.hits || [];
    $("#searchInfo").textContent = `${hits.length} hits`;
    if (hits.length) {
      // Seek to first hit
      videoEl.currentTime = hits[0];
      videoEl.play().catch(()=>{});
      // Show chips
      for (const t of hits) {
        const chip = document.createElement("div");
        chip.className = "timechip";
        chip.textContent = formatTime(t);
        chip.addEventListener("click", () => {
          videoEl.currentTime = t;
          videoEl.play().catch(()=>{});
        });
        hitsList.appendChild(chip);
      }
    }
  } catch (e) {
    $("#searchInfo").textContent = "Search failed.";
  }
});
