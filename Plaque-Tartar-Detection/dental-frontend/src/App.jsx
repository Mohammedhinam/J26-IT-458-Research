
import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!file) {
      setPreview("");
      return;
    }

    const url = URL.createObjectURL(file);
    setPreview(url);

    return () => URL.revokeObjectURL(url);
  }, [file]);

  function handleFileChange(event) {
    const selectedFile = event.target.files?.[0];

    setResult(null);
    setError("");

    if (!selectedFile) {
      setFile(null);
      return;
    }

    const allowedTypes = [
      "image/jpeg",
      "image/png",
      "image/webp",
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      setFile(null);
      setError("Please select a JPG, PNG, or WEBP image.");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setFile(null);
      setError("Image size must be 10 MB or less.");
      return;
    }

    setFile(selectedFile);
  }

  async function analyzeImage() {
    if (!file || loading) return;

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Image analysis failed."
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "Cannot connect to the AI backend. Please start FastAPI on port 8000."
          : err.message || "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  }

  function formatNumber(value) {
    return typeof value === "number"
      ? value.toLocaleString()
      : "N/A";
  }

  function formatPercentage(value) {
    return typeof value === "number" && Number.isFinite(value)
      ? `${value.toFixed(2)}%`
      : "Not available";
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="brand">
          <span className="brand-icon">🦷</span>

          <div>
            <strong>DentalAI</strong>
            <small>Plaque & Tartar Detection</small>
          </div>
        </div>

        <span className="research-tag">
          Research Prototype
        </span>
      </header>

      <main className="main-content">
        <section className="hero">
          <span className="eyebrow">
            AI-POWERED DENTAL IMAGE ANALYSIS
          </span>

          <h1>Understand Your Dental Image</h1>

          <p>
            Upload a clear dental photograph to identify
            possible plaque and tartar regions using our
            trained YOLOv8 models.
          </p>
        </section>

        <div className="workspace">
          {/* IMAGE UPLOAD SECTION */}
          <section className="panel upload-panel">
            <div className="section-heading">
              <span className="step-number">01</span>

              <div>
                <h2>Upload Dental Image</h2>
                <p>Choose a clear photograph of the teeth.</p>
              </div>
            </div>

            <label className="upload-zone">
              <span className="upload-symbol">📷</span>

              <strong>
                {file ? file.name : "Choose a dental image"}
              </strong>

              <span>
                JPG, PNG, or WEBP • Maximum 10 MB
              </span>

              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleFileChange}
              />
            </label>

            {preview && (
              <div className="image-container">
                <span className="image-label">
                  Original image
                </span>

                <img
                  src={preview}
                  alt="Uploaded dental photograph"
                />
              </div>
            )}

            <button
              className="analyze-button"
              onClick={analyzeImage}
              disabled={!file || loading}
            >
              {loading
                ? "Analyzing image..."
                : "Analyze Dental Image →"}
            </button>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <p className="privacy-note">
              Your image is sent to the locally configured
              AI backend for analysis.
            </p>
          </section>

          {/* AI ANALYSIS RESULTS */}
          <section className="panel results-panel">
            <div className="section-heading">
              <span className="step-number">02</span>

              <div>
                <h2>AI Analysis Results</h2>
                <p>
                  Review the detected regions and feedback.
                </p>
              </div>
            </div>

            {!result ? (
              <div className="empty-results">
                <span>🔬</span>

                <h3>
                  {loading
                    ? "Analyzing dental image..."
                    : "Ready for analysis"}
                </h3>

                <p>
                  {loading
                    ? "Please wait while the AI models process your image."
                    : "Upload an image and click Analyze Dental Image to view your AI results."}
                </p>
              </div>
            ) : (
              <div className="results-content">
                {/* DETECTION CARDS */}
                <div className="result-grid">
                  <div className="result-card">
                    <span>🟢 Plaque detection</span>

                    <strong>
                      {result.plaque_detected
                        ? "Possible plaque detected"
                        : "Not detected"}
                    </strong>
                  </div>

                  <div className="result-card">
                    <span>🔴 Tartar detection</span>

                    <strong>
                      {result.tartar_detected
                        ? "Possible tartar detected"
                        : "Not detected"}
                    </strong>
                  </div>

                  <div className="result-card">
                    <span>🦷 Tooth detection</span>

                    <strong>
                      {result.tooth_detected === true
                        ? "Teeth detected"
                        : result.tooth_detected === false
                          ? "No teeth detected"
                          : "Not available"}
                    </strong>
                  </div>

                  <div className="result-card">
                    <span>Predicted plaque pixels</span>

                    <strong>
                      {formatNumber(
                        result.predicted_plaque_pixels
                      )}
                    </strong>
                  </div>

                  <div className="result-card">
                    <span>Tartar bounding boxes</span>

                    <strong>
                      {result.tartar_box_count ?? 0}
                    </strong>
                  </div>

                  <div className="result-card">
                    <span>Automatic plaque coverage</span>

                    <strong>
                      {formatPercentage(
                        result.plaque_coverage_percent
                      )}
                    </strong>
                  </div>
                </div>

                {/* ANNOTATED IMAGE */}
                {result.annotated_image && (
                  <div className="image-container">
                    <span className="image-label">
                      AI annotated image
                    </span>

                    <img
                      src={result.annotated_image}
                      alt="Dental image with predicted tooth and plaque masks and tartar bounding boxes"
                    />

                    <div className="legend">
                      <span>
                        🔵 Blue: predicted teeth
                      </span>

                      <span>
                        🟢 Green: possible plaque
                      </span>

                      <span>
                        🔴 Red: possible tartar
                      </span>
                    </div>
                  </div>
                )}

                {/* ORAL HYGIENE FEEDBACK */}
                <div className="feedback-card">
                  <h3>Oral Hygiene Guidance</h3>

                  <p>
                    {result.feedback}
                  </p>
                </div>

                {/* QUANTIFICATION SECTION */}
                <div className="pending-card">
                  <h3>
                    Quantification & Hygiene Score
                  </h3>

                  <p>
                    <strong>
                      Automatic Plaque Coverage:
                    </strong>{" "}
                    {formatPercentage(
                      result.plaque_coverage_percent
                    )}
                  </p>

                  <p>
                    <strong>
                      Predicted Tooth Pixels:
                    </strong>{" "}
                    {formatNumber(
                      result.predicted_tooth_pixels
                    )}
                  </p>

                  <p>
                    <strong>
                      Plaque Pixels on Teeth:
                    </strong>{" "}
                    {formatNumber(
                      result.plaque_pixels_on_teeth
                    )}
                  </p>

                  <p>
                    <strong>
                      Tartar Bounding Boxes:
                    </strong>{" "}
                    {result.tartar_box_count ?? 0}
                  </p>

                  <p>
                    <strong>
                      Tartar Coverage:
                    </strong>{" "}
                    {result.tartar_coverage_percent != null
                      ? formatPercentage(
                          result.tartar_coverage_percent
                        )
                      : "Not available — tartar segmentation required"}
                  </p>

                  <p>
                    <strong>
                      Oral Hygiene Score:
                    </strong>{" "}
                    {result.hygiene_score != null
                      ? result.hygiene_score
                      : "Pending scientific validation"}
                  </p>

                  <small>
                    {result.quantification_status}
                  </small>

                  <p>
                    <small>
                      Plaque coverage is an experimental
                      measurement based on predicted tooth
                      and plaque segmentation masks.
                      A low value does not necessarily
                      indicate good oral hygiene, especially
                      when the model misses visible teeth.
                    </small>
                  </p>
                </div>

                {/* RESEARCH DISCLAIMER */}
                <p className="disclaimer">
                  {result.disclaimer ||
                    "This is a research prototype, not a clinical diagnostic tool."}
                </p>
              </div>
            )}
          </section>
        </div>

        <footer className="page-footer">
          AI-Based Dental Plaque and Tartar Detection
          <span> • </span>
          Individual Research Component
        </footer>
      </main>
    </div>
  );
}

export default App;
