const API_URL =
  "http://127.0.0.1:8000/predict";


const imageInput =
  document.getElementById(
    "imageInput"
  );

const imagePreview =
  document.getElementById(
    "imagePreview"
  );

const uploadPlaceholder =
  document.getElementById(
    "uploadPlaceholder"
  );

const selectedFile =
  document.getElementById(
    "selectedFile"
  );

const analyzeBtn =
  document.getElementById(
    "analyzeBtn"
  );

const resetBtn =
  document.getElementById(
    "resetBtn"
  );

const emptyState =
  document.getElementById(
    "emptyState"
  );

const loadingState =
  document.getElementById(
    "loadingState"
  );

const resultsContainer =
  document.getElementById(
    "resultsContainer"
  );

const resultCards =
  document.getElementById(
    "resultCards"
  );

const errorBox =
  document.getElementById(
    "errorBox"
  );

const disclaimerText =
  document.getElementById(
    "disclaimerText"
  );


let currentFile = null;


const displayNames = {
  crossbite: "Crossbite",
  open_bite: "Open Bite",
  crowding: "Crowding",
  spacing: "Spacing",
};


imageInput.addEventListener(
  "change",
  handleImageSelection
);


analyzeBtn.addEventListener(
  "click",
  analyzeImage
);


resetBtn.addEventListener(
  "click",
  resetScreening
);


function handleImageSelection(
  event
) {

  const file =
    event.target.files[0];

  if (!file) {
    return;
  }


  if (
    !file.type.startsWith(
      "image/"
    )
  ) {
    showError(
      "Please select a valid image file."
    );

    return;
  }


  currentFile =
    file;


  const reader =
    new FileReader();


  reader.onload =
    function (readerEvent) {

      imagePreview.src =
        readerEvent.target.result;

      imagePreview.classList.remove(
        "hidden"
      );

      uploadPlaceholder.classList.add(
        "hidden"
      );

    };


  reader.readAsDataURL(
    file
  );


  selectedFile.textContent =
    `${file.name} • ${formatBytes(
      file.size
    )}`;

  selectedFile.classList.remove(
    "hidden"
  );


  analyzeBtn.disabled =
    false;

  resetBtn.classList.remove(
    "hidden"
  );

  hideError();
}


async function analyzeImage() {

  if (!currentFile) {
    showError(
      "Please select an image first."
    );

    return;
  }


  showLoading();


  const formData =
    new FormData();

  formData.append(
    "file",
    currentFile
  );


  try {

    const response =
      await fetch(
        API_URL,
        {
          method: "POST",
          body: formData,
        }
      );


    const data =
      await response.json();


    if (!response.ok) {

      throw new Error(
        data.detail ||
        "Prediction request failed."
      );

    }


    renderResults(
      data
    );


  } catch (error) {

    hideLoading();

    showError(
      error.message ||
      "Could not connect to the prediction API."
    );

  }

}


function renderResults(
  data
) {

  resultCards.innerHTML =
    "";


  const results =
    data.results;


  Object.entries(
    results
  ).forEach(
    ([condition, result]) => {

      if (
        result.status ===
        "model_unavailable"
      ) {
        return;
      }


      const probability =
        Number(
          result.probability ||
          0
        );


      const percentage =
        (
          probability
          * 100
        ).toFixed(1);


      const detected =
        Boolean(
          result.detected
        );


      const reliability =
        result.reliability ||
        "preliminary";


      const severity =
        result
          .severity_assessment
          ?.severity_status ||
        "not_assessed";


      const card =
        document.createElement(
          "div"
        );


      card.className =
        `result-card ${
         detected
  ? "Above Screening Threshold"
  : "Below Screening Threshold"
        }`;


      if (
        reliability ===
        "experimental_low_data"
      ) {
        card.classList.add(
          "experimental"
        );
      }


      const readableName =
        displayNames[
          condition
        ] ||
        condition;


      card.innerHTML =
        `
          <div class="result-top">

            <h4>
              ${readableName}
            </h4>

            <span
              class="
                status-badge
                ${
                  detected
                    ? "positive"
                    : "negative"
                }
              "
            >
              ${
                detected
                    ? "Above Screening Threshold"
                    : "Below Screening Threshold"
              }
            </span>

          </div>


          <div class="probability">
            ${percentage}%
          </div>


          <div class="progress-track">

            <div
              class="progress-value"
              style="
                width:
                ${Math.min(
                  percentage,
                  100
                )}%
              "
            >
            </div>

          </div>


          <div class="result-meta">

            Threshold:
            ${(
              Number(
                result.threshold
              )
              * 100
            ).toFixed(0)}%

            <br />

            Reliability:
            ${
              reliability ===
              "experimental_low_data"
                ? "Experimental / Low Data"
                : "Preliminary"
            }

            <br />

            Severity:
            ${
              severity ===
              "not_assessed"
                ? "Pending clinical assessment"
                : severity
            }

          </div>
        `;


      resultCards.appendChild(
        card
      );

    }
  );


  disclaimerText.textContent =
    data.disclaimer ||
    (
      "This output is for preliminary " +
      "research screening only."
    );


  loadingState.classList.add(
    "hidden"
  );

  emptyState.classList.add(
    "hidden"
  );

  errorBox.classList.add(
    "hidden"
  );

  resultsContainer.classList.remove(
    "hidden"
  );

}


function showLoading() {

  emptyState.classList.add(
    "hidden"
  );

  resultsContainer.classList.add(
    "hidden"
  );

  errorBox.classList.add(
    "hidden"
  );

  loadingState.classList.remove(
    "hidden"
  );

  analyzeBtn.disabled =
    true;

}


function hideLoading() {

  loadingState.classList.add(
    "hidden"
  );

  analyzeBtn.disabled =
    false;

}


function showError(
  message
) {

  hideLoading();

  errorBox.textContent =
    message;

  errorBox.classList.remove(
    "hidden"
  );

}


function hideError() {

  errorBox.classList.add(
    "hidden"
  );

}


function resetScreening() {

  currentFile =
    null;


  imageInput.value =
    "";


  imagePreview.src =
    "";

  imagePreview.classList.add(
    "hidden"
  );


  uploadPlaceholder.classList.remove(
    "hidden"
  );


  selectedFile.textContent =
    "";

  selectedFile.classList.add(
    "hidden"
  );


  analyzeBtn.disabled =
    true;


  resetBtn.classList.add(
    "hidden"
  );


  resultsContainer.classList.add(
    "hidden"
  );


  loadingState.classList.add(
    "hidden"
  );


  errorBox.classList.add(
    "hidden"
  );


  emptyState.classList.remove(
    "hidden"
  );

}


function formatBytes(
  bytes
) {

  if (bytes === 0) {
    return "0 B";
  }


  const units = [
    "B",
    "KB",
    "MB",
    "GB",
  ];


  const index =
    Math.floor(
      Math.log(bytes)
      /
      Math.log(1024)
    );


  return (
    (
      bytes
      /
      Math.pow(
        1024,
        index
      )
    ).toFixed(1)
    +
    " "
    +
    units[index]
  );

}