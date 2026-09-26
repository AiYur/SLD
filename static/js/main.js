/* =========================================================================
   Sweet Diagnosis — front-end logic
   Plain JavaScript, no framework and no CDN, so the page runs offline.
   The browser only collects the image and draws the result; every model
   runs in Python on this computer.
   ========================================================================= */

(function () {
  "use strict";

  // ---------------------------------------------------------------- i18n
  const I18N = {
    en: {
      tagline: "Sugarcane leaf disease detection · 5-model CNN comparison",
      connecting: "Connecting…", online: "Server ready", offlineOk: "Offline ready",
      serverDown: "Server unreachable",
      leafImage: "Leaf image", dropHere: "Drop a leaf photo here",
      dropSub: "or click to browse · JPG, PNG · max 16 MB",
      choose: "Choose image", camera: "Use camera", capture: "Capture", clear: "Clear",
      model: "Model", analyze: "Analyze leaf", compareAll: "Compare all models",
      hint: "Tip: fill the frame with a single leaf, in even daylight, against a plain background.",
      result: "Result", emptyMain: "No scan yet",
      emptySub: "Choose a leaf photo and press Analyze.",
      working: "Working…",
      firstLoadNote: "The first run of a model takes a few seconds while its weights load.",
      somethingWrong: "Something went wrong", detected: "Detected",
      unclear: "Unclear result.",
      unclearSub: "Confidence is below the threshold — try a clearer, closer photo of one leaf.",
      topMatches: "Top matches", lookFor: "What to look for", whatToDo: "What to do next",
      thModel: "Model", thPrediction: "Prediction", thConfidence: "Confidence", thTime: "Time",
      exportCsv: "Export table (CSV)", history: "Recent scans", export: "Export CSV",
      clearHistory: "Clear", noHistory: "No scans recorded yet.",
      footer: "Sweet Diagnosis · runs fully offline on this computer",
      loadingModel: "Loading model…", analyzing: "Analyzing leaf…",
      comparing: "Running all models…",
      noImage: "Choose an image first.",
      unanimous: "All {n} models agree: {c}",
      split: "{v} of {n} models say {c} — the models disagree, so treat this as uncertain.",
      tie: "No agreement: all {n} models named a different class. Retake the photo before deciding.",
      noModels: "No model could run — check that the checkpoints are in model/.",
      missingCkpt: "checkpoint missing",
      confirmClear: "Clear all saved scans?",
      cameraFail: "Could not open the camera. Check that the browser has permission.",
      modelMissing: "This model's checkpoint is not in model/ yet."
    },
    fil: {
      tagline: "Pagtukoy ng sakit sa dahon ng tubo · paghahambing ng 5 CNN",
      connecting: "Kumukonekta…", online: "Handa na ang server", offlineOk: "Handa kahit offline",
      serverDown: "Hindi maabot ang server",
      leafImage: "Larawan ng dahon", dropHere: "Ilagay dito ang larawan ng dahon",
      dropSub: "o mag-click para pumili · JPG, PNG · hanggang 16 MB",
      choose: "Pumili ng larawan", camera: "Gumamit ng camera", capture: "Kunan", clear: "Alisin",
      model: "Modelo", analyze: "Suriin ang dahon", compareAll: "Ihambing lahat ng modelo",
      hint: "Tip: isang dahon lang sa larawan, may sapat na liwanag, at malinis na background.",
      result: "Resulta", emptyMain: "Wala pang suri",
      emptySub: "Pumili ng larawan at pindutin ang Suriin.",
      working: "Ginagawa…",
      firstLoadNote: "Ang unang takbo ng modelo ay tumatagal nang ilang segundo habang naglo-load.",
      somethingWrong: "May naging problema", detected: "Natukoy",
      unclear: "Hindi malinaw na resulta.",
      unclearSub: "Mababa ang kumpiyansa — subukan ang mas malinaw at mas malapit na larawan.",
      topMatches: "Pinakamalapit na tugma", lookFor: "Ano ang hanapin",
      whatToDo: "Ano ang gagawin",
      thModel: "Modelo", thPrediction: "Hula", thConfidence: "Kumpiyansa", thTime: "Oras",
      exportCsv: "I-export ang talahanayan (CSV)", history: "Mga nakaraang suri",
      export: "I-export CSV", clearHistory: "Burahin", noHistory: "Wala pang naitalang suri.",
      footer: "Sweet Diagnosis · tumatakbo nang offline sa computer na ito",
      loadingModel: "Naglo-load ng modelo…", analyzing: "Sinusuri ang dahon…",
      comparing: "Pinapatakbo lahat ng modelo…",
      noImage: "Pumili muna ng larawan.",
      unanimous: "Lahat ng {n} modelo ay sumasang-ayon: {c}",
      split: "{v} sa {n} modelo ang nagsasabing {c} — hindi magkasundo, kaya huwag muna siguraduhin.",
      tie: "Walang pagkakasundo: magkaiba ang sagot ng lahat ng {n} modelo. Kumuha ng bagong larawan.",
      noModels: "Walang modelong tumakbo — tingnan kung nasa model/ ang mga checkpoint.",
      missingCkpt: "walang checkpoint",
      confirmClear: "Burahin lahat ng naitalang suri?",
      cameraFail: "Hindi mabuksan ang camera. Tingnan ang pahintulot ng browser.",
      modelMissing: "Wala pa sa model/ ang checkpoint ng modelong ito."
    }
  };

  let lang = localStorage.getItem("sd_lang") || "en";
  const t = (key) => (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;

  function applyLanguage() {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      el.textContent = t(el.dataset.i18n);
    });
    document.documentElement.lang = lang === "fil" ? "fil" : "en";
    document.querySelectorAll(".lang-btn").forEach((b) =>
      b.classList.toggle("is-active", b.dataset.lang === lang)
    );
  }

  // ------------------------------------------------------------- elements
  const $ = (id) => document.getElementById(id);

  const els = {
    dropZone: $("dropZone"), dropPrompt: $("dropPrompt"), preview: $("preview"),
    camera: $("camera"), canvas: $("canvas"), fileInput: $("fileInput"),
    browseBtn: $("browseBtn"), cameraBtn: $("cameraBtn"), captureBtn: $("captureBtn"),
    clearBtn: $("clearBtn"), modelSelect: $("modelSelect"), modelNote: $("modelNote"),
    analyzeBtn: $("analyzeBtn"), compareBtn: $("compareBtn"),
    emptyState: $("emptyState"), loading: $("loading"), loadingText: $("loadingText"),
    errorBox: $("errorBox"), errorText: $("errorText"),
    singleResult: $("singleResult"), resultCard: $("resultCard"),
    predClass: $("predClass"), predModel: $("predModel"), confValue: $("confValue"),
    ringFill: $("ringFill"), lowConfWarn: $("lowConfWarn"), topK: $("topK"),
    timing: $("timing"), infoCard: $("infoCard"), infoTitle: $("infoTitle"),
    infoSummary: $("infoSummary"), infoSymptoms: $("infoSymptoms"),
    infoActions: $("infoActions"), infoDisclaimer: $("infoDisclaimer"),
    compareResult: $("compareResult"), agreementBanner: $("agreementBanner"),
    cmpBody: $("cmpBody"), compareInfo: $("compareInfo"), exportCmpBtn: $("exportCmpBtn"),
    historyStrip: $("historyStrip"), clearHistBtn: $("clearHistBtn"),
    exportHistBtn: $("exportHistBtn"), serverStatus: $("serverStatus"),
    deviceInfo: $("deviceInfo")
  };

  // --------------------------------------------------------------- state
  let selectedFile = null;   // File from the picker
  let capturedBlob = null;   // Blob from the webcam
  let stream = null;         // active MediaStream
  let lastCompare = null;    // last comparison, for CSV export and re-render
  let lastSingle = null;     // last single result, so a language switch re-renders it
  let modelsMeta = [];

  const RING = 327;          // circumference of the confidence ring (2*pi*52)

  // ----------------------------------------------------------- utilities
  function show(el, visible) { if (el) el.hidden = !visible; }

  function setBusy(isBusy, message) {
    show(els.loading, isBusy);
    if (message) els.loadingText.textContent = message;
    if (isBusy) {
      show(els.emptyState, false);
      show(els.singleResult, false);
      show(els.compareResult, false);
      show(els.errorBox, false);
    }
    els.analyzeBtn.disabled = isBusy || !hasImage();
    els.compareBtn.disabled = isBusy || !hasImage();
  }

  function showError(message) {
    setBusy(false);
    els.errorText.textContent = message;
    show(els.errorBox, true);
    show(els.emptyState, false);
  }

  function hasImage() { return !!(selectedFile || capturedBlob); }

  const pct = (x) => (x * 100).toFixed(1);

  // --------------------------------------------------------- image input
  function setPreviewFromBlob(blob) {
    const url = URL.createObjectURL(blob);
    els.preview.src = url;
    show(els.preview, true);
    show(els.dropPrompt, false);
    show(els.clearBtn, true);
    els.analyzeBtn.disabled = false;
    els.compareBtn.disabled = false;
  }

  function acceptFile(file) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      showError("That file is not an image.");
      return;
    }
    stopCamera();
    selectedFile = file;
    capturedBlob = null;
    setPreviewFromBlob(file);
    show(els.errorBox, false);
  }

  function clearImage() {
    stopCamera();
    selectedFile = null;
    capturedBlob = null;
    els.preview.removeAttribute("src");
    show(els.preview, false);
    show(els.dropPrompt, true);
    show(els.clearBtn, false);
    els.fileInput.value = "";
    els.analyzeBtn.disabled = true;
    els.compareBtn.disabled = true;
    show(els.singleResult, false);
    show(els.compareResult, false);
    show(els.errorBox, false);
    show(els.emptyState, true);
  }

  // ------------------------------------------------------------- camera
  async function startCamera() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 } }
      });
      els.camera.srcObject = stream;
      await els.camera.play();
      show(els.camera, true);
      show(els.preview, false);
      show(els.dropPrompt, false);
      show(els.captureBtn, true);
      show(els.clearBtn, true);
    } catch (err) {
      showError(t("cameraFail"));
    }
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    show(els.camera, false);
    show(els.captureBtn, false);
  }

  function captureFrame() {
    const video = els.camera;
    const canvas = els.canvas;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      capturedBlob = blob;
      selectedFile = null;
      stopCamera();
      setPreviewFromBlob(blob);
    }, "image/jpeg", 0.92);
  }

  // ------------------------------------------------------------ requests
  function buildFormData(extra) {
    const fd = new FormData();
    if (selectedFile) fd.append("image", selectedFile, selectedFile.name);
    else if (capturedBlob) fd.append("image", capturedBlob, "camera-capture.jpg");
    fd.append("lang", lang);
    Object.entries(extra || {}).forEach(([k, v]) => fd.append(k, v));
    return fd;
  }

  async function postImage(url, extra) {
    const res = await fetch(url, { method: "POST", body: buildFormData(extra) });
    let data;
    try {
      data = await res.json();
    } catch (e) {
      throw new Error(`Server returned ${res.status}. Is it still running?`);
    }
    if (!res.ok || !data.ok) throw new Error(data.error || `Request failed (${res.status}).`);
    return data;
  }

  // -------------------------------------------------------- render single
  function renderSingle(result) {
    lastSingle = result;
    els.predClass.textContent = result.display_name || result.predicted_class;
    els.predModel.textContent = `${result.model_name} · ${result.filename || ""}`;

    const conf = result.confidence;
    els.confValue.textContent = Math.round(conf * 100);
    els.ringFill.style.strokeDashoffset = String(RING * (1 - conf));
    els.ringFill.classList.toggle("is-low", result.low_confidence);

    els.resultCard.dataset.severity = (result.info && result.info.severity) || "unknown";
    show(els.lowConfWarn, !!result.low_confidence);

    els.topK.innerHTML = "";
    result.top_k.forEach((item) => {
      const li = document.createElement("li");
      li.innerHTML =
        `<div class="bar-top"><b></b><span>${pct(item.probability)}%</span></div>
         <div class="bar-track"><div class="bar-fill"></div></div>`;
      li.querySelector("b").textContent = item.display || item.class;
      li.querySelector(".bar-fill").style.width = `${item.probability * 100}%`;
      els.topK.appendChild(li);
    });

    els.timing.textContent =
      `${result.predict_ms} ms inference · ${Math.round(result.load_ms)} ms model load · ${result.device}`;

    const info = result.info || {};
    els.infoTitle.textContent = info.title || "";
    els.infoSummary.textContent = info.summary || "";
    fillList(els.infoSymptoms, info.symptoms);
    fillList(els.infoActions, info.actions);
    els.infoDisclaimer.textContent = info.disclaimer || "";

    setBusy(false);
    show(els.singleResult, true);
    show(els.compareResult, false);
  }

  function fillList(ul, items) {
    ul.innerHTML = "";
    (items || []).forEach((text) => {
      const li = document.createElement("li");
      li.textContent = text;
      ul.appendChild(li);
    });
  }

  // ------------------------------------------------------- render compare
  function renderCompare(data) {
    lastCompare = data;
    const { results, agreement } = data;

    const banner = els.agreementBanner;
    if (agreement.unanimous) {
      banner.className = "agreement agreement--unanimous";
      banner.textContent = t("unanimous")
        .replace("{n}", agreement.total_models)
        .replace("{c}", agreement.consensus_class);
    } else if (agreement.consensus_class) {
      banner.className = "agreement agreement--split";
      banner.textContent = t("split")
        .replace("{v}", agreement.consensus_votes)
        .replace("{n}", agreement.total_models)
        .replace("{c}", agreement.consensus_class);
    } else if (agreement.tie) {
      banner.className = "agreement agreement--split";
      banner.textContent = t("tie").replace("{n}", agreement.total_models);
    } else {
      banner.className = "agreement agreement--split";
      banner.textContent = t("noModels");
    }

    const best = results
      .filter((r) => !r.error)
      .reduce((a, b) => (a && a.confidence >= b.confidence ? a : b), null);

    els.cmpBody.innerHTML = "";
    results.forEach((r) => {
      const tr = document.createElement("tr");

      if (r.error) {
        tr.innerHTML =
          `<td class="model-cell"></td>
           <td colspan="3" class="row-error"></td>`;
        tr.querySelector(".model-cell").textContent = r.model_name || r.model;
        tr.querySelector(".row-error").textContent = r.error;
      } else {
        const isConsensus = r.predicted_class === agreement.consensus_class;
        if (best && r.model === best.model) tr.classList.add("is-best");

        tr.innerHTML =
          `<td class="model-cell"><span class="name"></span><span class="arch"></span></td>
           <td><span class="pred-chip ${isConsensus ? "is-consensus" : "is-outlier"}"></span></td>
           <td class="conf-cell">
             <div class="conf-inline">
               <div class="bar-track"><div class="bar-fill"></div></div>
               <span>${pct(r.confidence)}%</span>
             </div>
           </td>
           <td class="time-cell">${r.predict_ms} ms</td>`;

        tr.querySelector(".name").textContent = r.model_name;
        tr.querySelector(".arch").textContent = r.model;
        tr.querySelector(".pred-chip").textContent = r.display_name || r.predicted_class;
        tr.querySelector(".bar-fill").style.width = `${r.confidence * 100}%`;
      }
      els.cmpBody.appendChild(tr);
    });

    els.compareInfo.innerHTML = "";
    if (data.consensus_info) {
      const info = data.consensus_info;
      const card = document.createElement("div");
      card.className = "info-card";
      card.innerHTML =
        `<h4></h4><p class="info-summary"></p>
         <div class="info-cols">
           <div><p class="sub-title">${t("lookFor")}</p><ul class="tick-list sym"></ul></div>
           <div><p class="sub-title">${t("whatToDo")}</p><ul class="tick-list act"></ul></div>
         </div>
         <p class="disclaimer"></p>`;
      card.querySelector("h4").textContent = info.title || "";
      card.querySelector(".info-summary").textContent = info.summary || "";
      fillList(card.querySelector(".sym"), info.symptoms);
      fillList(card.querySelector(".act"), info.actions);
      card.querySelector(".disclaimer").textContent = info.disclaimer || "";
      els.compareInfo.appendChild(card);
    }

    setBusy(false);
    show(els.compareResult, true);
    show(els.singleResult, false);
  }

  function exportCompareCsv() {
    if (!lastCompare) return;
    const rows = [["model", "architecture", "prediction", "confidence", "inference_ms"]];
    lastCompare.results.forEach((r) => {
      if (r.error) rows.push([r.model_name || r.model, r.model, "ERROR", "", r.error]);
      else rows.push([r.model_name, r.model, r.predicted_class,
                      r.confidence.toFixed(4), r.predict_ms]);
    });
    const csv = rows.map((cols) =>
      cols.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")
    ).join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "model_comparison.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // ------------------------------------------------------------- history
  async function loadHistory() {
    try {
      const res = await fetch("/api/history?limit=24");
      const data = await res.json();
      const scans = (data && data.scans) || [];

      if (!scans.length) {
        els.historyStrip.innerHTML = `<p class="empty-sub">${t("noHistory")}</p>`;
        return;
      }

      els.historyStrip.innerHTML = "";
      scans.forEach((s) => {
        const card = document.createElement("div");
        card.className = "hist-card" + (s.low_confidence ? " is-low" : "");
        const when = new Date(s.created_at);
        const time = isNaN(when) ? "" : when.toLocaleString();
        card.innerHTML =
          `${s.thumbnail ? `<img alt="" src="${s.thumbnail}">` : `<div style="height:88px"></div>`}
           <div class="hist-body">
             <div class="hist-class"></div>
             <div class="hist-meta"></div>
           </div>`;
        card.querySelector(".hist-class").textContent =
          `${s.predicted_class} · ${Math.round(s.confidence * 100)}%`;
        card.querySelector(".hist-meta").textContent = `${s.model_name} · ${time}`;
        els.historyStrip.appendChild(card);
      });
    } catch (err) {
      /* history is optional — never block the app on it */
    }
  }

  // -------------------------------------------------------------- models
  async function loadModels() {
    try {
      const res = await fetch("/api/models");
      const data = await res.json();
      if (!data.ok) throw new Error(data.error);

      modelsMeta = data.models;

      // Keep whatever the user picked; this runs again after every scan.
      const previous = els.modelSelect.value;
      els.modelSelect.innerHTML = "";

      data.models.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.slug;
        opt.textContent = m.available
          ? `${m.name} (${m.size_mb} MB)`
          : `${m.name} — ${t("missingCkpt")}`;
        opt.disabled = !m.available;
        els.modelSelect.appendChild(opt);
      });

      const available = data.models.filter((m) => m.available);
      const pick = (slug) => slug && available.some((m) => m.slug === slug);

      els.modelSelect.value =
        pick(previous) ? previous
          : pick(data.default) ? data.default
            : (available[0] ? available[0].slug : data.models[0].slug);

      updateModelNote();
      els.compareBtn.disabled = !hasImage() || available.length === 0;

      setStatus(available.length ? "ok" : "bad",
        available.length ? t("offlineOk") : "No checkpoints found");
    } catch (err) {
      setStatus("bad", t("serverDown"));
      showError(err.message);
    }
  }

  function updateModelNote() {
    const m = modelsMeta.find((x) => x.slug === els.modelSelect.value);
    if (!m) { els.modelNote.textContent = ""; return; }
    els.modelNote.textContent = m.available
      ? `${m.arch}${m.notes ? " · " + m.notes : ""}`
      : t("modelMissing");
  }

  function setStatus(kind, text) {
    els.serverStatus.className = `status-pill status-pill--${kind}`;
    els.serverStatus.innerHTML = `<span class="dot"></span><span></span>`;
    els.serverStatus.querySelector("span:last-child").textContent = text;
  }

  async function loadHealth() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      if (data.ok) {
        els.deviceInfo.textContent =
          `${data.device} · ${data.models_available}/${data.models_total} models · ${data.preprocessing.resize}`;
      }
    } catch (err) { /* footer detail only */ }
  }

  // -------------------------------------------------------------- events
  els.browseBtn.addEventListener("click", () => els.fileInput.click());
  els.dropZone.addEventListener("click", () => { if (!stream) els.fileInput.click(); });
  els.dropZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); els.fileInput.click(); }
  });
  els.fileInput.addEventListener("change", (e) => acceptFile(e.target.files[0]));

  ["dragenter", "dragover"].forEach((ev) =>
    els.dropZone.addEventListener(ev, (e) => {
      e.preventDefault();
      els.dropZone.classList.add("is-dragging");
    })
  );
  ["dragleave", "drop"].forEach((ev) =>
    els.dropZone.addEventListener(ev, (e) => {
      e.preventDefault();
      els.dropZone.classList.remove("is-dragging");
    })
  );
  els.dropZone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    acceptFile(file);
  });

  els.cameraBtn.addEventListener("click", startCamera);
  els.captureBtn.addEventListener("click", captureFrame);
  els.clearBtn.addEventListener("click", clearImage);
  els.modelSelect.addEventListener("change", updateModelNote);

  els.analyzeBtn.addEventListener("click", async () => {
    if (!hasImage()) return showError(t("noImage"));
    const slug = els.modelSelect.value;
    const meta = modelsMeta.find((m) => m.slug === slug);
    setBusy(true, meta && meta.loaded ? t("analyzing") : t("loadingModel"));
    try {
      const data = await postImage("/api/predict", { model: slug });
      renderSingle(data.result);
      loadModels();     // refresh "loaded" flags and load times
      loadHistory();
    } catch (err) {
      showError(err.message);
    }
  });

  els.compareBtn.addEventListener("click", async () => {
    if (!hasImage()) return showError(t("noImage"));
    setBusy(true, t("comparing"));
    try {
      const data = await postImage("/api/compare", {});
      renderCompare(data);
      loadHistory();
    } catch (err) {
      showError(err.message);
    }
  });

  els.exportCmpBtn.addEventListener("click", exportCompareCsv);
  els.exportHistBtn.addEventListener("click", () => { window.location = "/api/history/export"; });
  els.clearHistBtn.addEventListener("click", async () => {
    if (!confirm(t("confirmClear"))) return;
    await fetch("/api/history", { method: "DELETE" });
    loadHistory();
  });

  document.querySelectorAll(".lang-btn").forEach((btn) =>
    btn.addEventListener("click", async () => {
      lang = btn.dataset.lang;
      localStorage.setItem("sd_lang", lang);
      applyLanguage();
      loadModels();
      loadHistory();
      await retranslateResult();
    })
  );

  /* A result already on screen was rendered in the previous language. Rather
     than re-running the model, just fetch the disease notes again and redraw. */
  async function retranslateResult() {
    try {
      if (lastSingle && !els.singleResult.hidden) {
        const res = await fetch(`/api/disease/${lastSingle.predicted_class}?lang=${lang}`);
        const data = await res.json();
        if (data.ok) { lastSingle.info = data.info; renderSingle(lastSingle); }
      } else if (lastCompare && !els.compareResult.hidden) {
        const cls = lastCompare.agreement.consensus_class;
        if (cls) {
          const res = await fetch(`/api/disease/${cls}?lang=${lang}`);
          const data = await res.json();
          if (data.ok) lastCompare.consensus_info = data.info;
        }
        renderCompare(lastCompare);
      }
    } catch (err) { /* language switch must never break the page */ }
  }

  window.addEventListener("beforeunload", stopCamera);

  // ---------------------------------------------------------------- init
  applyLanguage();
  loadModels();
  loadHealth();
  loadHistory();
})();
