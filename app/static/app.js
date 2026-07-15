const modalOverlay = document.getElementById("modalOverlay");
const notesOverlay = document.getElementById("notesOverlay");
const feedback = document.getElementById("feedback");
const searchInput = document.getElementById("searchInput");
const tableHint = document.getElementById("tableHint");
const defaultDate = document.body.dataset.defaultDate;

let editingId = null;
let currentFilter = "all";

document.getElementById("fDate").value = defaultDate;

document.getElementById("addBtn").addEventListener("click", () => openModal());
document.getElementById("closeModalBtn").addEventListener("click", closeModal);
document.getElementById("cancelBtn").addEventListener("click", closeModal);
document.getElementById("saveBtn").addEventListener("click", saveJob);
document.getElementById("closeNotesBtn").addEventListener("click", closeNotes);
document.getElementById("searchBtn").addEventListener("click", () => loadJobs());
searchInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    loadJobs();
  }
});

document.querySelectorAll(".filter-chip").forEach((button) => {
  button.addEventListener("click", () => {
    currentFilter = button.dataset.filter;
    document
      .querySelectorAll(".filter-chip")
      .forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    loadJobs();
  });
});

modalOverlay.addEventListener("click", (event) => {
  if (event.target === modalOverlay) {
    closeModal();
  }
});

notesOverlay.addEventListener("click", (event) => {
  if (event.target === notesOverlay) {
    closeNotes();
  }
});

function setFeedback(message, type = "info") {
  if (!message) {
    feedback.textContent = "";
    feedback.className = "feedback hidden";
    return;
  }

  feedback.textContent = message;
  feedback.className = `feedback ${type}`;
}

function resetForm() {
  document.getElementById("jobForm").reset();
  document.getElementById("fDate").value = defaultDate;
  document.getElementById("fStatus").value = "applied";
}

function openModal(job = null) {
  editingId = job?._id || null;
  document.getElementById("modalTitle").textContent = editingId
    ? "Edit Application"
    : "Add New Application";

  resetForm();

  if (job) {
    document.getElementById("fCompany").value = job.company || "";
    document.getElementById("fPosition").value = job.position || "";
    document.getElementById("fLocation").value = job.location || "";
    document.getElementById("fPlatform").value = job.platform || "";
    document.getElementById("fDate").value = job.application_date || defaultDate;
    document.getElementById("fDeadline").value = job.deadline || "";
    document.getElementById("fStatus").value = job.status || "applied";
    document.getElementById("fLink").value = job.job_link || "";
    document.getElementById("fReminder").value = job.reminder || "";
    document.getElementById("fNotes").value = job.interview_notes || "";
  }

  modalOverlay.classList.add("show");
}

function closeModal() {
  modalOverlay.classList.remove("show");
  editingId = null;
}

function closeNotes() {
  notesOverlay.classList.remove("show");
}

function showNotes(notes) {
  document.getElementById("notesContent").textContent = notes || "No notes saved.";
  notesOverlay.classList.add("show");
}

function collectFormData() {
  return {
    company: document.getElementById("fCompany").value.trim(),
    position: document.getElementById("fPosition").value.trim(),
    location: document.getElementById("fLocation").value.trim(),
    platform: document.getElementById("fPlatform").value.trim(),
    application_date: document.getElementById("fDate").value,
    deadline: document.getElementById("fDeadline").value,
    status: document.getElementById("fStatus").value,
    job_link: document.getElementById("fLink").value.trim(),
    reminder: document.getElementById("fReminder").value.trim(),
    interview_notes: document.getElementById("fNotes").value.trim(),
  };
}

async function saveJob() {
  const body = collectFormData();

  if (!body.company || !body.position || !body.application_date) {
    setFeedback("Company, position, and application date are required.", "error");
    return;
  }

  const url = editingId ? `/api/jobs/${editingId}` : "/api/jobs/";
  const method = editingId ? "PUT" : "POST";

  try {
    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const payload = await response.json();

    if (!response.ok) {
      setFeedback(payload.error || "Could not save the application.", "error");
      return;
    }

    closeModal();
    setFeedback(
      editingId ? "Application updated successfully." : "Application added successfully.",
      "success"
    );
    await loadJobs();
  } catch (error) {
    setFeedback("Could not save data. Check if MongoDB is running.", "error");
  }
}

function buildQuery() {
  const params = new URLSearchParams();
  const searchValue = searchInput.value.trim();

  if (currentFilter !== "all") {
    params.set("status", currentFilter);
  }

  if (searchValue) {
    params.set("q", searchValue);
  }

  const queryString = params.toString();
  return queryString ? `/api/jobs/?${queryString}` : "/api/jobs/";
}

function renderTable(jobs) {
  const tbody = document.getElementById("jobTableBody");

  if (!jobs.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">No applications found. Add your first application or adjust the current filters.</td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = jobs
    .map((job) => {
      const noteButton = job.interview_notes
        ? `<button class="action-btn" type="button" data-action="notes" data-id="${job._id}">Notes</button>`
        : "";
      const reminderText = job.reminder ? escapeHtml(job.reminder) : `<span class="muted-text">No reminder</span>`;
      const deadlineText = job.deadline || `<span class="muted-text">Not set</span>`;
      const locationText = job.location ? `<small>${escapeHtml(job.location)}</small>` : "";

      return `
        <tr>
          <td class="company-cell">
            <strong>${escapeHtml(job.company)}</strong>
            ${locationText}
          </td>
          <td>
            <div>${escapeHtml(job.position)}</div>
            <small class="muted-text">${escapeHtml(job.platform || "Direct application")}</small>
          </td>
          <td>${job.application_date || "-"}</td>
          <td><span class="badge badge-${job.status}">${job.status}</span></td>
          <td>${deadlineText}</td>
          <td>${reminderText}</td>
          <td>
            <div class="action-row">
              ${noteButton}
              <button class="action-btn" type="button" data-action="edit" data-id="${job._id}">Edit</button>
              <button class="action-btn danger" type="button" data-action="delete" data-id="${job._id}">Delete</button>
            </div>
          </td>
        </tr>
      `;
    })
    .join("");

  tbody.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.action;
      const id = button.dataset.id;

      if (action === "notes") {
        const job = jobs.find((item) => item._id === id);
        showNotes(job?.interview_notes || "");
      }

      if (action === "edit") {
        const job = jobs.find((item) => item._id === id);
        openModal(job);
      }

      if (action === "delete") {
        await deleteJob(id);
      }
    });
  });
}

async function loadStats() {
  try {
    const response = await fetch("/api/jobs/stats/summary");
    const stats = await response.json();

    if (!response.ok) {
      setFeedback(stats.error || "Could not load stats.", "error");
      return;
    }

    document.getElementById("statTotal").textContent = stats.total || 0;
    document.getElementById("statApplied").textContent = stats.applied || 0;
    document.getElementById("statInterview").textContent = stats.interview || 0;
    document.getElementById("statSelected").textContent = stats.selected || 0;
    document.getElementById("statRejected").textContent = stats.rejected || 0;
    document.getElementById("statDeadline").textContent = stats.upcoming_deadlines || 0;
  } catch (error) {
    setFeedback("Could not load stats. Check if MongoDB is running.", "error");
  }
}

async function loadJobs() {
  const url = buildQuery();
  const filterLabel = currentFilter === "all" ? "all statuses" : currentFilter;
  const searchLabel = searchInput.value.trim();

  tableHint.textContent = searchLabel
    ? `Showing ${filterLabel} matching "${searchLabel}".`
    : `Showing applications for ${filterLabel}.`;

  try {
    const response = await fetch(url);
    const jobs = await response.json();

    if (!response.ok) {
      renderTable([]);
      setFeedback(jobs.error || "Could not load applications.", "error");
      return;
    }

    renderTable(jobs);
    await loadStats();

    if (!jobs.length) {
      setFeedback("No applications matched the current search or filter.", "info");
    } else {
      setFeedback("");
    }
  } catch (error) {
    renderTable([]);
    setFeedback("Could not connect to the API. Start the Flask server and MongoDB.", "error");
  }
}

async function deleteJob(id) {
  const confirmed = window.confirm("Delete this application?");
  if (!confirmed) {
    return;
  }

  try {
    const response = await fetch(`/api/jobs/${id}`, { method: "DELETE" });
    const payload = await response.json();

    if (!response.ok) {
      setFeedback(payload.error || "Could not delete the application.", "error");
      return;
    }

    setFeedback("Application hidden from the dashboard successfully.", "success");
    await loadJobs();
  } catch (error) {
    setFeedback("Could not delete data. Check if MongoDB is running.", "error");
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

loadJobs();
