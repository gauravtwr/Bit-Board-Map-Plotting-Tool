const state = {
    items: [],
    outputPath: null,
};

const sourcePathEl = document.getElementById("source-path");
const outputPathEl = document.getElementById("output-path");
const browseSourceBtn = document.getElementById("browse-source-btn");
const browseOutputBtn = document.getElementById("browse-output-btn");
const captureBtn = document.getElementById("capture-btn");
const itemsSection = document.getElementById("items-section");
const itemsTableBody = document.querySelector("#items-table tbody");
const progressEl = document.getElementById("progress");
const logEl = document.getElementById("log");

function currentMode() {
    return document.querySelector('input[name="mode"]:checked').value;
}

function logLine(text) {
    logEl.textContent += text + "\n";
    logEl.scrollTop = logEl.scrollHeight;
}

function updateCaptureEnabled() {
    captureBtn.disabled = !(state.items.length > 0 && state.outputPath);
}

document.querySelectorAll('input[name="mode"]').forEach((el) => {
    el.addEventListener("change", () => {
        sourcePathEl.value = "";
        state.items = [];
        itemsSection.hidden = true;
        itemsTableBody.innerHTML = "";
        updateCaptureEnabled();
    });
});

browseSourceBtn.addEventListener("click", async () => {
    const mode = currentMode();
    const endpoint = mode === "single" ? "/api/pick-file" : "/api/pick-folder";
    const body = mode === "bulk" ? JSON.stringify({ title: "Select a folder of images" }) : undefined;

    const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body || JSON.stringify({}),
    });
    const data = await res.json();
    if (!data.path) return;

    sourcePathEl.value = data.path;
    await scanSource(mode, data.path);
});

browseOutputBtn.addEventListener("click", async () => {
    const res = await fetch("/api/pick-folder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "Select output folder" }),
    });
    const data = await res.json();
    if (!data.path) return;
    outputPathEl.value = data.path;
    state.outputPath = data.path;
    updateCaptureEnabled();
});

async function scanSource(mode, path) {
    const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, path }),
    });
    const data = await res.json();

    if (data.error) {
        alert(data.error);
        state.items = [];
        itemsSection.hidden = true;
        updateCaptureEnabled();
        return;
    }

    state.items = data.items;
    renderItemsTable();
    itemsSection.hidden = state.items.length === 0;
    updateCaptureEnabled();
}

function renderItemsTable() {
    itemsTableBody.innerHTML = "";
    state.items.forEach((item, index) => {
        const tr = document.createElement("tr");

        const nameTd = document.createElement("td");
        nameTd.textContent = item.name;
        tr.appendChild(nameTd);

        const latTd = document.createElement("td");
        const latInput = document.createElement("input");
        latInput.type = "text";
        latInput.value = item.lat ?? "";
        latInput.dataset.index = index;
        latInput.dataset.field = "lat";
        latTd.appendChild(latInput);
        tr.appendChild(latTd);

        const lonTd = document.createElement("td");
        const lonInput = document.createElement("input");
        lonInput.type = "text";
        lonInput.value = item.lon ?? "";
        lonInput.dataset.index = index;
        lonInput.dataset.field = "lon";
        lonTd.appendChild(lonInput);
        tr.appendChild(lonTd);

        const sourceTd = document.createElement("td");
        sourceTd.textContent = item.lat != null ? "EXIF" : "manual entry needed";
        tr.appendChild(sourceTd);

        itemsTableBody.appendChild(tr);
    });
}

captureBtn.addEventListener("click", async () => {
    if (!state.outputPath || state.items.length === 0) return;

    const format = document.getElementById("export-format").value;
    const zoom = document.getElementById("zoom").value;

    logEl.textContent = "";
    progressEl.max = state.items.length;
    progressEl.value = 0;
    captureBtn.disabled = true;

    const latInputs = document.querySelectorAll('input[data-field="lat"]');
    const lonInputs = document.querySelectorAll('input[data-field="lon"]');
    latInputs.forEach((el) => {
        state.items[el.dataset.index].lat = el.value.trim() === "" ? null : parseFloat(el.value);
    });
    lonInputs.forEach((el) => {
        state.items[el.dataset.index].lon = el.value.trim() === "" ? null : parseFloat(el.value);
    });

    let done = 0, skipped = 0, errors = 0;

    for (const item of state.items) {
        const res = await fetch("/api/capture-one", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                path: item.path,
                lat: item.lat,
                lon: item.lon,
                output_dir: state.outputPath,
                format,
                zoom,
            }),
        });
        const result = await res.json();

        if (result.error) {
            logLine(`[ERROR] ${item.name} - ${result.error}`);
            errors++;
        } else if (result.status === "done") {
            logLine(`[DONE] ${result.name} -> ${result.output_path.split(/[\\/]/).pop()}`);
            done++;
        } else if (result.status === "skipped") {
            logLine(`[SKIPPED] ${result.name} - ${result.message}`);
            skipped++;
        } else {
            logLine(`[ERROR] ${result.name} - ${result.message}`);
            errors++;
        }
        progressEl.value++;
    }

    logLine(`\nFinished: ${done} captured, ${skipped} skipped, ${errors} errors.`);
    captureBtn.disabled = false;
});
