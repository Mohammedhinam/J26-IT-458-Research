
import ResultCard from "./ResultCard";

const CONDITIONS = [
  "crossbite",
  "open_bite",
  "crowding",
  "spacing",
];

export default function ScreeningResults({
  prediction,
  loading,
  error,
}) {
  return (
    <section className="panel result-panel">
      <div className="panel-heading">
        <span className="step-number">02</span>

        <div>
          <h3>Screening Results</h3>
          <p>
            Model probabilities and preliminary
            screening status.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="loading-state" role="status">
          <div className="spinner" />
          <h4>Analyzing image...</h4>
          <p>Running preliminary AI screening.</p>
        </div>
      ) : error ? (
        <div className="error-box" role="alert">
          {error}
        </div>
      ) : !prediction ? (
        <div className="empty-state">
          <div className="empty-circle">AI</div>
          <h4>No analysis yet</h4>
          <p>
            Upload a dental image and select
            Analyze Image to view results.
          </p>
        </div>
      ) : (
        <div className="results-container">
          <div className="result-cards">
            {CONDITIONS.map((condition) => (
              <ResultCard
                key={condition}
                condition={condition}
                result={
                  prediction.results?.[condition] ?? {
                    status: "model_unavailable",
                  }
                }
              />
            ))}
          </div>

          <div className="severity-box">
            <h4>Severity Assessment</h4>
            <p>
              Severity classification is currently
              under clinical-methodology development.
              Model probability is not a severity score.
            </p>
          </div>

          <div className="disclaimer">
            <strong>Research Use Only</strong>
            <p>
              {prediction.disclaimer ||
                "This is preliminary research screening, not a dental diagnosis."}
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
