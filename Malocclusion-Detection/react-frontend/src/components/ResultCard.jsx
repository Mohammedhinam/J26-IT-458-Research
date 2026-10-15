
const CONDITION_NAMES = {
  crossbite: "Crossbite",
  open_bite: "Open Bite",
  crowding: "Crowding",
  spacing: "Spacing",
};

export default function ResultCard({
  condition,
  result,
}) {
  const name = CONDITION_NAMES[condition] || condition;

  if (result?.status === "model_unavailable") {
    return (
      <article className="result-card">
        <h4>{name}</h4>
        <p>Model unavailable</p>
      </article>
    );
  }

  const probability = Number(result?.probability ?? 0);
  const percentage = (probability * 100).toFixed(1);
  const detected = Boolean(result?.detected);

  const experimental =
    result?.reliability === "experimental_low_data";

  const severity = result?.severity_assessment;

  return (
    <article
      className={[
        "result-card",
        detected ? "detected" : "not-detected",
        experimental ? "experimental" : "",
      ].join(" ")}
    >
      <div className="result-top">
        <h4>{name}</h4>

        <span
          className={`status-badge ${
            detected ? "positive" : "negative"
          }`}
        >
          {detected
            ? "Above Threshold"
            : "Below Threshold"}
        </span>
      </div>

      <div className="probability">
        {percentage}%
      </div>

      <div
        className="progress-track"
        role="progressbar"
        aria-label={`${name} model probability`}
        aria-valuenow={probability * 100}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="progress-value"
          style={{
            width: `${Math.min(
              100,
              Math.max(0, probability * 100)
            )}%`,
          }}
        />
      </div>

      <div className="result-meta">
        <p>
          Threshold:{" "}
          {Math.round(Number(result?.threshold ?? 0.5) * 100)}%
        </p>

        <p>
          Reliability:{" "}
          {experimental
            ? "Experimental / Low Data"
            : "Preliminary"}
        </p>

        <p>
          Severity:{" "}
          {severity?.severity_status === "not_assessed"
            ? "Pending clinical assessment"
            : severity?.severity_status ||
              "Not assessed"}
        </p>
      </div>
    </article>
  );
}
