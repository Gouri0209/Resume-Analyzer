(function () {
  const form = document.getElementById("analyze-form");
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("resume-input");
  const dropzoneEmpty = document.getElementById("dropzone-empty");
  const dropzoneFilled = document.getElementById("dropzone-filled");
  const fileNameEl = document.getElementById("file-name");
  const removeFileBtn = document.getElementById("remove-file");
  const errorBox = document.getElementById("error-box");
  const submitBtn = document.getElementById("submit-btn");
  const submitText = document.getElementById("submit-text");
  const submitSpinner = document.getElementById("submit-spinner");

  function showFile(file) {
    fileNameEl.textContent = file.name;
    dropzoneEmpty.style.display = "none";
    dropzoneFilled.style.display = "block";
  }

  function clearFile() {
    fileInput.value = "";
    dropzoneEmpty.style.display = "block";
    dropzoneFilled.style.display = "none";
  }

  dropzone.addEventListener("click", (e) => {
    if (e.target === removeFileBtn) return;
    fileInput.click();
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) showFile(fileInput.files[0]);
  });

  removeFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearFile();
  });

  ["dragenter", "dragover"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === "application/pdf") {
      fileInput.files = files;
      showFile(files[0]);
    } else {
      showError("Only PDF files are supported.");
    }
  });

  function showError(message) {
    errorBox.textContent = message;
    errorBox.style.display = "block";
  }

  function hideError() {
    errorBox.style.display = "none";
  }

  function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    submitText.textContent = isLoading ? "Analyzing..." : "Analyze Resume";
    submitSpinner.style.display = isLoading ? "inline-block" : "none";
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();

    if (!fileInput.files || fileInput.files.length === 0) {
      showError("Please select a resume PDF to upload.");
      return;
    }

    const jobDescription = document.getElementById("job_description").value.trim();
    if (!jobDescription) {
      showError("Please paste a job description.");
      return;
    }

    const formData = new FormData();
    formData.append("resume", fileInput.files[0]);
    formData.append("job_description", jobDescription);
    formData.append("candidate_name", document.getElementById("candidate_name").value.trim());
    formData.append("job_title", document.getElementById("job_title").value.trim());

    setLoading(true);
    try {
      const response = await fetch("/api/analyze", { method: "POST", body: formData });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong while analyzing your resume.");
      }

      window.location.href = data.redirect_url;
    } catch (err) {
      showError(err.message || "Unable to reach the server. Please try again.");
      setLoading(false);
    }
  });
})();
