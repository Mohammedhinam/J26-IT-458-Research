
import { useEffect, useRef, useState } from 'react';
import { getHealth, predictCaries, getGradcam } from '../services/api.js';

const labels = ['No Caries', 'Early-Stage Caries', 'Advanced Caries'];

const severityLabels = {
  NoEnamel_Caries: 'No Enamel Caries',
  EarlyStageEnamel_Caries: 'Early-Stage Caries',
  AdvanceEnamel_Caries: 'Advanced Caries',
  Uncertain: 'Review Required',
};

export default function Home() {
  const [status, setStatus] = useState('loading');
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [results, setResults] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  const [imageDimensions, setImageDimensions] = useState({
  width: 0,
  height: 0,
});

const [selectedRegion, setSelectedRegion] = useState(null);
const [gradcamResults, setGradcamResults] = useState(null);
const [gradcamLoading, setGradcamLoading] = useState(false);
const [gradcamError, setGradcamError] = useState('');
const gradcamRequestId = useRef(0);

  async function checkBackend() {
    setStatus('loading');

    try {
      await getHealth();
      setStatus('connected');
    } catch {
      setStatus('disconnected');
    }
  }

  useEffect(() => {
    checkBackend();
  }, []);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  function handleFileChange(event) {
    const file = event.target.files?.[0];

    if (!file) return;

    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      setError('Please select a JPG or PNG image.');
      return;
    }

    setSelectedFile(file);
    gradcamRequestId.current += 1;
    setSelectedRegion(null);
    setGradcamResults(null);
    setGradcamLoading(false);
    setGradcamError('');
    setImageDimensions({ width: 0, height: 0 });

const img = new Image();
const objectUrl = URL.createObjectURL(file);

img.onload = () => {
  setImageDimensions({
    width: img.naturalWidth,
    height: img.naturalHeight,
  });
  URL.revokeObjectURL(objectUrl);
};

img.onerror = () => URL.revokeObjectURL(objectUrl);
img.src = objectUrl;
    setPreview(URL.createObjectURL(file));
    setResults(null);
    setError('');
  }

  async function handleAnalyze() {
    if (!selectedFile) return;

    setAnalyzing(true);
    setResults(null);
    gradcamRequestId.current += 1;
    setSelectedRegion(null);
    setGradcamResults(null);
    setGradcamLoading(false);
    setGradcamError('');
    setError(''); 

    try {
      const response = await predictCaries(selectedFile);
      setResults(response);
    } catch (err) {
      setError(err.message || 'Image analysis failed.');
    } finally {
      setAnalyzing(false);
    }
  }
  
async function handleGradcam() {
  if (!selectedFile || selectedRegion === null || gradcamLoading) {
    return;
  }

  const requestedRegion = selectedRegion;
  const requestId = ++gradcamRequestId.current;

  setGradcamLoading(true);
  setGradcamResults(null);
  setGradcamError('');

  try {
    const response = await getGradcam(
      selectedFile,
      requestedRegion
    );

    if (requestId !== gradcamRequestId.current) return;

    if (response.region !== requestedRegion) {
      throw new Error('Grad-CAM region mismatch.');
    }

    setGradcamResults(response);
  } catch (err) {
    if (requestId !== gradcamRequestId.current) return;

    setGradcamError(
      err.message || 'Failed to generate Grad-CAM.'
    );
  } finally {
    if (requestId === gradcamRequestId.current) {
      setGradcamLoading(false);
    }
  }
}

function handleRegionSelect(regionNumber) {
  gradcamRequestId.current += 1;

  setSelectedRegion(regionNumber);
  setGradcamResults(null);
  setGradcamLoading(false);
  setGradcamError('');
}


  return (
    <main className="min-h-screen bg-slate-50 px-6 py-12 text-slate-900">
      <section className="mx-auto max-w-4xl space-y-6">

        <p className="font-medium text-teal-700">
          Individual Research Project
        </p>

        <h1 className="text-4xl font-bold">
          Dental Caries Detection
        </h1>

        <p className="text-lg text-slate-600">
          AI-Based Dental Caries Detection and Severity Assessment
        </p>

        <p className="text-slate-600">
          Detect suspected dental caries using YOLOv8 and assess
          enamel caries severity using MobileNetV2 and EfficientNet-B0.
        </p>

        <ul className="flex flex-wrap gap-3">
          {labels.map((label) => (
            <li
              key={label}
              className="rounded-lg border border-teal-200 bg-teal-50 px-4 py-2"
            >
              {label}
            </li>
          ))}
        </ul>

        {/* Backend connection */}
        <div className="rounded-xl border bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p>
              Backend:
              <span className="ml-2 font-semibold">
                {status === 'connected'
                  ? 'Connected'
                  : status === 'loading'
                  ? 'Checking...'
                  : 'Disconnected'}
              </span>
            </p>

            <button
              onClick={checkBackend}
              disabled={status === 'loading'}
              className="rounded-lg bg-teal-700 px-4 py-2 text-white disabled:opacity-50"
            >
              Check Connection
            </button>
          </div>
        </div>

        {/* Image upload */}
        <div className="space-y-4 rounded-xl border bg-white p-6">
          <h2 className="text-xl font-semibold">
            Upload Dental Image
          </h2>

          <input
            type="file"
            accept="image/jpeg,image/png"
            onChange={handleFileChange}
            className="block w-full text-sm"
          />

          
{preview && (
  <div className="space-y-2">
    <h3 className="font-medium">
      Dental Image Analysis
    </h3>

    <div className="relative inline-block max-w-full">
      <img
        src={preview}
        alt="Dental image with AI detection regions"
        className="block max-h-96 max-w-full rounded-lg"
      />

      {results?.regions?.map((region) => {
        const [x1, y1, x2, y2] = region.bounding_box;

        const imageWidth = imageDimensions.width;
        const imageHeight = imageDimensions.height;

        if (!imageWidth || !imageHeight) return null;

        const isUncertain =
          region.final_prediction === 'Uncertain';

        const isSelected = selectedRegion === region.region;

        return (
          <div
  key={region.region}
  role="button"
  tabIndex={0}
  aria-label={`Select region ${region.region}`}
  aria-pressed={isSelected}
  onClick={() => handleRegionSelect(region.region)}
  onKeyDown={(event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleRegionSelect(region.region);
    }
  }}
  className={`absolute cursor-pointer transition-all ${
    isSelected
      ? 'z-10 border-4 border-yellow-400'
      : isUncertain
      ? 'border-2 border-purple-500'
      : 'border-2 border-red-500'
  }`}
  style={{
              left: `${(x1 / imageWidth) * 100}%`,
              top: `${(y1 / imageHeight) * 100}%`,
              width: `${((x2 - x1) / imageWidth) * 100}%`,
              height: `${((y2 - y1) / imageHeight) * 100}%`,
            }}
          >
            <span
              className={`absolute bottom-full left-0 whitespace-nowrap px-1 text-xs font-bold text-white ${
                isUncertain
                  ? 'bg-purple-600'
                  : 'bg-red-600'
              }`}
            >
              R{region.region}
            </span>
          </div>
        );
      })}
    </div>
  </div>
)}


          <button
            onClick={handleAnalyze}
            disabled={!selectedFile || analyzing}
            className="rounded-lg bg-teal-700 px-6 py-3 font-medium text-white hover:bg-teal-800 disabled:opacity-50"
          >
            {analyzing ? 'Analyzing Image...' : 'Analyze Image'}
          </button>

          {error && (
            <p role="alert" className="text-red-600">
              {error}
            </p>
          )}
        </div>

        {/* Prediction results */}
        {results && (
          <div className="space-y-4 rounded-xl border bg-white p-6">
            <h2 className="text-xl font-semibold">
              AI Analysis Results
            </h2>
            
{/* Grad-CAM controls */}
<div className="space-y-3 rounded-lg border border-teal-200 bg-teal-50 p-4">
  <h3 className="font-semibold text-teal-900">
    Explainable AI — Grad-CAM
  </h3>

  <p className="text-sm text-slate-600">
    Select a detected region (R1, R2, etc.) to generate
    visual explanations from both classification models.
  </p>

  <p className="text-sm font-medium">
    Selected Region: {selectedRegion === null ? 'None' : `R${selectedRegion}`}
  </p>

  <button
    type="button"
    onClick={handleGradcam}
    disabled={selectedRegion === null || gradcamLoading}
    className="rounded-lg bg-teal-700 px-4 py-2 font-medium text-white hover:bg-teal-800 disabled:opacity-50"
  >
    {gradcamLoading ? 'Generating Grad-CAM...' : 'Generate Grad-CAM'}
  </button>

  {gradcamError && (
    <p role="alert" className="text-sm text-red-600">
      {gradcamError}
    </p>
  )}

  {/* Grad-CAM visualization */}
  {gradcamResults && gradcamResults.region === selectedRegion && (
    <div className="space-y-4">
      <h4 className="font-semibold text-slate-800">
        Grad-CAM Explanations — Region R{gradcamResults.region}
      </h4>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border bg-white p-3">
          <h5 className="mb-2 font-semibold">
            MobileNetV2
          </h5>
          <img
            src={gradcamResults.MobileNetV2.overlay}
            alt="MobileNetV2 Grad-CAM visualization"
            className="w-full rounded-lg"
          />
        </div>

        <div className="rounded-lg border bg-white p-3">
          <h5 className="mb-2 font-semibold">
            EfficientNet-B0
          </h5>
          <img
            src={gradcamResults.EfficientNetB0.overlay}
            alt="EfficientNet-B0 Grad-CAM visualization"
            className="w-full rounded-lg"
          />
        </div>
      </div>

      <p className="text-xs text-slate-500">
        Grad-CAM highlights image areas influencing each model's
        prediction. These visualizations do not confirm dental
        caries or establish clinical accuracy.
      </p>
    </div>
  )}
</div>

            
<div className="grid grid-cols-2 gap-4 rounded-lg bg-teal-50 p-4 md:grid-cols-4">
  {[
    ['Detected Regions', results.total_regions],
    [
      'Model Agreement',
      results.regions.filter(r => r.status === 'Agreement').length
    ],
    [
      'Advanced Predictions',
      results.regions.filter(
        r => r.final_prediction === 'AdvanceEnamel_Caries'
      ).length
    ],
    [
      'Review Required',
      results.regions.filter(
        r => r.status !== 'Agreement'
      ).length
    ],
  ].map(([label, value]) => (
    <div key={label} className="text-center">
      <p className="text-2xl font-bold text-teal-800">
        {value}
      </p>
      <p className="text-sm text-slate-600">
        {label}
      </p>
    </div>
  ))}
</div>


            <p>
              Detected regions:
              <strong className="ml-2">{results.total_regions}</strong>
            </p>

            {results.total_regions === 0 && (
              <p>
                No suspected caries regions detected.
                This does not rule out dental disease.
              </p>
            )}

            {results.regions.map((region) => (
  <div
    key={region.region}
    onClick={() => handleRegionSelect(region.region)}
    className={`space-y-2 rounded-lg border p-4 cursor-pointer transition-all ${
      selectedRegion === region.region
        ? 'border-yellow-400 bg-yellow-50 ring-2 ring-yellow-300'
        : 'border-slate-200 bg-white'
    }`}
  >
                <h3 className="font-semibold">
                  Region {region.region}
                </h3>

                <p>
                  YOLOv8 confidence:{' '}
                  {(region.detection_confidence * 100).toFixed(2)}%
                </p>

                <p>
                  MobileNetV2:{' '}
                  {severityLabels[region.MobileNetV2.prediction]}
                  {' '}
                  ({(region.MobileNetV2.confidence * 100).toFixed(2)}%)
                </p>

                <p>
                  EfficientNet-B0:{' '}
                  {severityLabels[region.EfficientNetB0.prediction]}
                  {' '}
                  ({(region.EfficientNetB0.confidence * 100).toFixed(2)}%)
                </p>

                <p className="font-medium">
                  Result:{' '}
                  {severityLabels[region.final_prediction] || 'Uncertain'}
                </p>

                {region.status !== 'Agreement' && (
                  <p className="text-amber-700">
                    Models disagree. Professional review is recommended.
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        <p className="text-sm text-slate-500">
          Research prototype only. Predictions are not confirmed
          dental diagnoses and should not replace professional
          dental assessment.
        </p>

      </section>
    </main>
  );
}
