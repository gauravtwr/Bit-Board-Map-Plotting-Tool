const state = {
    items: [], // { name, lat, lon }
};

const singleSection = document.getElementById("select-single");
const bulkSection = document.getElementById("select-bulk");
const fileSingle = document.getElementById("file-single");
const fileBulkFiles = document.getElementById("file-bulk-files");
const fileBulkFolder = document.getElementById("file-bulk-folder");
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

function resetItems() {
    state.items = [];
    itemsSection.hidden = true;
    itemsTableBody.innerHTML = "";
    captureBtn.disabled = true;
}

document.querySelectorAll('input[name="mode"]').forEach((el) => {
    el.addEventListener("change", () => {
        const mode = currentMode();
        singleSection.hidden = mode !== "single";
        bulkSection.hidden = mode !== "bulk";
        fileSingle.value = "";
        fileBulkFiles.value = "";
        fileBulkFolder.value = "";
        resetItems();
    });
});

fileSingle.addEventListener("change", () => {
    if (fileSingle.files.length) scanFiles([fileSingle.files[0]]);
});

fileBulkFiles.addEventListener("change", () => {
    if (fileBulkFiles.files.length) scanFiles(Array.from(fileBulkFiles.files));
});

fileBulkFolder.addEventListener("change", () => {
    if (fileBulkFolder.files.length) scanFiles(Array.from(fileBulkFolder.files));
});

async function scanFiles(files) {
    const formData = new FormData();
    files.forEach((file) => formData.append("images", file, file.name));

    logEl.textContent = "";
    const res = await fetch("/api/scan", { method: "POST", body: formData });
    const data = await res.json();

    if (data.error) {
        alert(data.error);
        resetItems();
        return;
    }

    state.items = data.items.map((item) => ({ name: item.name, lat: item.lat, lon: item.lon }));
    renderItemsTable();
    itemsSection.hidden = state.items.length === 0;
    captureBtn.disabled = state.items.length === 0;
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

function filenameFromContentDisposition(header, fallback) {
    if (!header) return fallback;
    const match = header.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
    return match ? decodeURIComponent(match[1]) : fallback;
}

captureBtn.addEventListener("click", async () => {
    if (state.items.length === 0) return;

    const format = document.getElementById("export-format").value;
    const zoom = document.getElementById("zoom").value;

    const latInputs = document.querySelectorAll('input[data-field="lat"]');
    const lonInputs = document.querySelectorAll('input[data-field="lon"]');
    latInputs.forEach((el) => {
        state.items[el.dataset.index].lat = el.value.trim() === "" ? null : parseFloat(el.value);
    });
    lonInputs.forEach((el) => {
        state.items[el.dataset.index].lon = el.value.trim() === "" ? null : parseFloat(el.value);
    });

    logEl.textContent = "";
    progressEl.removeAttribute("value");
    captureBtn.disabled = true;
    logLine("Capturing map area(s)... this can take a few seconds per image.");

    try {
        const res = await fetch("/api/capture-batch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ items: state.items, format, zoom }),
        });

        const resultsHeader = res.headers.get("X-Capture-Results");
        let summary = null;
        if (resultsHeader) {
            summary = JSON.parse(decodeURIComponent(escape(atob(resultsHeader))));
        }

        if (!res.ok) {
            const errBody = await res.json().catch(() => ({}));
            logLine(`\n[ERROR] ${errBody.error || "Capture failed."}`);
            if (summary) logSummary(summary);
            return;
        }

        const blob = await res.blob();
        const contentDisposition = res.headers.get("Content-Disposition");
        const defaultName = state.items.length === 1 ? "map-capture" : "bit-and-board-maps.zip";
        const filename = filenameFromContentDisposition(contentDisposition, defaultName);

        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);

        logEl.textContent = "";
        if (summary) logSummary(summary);
        logLine(`\nDownloaded: ${filename}`);
    } catch (err) {
        logLine(`\n[ERROR] ${err.message}`);
    } finally {
        progressEl.value = 1;
        progressEl.max = 1;
        captureBtn.disabled = false;
    }
});

function logSummary(summary) {
    summary.items.forEach((item) => {
        const tag = item.status === "done" ? "DONE" : item.status === "skipped" ? "SKIPPED" : "ERROR";
        logLine(`[${tag}] ${item.name} - ${item.message}`);
    });
    logLine(`\nFinished: ${summary.done} captured, ${summary.skipped} skipped, ${summary.errors} errors.`);
}
