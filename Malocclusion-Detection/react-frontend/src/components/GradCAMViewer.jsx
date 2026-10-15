
import { useEffect, useRef, useState } from "react";
import { generateGradCAM } from "../services/api";

const OPTIONS = [
  { value: "open_bite", label: "Open Bite" },
  { value: "crossbite", label: "Crossbite" },
  { value: "crowding", label: "Crowding" },
];

export default function GradCAMViewer({ file }) {
  const [condition, setCondition] = useState("open_bite");
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const controllerRef = useRef(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  function clearExplanation() {
    requestIdRef.current += 1;
    controllerRef.current?.abort();

    setExplanation(null);
    setLoading(false);
    setError("");
  }

  async function handleGenerate() {
    if (!file) {
      setError("Upload a dental image first.");
      return;
    }

    controllerRef.current?.abort();

    const controller = new AbortController();
    controllerRef.current = controller;
    const requestId = ++requestIdRef.current;

    setLoading(true);
    setError("");
    setExplanation(null);

    try {
      const data = await generateGradCAM(
        file,
        condition,
        controller.signal
      );

      if (requestId !== requestIdRef.current) return;

      if (
        !data?.images?.original ||
        !data?.images?.heatmap ||
        !data?.images?.overlay
      ) {
        throw new Error(
          "Explanation images are missing in API response."
        );
      }

      setExplanation(data);
    } catch (err) {
      if (
        requestId !== requestIdRef.current ||
        err.name === "AbortError"
      ) {
        return;
      }

      setError(err.message || "Grad-CAM generation failed.");
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }

  // Remount this component from App when a new file is chosen
  // to clear explanations associated with previous images.

  return (
    <section className="explainability-section">
      <div className="panel">
        <div className="panel-heading">
          <span className="step-number">03</span>

          <div>
            <h3>AI Explainability — Grad-CAM</h3>
            <p>
              Explore which image regions influence the
              selected model output.
            </p>
          </div>
        </div>

        <div className="explain-controls">
          <div className="explain-field">
            <label htmlFor="explainCondition">
              Select Condition
            </label>

            <select
              id="explainCondition"
              value={condition}
              onChange={(event) => {
                clearExplanation();
                setCondition(event.target.value);
              }}
            >
              {OPTIONS.map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <button
            className="primary-btn explain-btn"
            disabled={!file || loading}
            onClick={handleGenerate}
          >
            {loading
              ? "Generating..."
              : "Generate Grad-CAM"}
          </button>
        </div>

        {!file && (
          <p className="helper-text">
            Upload a dental image to enable Grad-CAM.
          </p>
        )}

        {loading && (
          <div className="gradcam-loading" role="status">
            <div className="spinner" />
            <p>Generating Grad-CAM visualization...</p>
          </div>
        )}

        {error && (
          <div className="error-box" role="alert">
            {error}
          </div>
        )}

        {explanation && (
          <div className="gradcam-results">
            <div className="gradcam-grid">
              <div className="gradcam-image-card">
                <h4>Original Dental Image</h4>
                <img
                  src={explanation.images.original}
                  alt="Original dental image"
                />
              </div>

              <div className="gradcam-image-card">
                <h4>Grad-CAM Heatmap</h4>
                <img
                  src={explanation.images.heatmap}
                  alt="Grad-CAM activation heatmap"
                />
              </div>

              <div className="gradcam-image-card">
                <h4>Grad-CAM Overlay</h4>
                <img
                  src={explanation.images.overlay}
                  alt="Grad-CAM activation overlaid on dental image"
                />
              </div>
            </div>

            <div className="gradcam-details">
              <p>
                <strong>Condition:</strong>{" "}
                {OPTIONS.find(
                  (item) => item.value === explanation.condition
                )?.label || explanation.condition}
              </p>

              <p>
                <strong>Model Probability:</strong>{" "}
                {(Number(explanation.probability) * 100).toFixed(2)}%
              </p>

              <p>
                <strong>Feature Layer:</strong>{" "}
                {explanation.target_layer}
              </p>

              <p>
                <strong>Generation Status:</strong>{" "}
                {explanation.status}
              </p>
            </div>

            <div className="gradcam-notice">
              <strong>Explainability Limitation</strong>
              <p>
                {explanation.limitations ||
                  "Grad-CAM has not been clinically validated."}
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
