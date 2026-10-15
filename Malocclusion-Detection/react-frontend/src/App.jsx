
import { useEffect, useRef, useState } from "react";

import Header from "./components/Header";
import ImageUpload from "./components/ImageUpload";
import ScreeningResults from "./components/ScreeningResults";
import GradCAMViewer from "./components/GradCAMViewer";
import Footer from "./components/Footer";

import {
  checkHealth,
  predictDentalImage,
} from "./services/api";

const CONDITION_DETAILS = [
  {
    title: "Crossbite",
    description:
      "An abnormal bite relationship where some upper teeth close inside the lower teeth.",
  },
  {
    title: "Open Bite",
    description:
      "Upper and lower teeth do not make contact in part of the bite.",
  },
  {
    title: "Crowding",
    description:
      "Insufficient arch space can cause teeth to overlap or become displaced.",
  },
  {
    title: "Spacing",
    description:
      "Spaces or gaps occur between teeth.",
  },
];

export default function App() {
  const [file, setFile] = useState(null);
  const [fileVersion, setFileVersion] = useState(0);

  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [apiStatus, setApiStatus] = useState("checking");

  const controllerRef = useRef(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    const controller = new AbortController();

    checkHealth(controller.signal)
      .then((data) => {
        setApiStatus(
          data?.loaded_model_count > 0
            ? "connected"
            : "no-models"
        );
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          setApiStatus("disconnected");
        }
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  function cancelPrediction() {
    requestIdRef.current += 1;
    controllerRef.current?.abort();
    controllerRef.current = null;
  }

  function handleFileChange(selectedFile) {
    cancelPrediction();

    setFile(selectedFile);
    setFileVersion((version) => version + 1);
    setPrediction(null);
    setError("");
    setLoading(false);
  }

  function handleReset() {
    cancelPrediction();

    setFile(null);
    setFileVersion((version) => version + 1);
    setPrediction(null);
    setError("");
    setLoading(false);
  }

  async function handleAnalyze() {
    if (!file) return;

    controllerRef.current?.abort();

    const controller = new AbortController();
    controllerRef.current = controller;

    const requestId = ++requestIdRef.current;

    setLoading(true);
    setError("");
    setPrediction(null);

    try {
      const response = await predictDentalImage(
        file,
        controller.signal
      );

      if (requestId !== requestIdRef.current) return;

      setPrediction(response);
      setApiStatus("connected");
    } catch (err) {
      if (
        requestId !== requestIdRef.current ||
        err.name === "AbortError"
      ) {
        return;
      }

      setError(
        err.message || "Unable to connect to FastAPI."
      );
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }

  return (
    <>
      <Header />

      <main className="container">
        <section className="hero">
          <div className="hero-text">
            <span className="eyebrow">
              AI-ASSISTED ORTHODONTIC SCREENING
            </span>

            <h2>
              Preliminary
              <br />
              Malocclusion Detection
            </h2>

            <p>
              Upload a dental image to screen for
              Crossbite, Open Bite, Crowding and Spacing
              using preliminary AI models.
            </p>
          </div>

          <div className="hero-info">
            <div className="info-stat">
              <strong>4</strong>
              <span>Target Conditions</span>
            </div>

            <div className="info-stat">
              <strong>MobileNetV2</strong>
              <span>Transfer Learning</span>
            </div>

            <div className="info-stat">
              <strong>Grad-CAM</strong>
              <span>Exploratory Explainability</span>
            </div>
          </div>
        </section>

        <div
          className={`api-indicator api-${apiStatus}`}
          role="status"
        >
          <span className="api-dot" />
          {apiStatus === "connected"
            ? "AI Backend Connected"
            : apiStatus === "checking"
              ? "Checking AI Backend..."
              : apiStatus === "no-models"
                ? "Backend Available — No Models Loaded"
                : "AI Backend Not Connected"}
        </div>

        <div className="screening-grid">
          <ImageUpload
            file={file}
            onFileChange={handleFileChange}
            onAnalyze={handleAnalyze}
            onReset={handleReset}
            loading={loading}
          />

          <ScreeningResults
            prediction={prediction}
            loading={loading}
            error={error}
          />
        </div>

        <GradCAMViewer
          key={fileVersion}
          file={file}
        />

        <section className="conditions-section">
          <div className="section-title">
            <span>TARGET CONDITIONS</span>
            <h3>
              Malocclusion Categories Included
              in the Research
            </h3>
          </div>

          <div className="condition-info-grid">
            {CONDITION_DETAILS.map((item) => (
              <article key={item.title}>
                <h4>{item.title}</h4>
                <p>{item.description}</p>
              </article>
            ))}
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
