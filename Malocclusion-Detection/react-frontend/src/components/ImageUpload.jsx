
import { useEffect, useState } from "react";

const MAX_FILE_SIZE = 5 * 1024 * 1024;

export default function ImageUpload({
  file,
  onFileChange,
  onAnalyze,
  onReset,
  loading,
}) {
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!file) {
      return;
    }

    const url = URL.createObjectURL(file);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => {
    if (!file) {
      return;
    }

    const url = URL.createObjectURL(file);
    const update = () => setPreview(url);
    update();

    return () => URL.revokeObjectURL(url);
  }, [file]);

  function handleSelection(event) {
    const selected = event.target.files?.[0];

    if (!selected) return;

    if (!["image/jpeg", "image/png"].includes(selected.type)) {
      setError("Please select a JPG or PNG image.");
      event.target.value = "";
      return;
    }

    if (selected.size > MAX_FILE_SIZE) {
      setError("Maximum image size is 5 MB.");
      event.target.value = "";
      return;
    }

    setError("");
    onFileChange(selected);
  }

  function reset() {
    setPreview("");
    setError("");
    onReset();
  }

  return (
    <section className="panel upload-panel">
      <div className="panel-heading">
        <span className="step-number">01</span>

        <div>
          <h3>Upload Dental Image</h3>
          <p>
            Select a clear frontal dental photograph
            for preliminary screening.
          </p>
        </div>
      </div>

      <label className="upload-box" htmlFor="dentalImage">
        <input
          id="dentalImage"
          type="file"
          accept=".jpg,.jpeg,.png,image/jpeg,image/png"
          onChange={handleSelection}
          disabled={loading}
          key={file ? file.name + file.size : "empty"}
          hidden
        />

        {file && preview ? (
          <img
            src={preview}
            alt="Uploaded dental preview"
            className="image-preview"
          />
        ) : (
          <div className="upload-placeholder">
            <div className="upload-icon">+</div>
            <strong>Choose Dental Image</strong>
            <span>JPG or PNG • Maximum 5 MB</span>
          </div>
        )}
      </label>

      {file && (
        <div className="selected-file">
          {file.name} — {(file.size / 1024).toFixed(1)} KB
        </div>
      )}

      {error && (
        <div className="error-box" role="alert">
          {error}
        </div>
      )}

      <button
        type="button"
        className="primary-btn"
        disabled={!file || loading}
        onClick={onAnalyze}
      >
        {loading ? "Analyzing Image..." : "Analyze Image"}
      </button>

      {file && (
        <button
          type="button"
          className="secondary-btn"
          onClick={reset}
        >
          Upload Another Image
        </button>
      )}
    </section>
  );
}
