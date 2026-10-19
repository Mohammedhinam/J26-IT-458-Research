
import { useEffect, useRef, useState } from 'react';
import { getHealth, predictCaries, getGradcam } from '../services/api.js';

const labels = ['No Caries', 'Early-Stage Caries', 'Advanced Caries'];
// Enable for PP2 to restore the Grad-CAM UI.
const SHOW_GRADCAM = false;

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
    <>
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white shadow-sm">
        <nav
          aria-label="Main navigation"
          className="mx-auto flex max-w-[1360px] flex-wrap items-center justify-between gap-x-6 gap-y-3 px-4 py-4 sm:px-6 lg:px-8"
        >
          <a
            href="#home"
            className="flex items-center gap-2 rounded-lg text-lg font-bold text-navy focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-sky-accent"
          >
            <span aria-hidden="true" className="flex h-9 w-9 items-center justify-center rounded-xl bg-dashboard text-2xl font-bold text-navy">
              +
            </span>
            Digital Dentistry
          </a>

          <div
            role="status"
            aria-live="polite"
            aria-atomic="true"
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium ${
              status === 'connected'
                ? 'bg-green-50 text-green-700'
                : status === 'loading'
                ? 'bg-amber-50 text-amber-700'
                : 'bg-red-50 text-red-700'
            }`}
          >
            <span aria-hidden="true" className="h-2 w-2 shrink-0 rounded-full bg-current" />
            <span>
              <span className="sr-only">Backend: </span>
              {status === 'connected' ? 'Connected' : status === 'loading' ? 'Checking' : 'Disconnected'}
            </span>
          </div>

          <ul className="flex w-full items-center gap-2 text-sm font-medium sm:order-none sm:w-auto sm:flex-1 sm:justify-end">
            <li>
              <a href="#home" className="inline-flex rounded-lg px-4 py-2 text-slate-600 transition-colors hover:bg-dashboard hover:text-navy focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-accent">
                Home
              </a>
            </li>
            <li>
              <a href="#ai-assessment" className="inline-flex rounded-lg bg-dashboard px-4 py-2 text-navy transition-colors hover:bg-light-blue/40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-accent">
                AI Assessment
              </a>
            </li>
          </ul>
        </nav>
      </header>
    <main className="min-h-screen bg-dashboard px-4 py-8 sm:px-6 lg:px-8 text-navy">
      <section id="home" className="mx-auto max-w-[1360px] space-y-6">

        <div className="space-y-4 rounded-3xl border border-light-blue/40 bg-linear-to-br from-white to-dashboard p-5 shadow-sm sm:p-7">
        <p className="inline-flex items-center gap-2 rounded-full border border-light-blue bg-white px-3 py-1 text-xs font-semibold tracking-wide text-navy">
          <span aria-hidden="true" className="h-2 w-2 rounded-full bg-sky-accent" />
          DENTAL AI RESEARCH
        </p>

        <h1 className="max-w-2xl text-4xl font-bold leading-tight tracking-tight text-navy sm:text-5xl">
          Dental Caries Detection<span className="text-navy"> with AI</span>
        </h1>

        <p className="max-w-2xl text-lg font-medium leading-relaxed text-slate-700">
          Explore suspected caries, assess enamel severity, and understand
          model predictions in one workspace.
        </p>

        <p className="max-w-2xl text-sm leading-6 text-slate-600">
          Upload a dental image to detect suspected regions with YOLOv8,
          compare MobileNetV2 and EfficientNet-B0 classifications
          {SHOW_GRADCAM && ', and explore visual explanations with Grad-CAM'}.
          {' '}Individual Research Project.
        </p>

        <div className="space-y-3 border-t border-light-blue/40 pt-4">
        <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">Classification categories</p>
        <ul className="flex flex-wrap gap-2">
          {labels.map((label) => (
            <li
              key={label}
              className="inline-flex items-center gap-2 rounded-full border border-light-blue bg-white px-3 py-1.5 text-sm font-medium text-navy"
            >
              <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-sky-accent" />
              {label}
            </li>
          ))}
        </ul>
        </div>
        </div>

        {/* Image upload */}
        <div id="ai-assessment" className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-widest text-navy">AI Assessment</p>
          <h2 className="text-2xl font-bold tracking-tight text-navy">
            Upload Dental Image
          </h2>
          <p className="text-sm leading-6 text-slate-600">
            Choose an image to begin detection and severity assessment.
          </p>
          </div>

          <div className="rounded-2xl border-2 border-dashed border-light-blue bg-dashboard/50 p-5 sm:p-6">
          <label htmlFor="dental-image" className="mb-2 block text-sm font-semibold text-navy">
            Select a dental image
          </label>
          <p id="upload-help" className="mb-4 text-sm text-slate-500">Supported formats: JPG and PNG.</p>
          <input
            id="dental-image"
            type="file"
            accept="image/jpeg,image/png"
            aria-describedby="upload-help selected-filename"
            onChange={handleFileChange}
            className="block w-full min-w-0 cursor-pointer rounded-xl border border-light-blue bg-white text-sm text-slate-600 file:mr-3 file:cursor-pointer file:border-0 file:bg-navy file:px-4 file:py-3 file:text-sm file:font-semibold file:text-white hover:file:bg-navy/90 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-sky-accent"
          />
          <p id="selected-filename" role="status" className="mt-4 break-all text-sm text-slate-600">
            {selectedFile ? (
              <><span className="font-semibold text-navy">Selected file: </span>{selectedFile.name}</>
            ) : 'No image selected yet.'}
          </p>
          </div>

          
{preview && (
  <div className="space-y-4 rounded-2xl border border-slate-200 bg-dashboard p-4 sm:p-5">
    <h3 className="text-sm font-semibold text-slate-800">
      Dental Image Analysis
    </h3>

    <p className="text-xs leading-5 text-slate-500">
      Select a labeled box or a region card to inspect a prediction.
      Yellow marks the selected region; purple indicates review required.
    </p>
    <div className="flex justify-center pt-4">
    <div className="relative inline-block max-w-full leading-none">
      <img
        src={preview}
        alt="Dental image with AI detection regions"
        className="block max-h-[32rem] w-auto max-w-full rounded-lg sm:max-h-[40rem]"
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
  </div>
)}


          <button
            type="button"
            onClick={handleAnalyze}
            disabled={!selectedFile || analyzing}
            aria-busy={analyzing}
            className="inline-flex w-full items-center justify-center gap-3 rounded-xl bg-navy px-6 py-3.5 font-semibold text-white shadow-sm transition-colors hover:bg-navy/90 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-sky-accent disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-500 disabled:shadow-none sm:w-auto"
          >
            {analyzing && <span aria-hidden="true" className="h-4 w-4 rounded-full border-2 border-white/40 border-t-white motion-safe:animate-spin" />}
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
          <div className="flex min-w-0 flex-col gap-5 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
            <h2 className="text-2xl font-bold tracking-tight text-navy">
              AI Analysis Results
            </h2>
            
{/* Grad-CAM controls */}
{SHOW_GRADCAM && (
<div className="order-last min-w-0 space-y-5 rounded-2xl border border-light-blue/40 bg-white p-4 shadow-sm sm:p-6">
  <div className="space-y-2">
  <p className="text-xs font-semibold uppercase tracking-widest text-navy">Model insights</p>
  <h3 className="text-xl font-bold tracking-tight text-navy">
    Explainable AI — Grad-CAM
  </h3>

  <p className="max-w-2xl text-sm leading-6 text-slate-600">
    Select a detected region to compare the image areas influencing
    MobileNetV2 and EfficientNet-B0 predictions.
  </p>
  </div>

  <div className="flex flex-col gap-4 rounded-xl border border-light-blue/40 bg-dashboard/60 p-4 sm:flex-row sm:items-center sm:justify-between">
  <div className="space-y-2">
  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Selected region</p>
  <p role="status" aria-atomic="true" className="inline-flex items-center gap-2 rounded-full border border-light-blue bg-white px-3 py-1.5 text-sm font-semibold text-navy">
    <span aria-hidden="true" className={`h-2 w-2 rounded-full ${selectedRegion === null ? 'bg-slate-400' : 'bg-sky-accent'}`} />
    {selectedRegion === null ? 'No region selected' : `Region R${selectedRegion}`}
  </p>
  {selectedRegion === null && <p className="text-xs leading-5 text-slate-500">Choose a box on the image or a region card above.</p>}
  </div>

  <button
    type="button"
    onClick={handleGradcam}
    disabled={selectedRegion === null || gradcamLoading}
    aria-busy={gradcamLoading}
    className="inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-xl bg-navy px-5 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-navy/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-accent disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-500 disabled:shadow-none sm:w-auto"
  >
    {gradcamLoading && <span aria-hidden="true" className="h-4 w-4 rounded-full border-2 border-current border-t-transparent motion-safe:animate-spin" />}
    {gradcamLoading ? 'Generating Grad-CAM...' : 'Generate Grad-CAM'}
  </button>
  </div>

  {gradcamLoading && (
    <p role="status" className="rounded-xl border border-light-blue/40 bg-dashboard px-4 py-3 text-sm leading-6 text-navy">
      Generating visual explanations for the selected region. Heatmaps will appear below when ready.
    </p>
  )}

  {gradcamError && (
    <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-700">
      {gradcamError}
    </p>
  )}

  {/* Grad-CAM visualization */}
  {gradcamResults && gradcamResults.region === selectedRegion && (
    <div className="space-y-4">
      <h4 className="font-semibold text-slate-800">
        Grad-CAM Explanations — Region R{gradcamResults.region}
      </h4>

      <div className="grid grid-cols-1 items-start gap-4 md:grid-cols-2">
        <div className="min-w-0 space-y-3 rounded-2xl border border-slate-200 bg-dashboard p-3 sm:p-4">
          <h5 className="border-b border-slate-200 pb-3 text-sm font-semibold text-navy">
            MobileNetV2
          </h5>
          <img
            src={gradcamResults.MobileNetV2.overlay}
            alt="MobileNetV2 Grad-CAM visualization"
            className="block h-auto w-full rounded-xl border border-slate-200 bg-white"
          />
        </div>

        <div className="min-w-0 space-y-3 rounded-2xl border border-slate-200 bg-dashboard p-3 sm:p-4">
          <h5 className="border-b border-slate-200 pb-3 text-sm font-semibold text-navy">
            EfficientNet-B0
          </h5>
          <img
            src={gradcamResults.EfficientNetB0.overlay}
            alt="EfficientNet-B0 Grad-CAM visualization"
            className="block h-auto w-full rounded-xl border border-slate-200 bg-white"
          />
        </div>
      </div>

      <p className="rounded-xl border border-slate-200 bg-dashboard p-4 text-xs leading-5 text-slate-500">
        Grad-CAM highlights image areas influencing each model's
        prediction. These visualizations do not confirm dental
        caries or establish clinical accuracy.
      </p>
    </div>
  )}
</div>
)}

            
<div className="grid grid-cols-2 gap-3 md:grid-cols-4">
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
    <div key={label} className="min-w-0 rounded-2xl border border-light-blue/40 bg-dashboard/60 p-4">
      <p className="text-3xl font-bold tabular-nums text-navy">
        {value}
      </p>
      <p className="mt-2 text-xs font-medium leading-5 text-slate-600">
        {label}
      </p>
    </div>
  ))}
</div>


            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-5">
              <h3 className="font-semibold text-slate-800">Region predictions</h3>
              {SHOW_GRADCAM && <p className="text-xs text-slate-500">Select a card to explore Grad-CAM</p>}
            </div>

            {results.total_regions === 0 && (
              <p className="rounded-xl border border-slate-200 bg-dashboard p-4 text-sm leading-6 text-slate-600">
                No suspected caries regions detected.
                This does not rule out dental disease.
              </p>
            )}

            <div className="grid min-w-0 gap-4 md:grid-cols-2">
            {results.regions.map((region) => (
  <button
    type="button"
    key={region.region}
    aria-label={`Select region ${region.region}`}
    aria-pressed={selectedRegion === region.region}
    onClick={() => handleRegionSelect(region.region)}
    className={`min-w-0 space-y-4 rounded-2xl border p-4 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-sky-accent ${
      selectedRegion === region.region
        ? 'border-yellow-400 bg-yellow-50 ring-2 ring-yellow-300'
        : 'border-slate-200 bg-white hover:border-sky-accent hover:bg-dashboard/30'
    }`}
  >
                <span className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold text-navy">Region {region.region}</span>
                  <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${region.status === 'Agreement' ? 'bg-dashboard text-navy' : 'bg-amber-50 text-amber-800'}`}>
                    {region.status === 'Agreement' ? 'Models agree' : 'Review required'}
                  </span>
                </span>

                <span className="block text-xs text-slate-500">
                  YOLOv8 confidence:{' '}
                  {(region.detection_confidence * 100).toFixed(2)}%
                </span>

                <span className="block rounded-xl bg-dashboard p-3 text-sm leading-6 text-slate-700">
                  <span className="block text-xs font-semibold text-slate-500">MobileNetV2</span>
                  {severityLabels[region.MobileNetV2.prediction]}
                  {' '}
                  ({(region.MobileNetV2.confidence * 100).toFixed(2)}%)
                </span>

                <span className="block rounded-xl bg-dashboard p-3 text-sm leading-6 text-slate-700">
                  <span className="block text-xs font-semibold text-slate-500">EfficientNet-B0</span>
                  {severityLabels[region.EfficientNetB0.prediction]}
                  {' '}
                  ({(region.EfficientNetB0.confidence * 100).toFixed(2)}%)
                </span>

                <span className="block border-t border-slate-200 pt-3 text-sm font-semibold text-navy">
                  Result:{' '}
                  {severityLabels[region.final_prediction] || 'Uncertain'}
                </span>

                {region.status !== 'Agreement' && (
                  <span className="block text-xs leading-5 text-amber-700">
                    Models disagree. Professional review is recommended.
                  </span>
                )}
              </button>
            ))}
            </div>
          </div>
        )}

      </section>
    </main>

    <footer className="border-t border-light-blue/40 bg-white px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
      <div className="mx-auto grid max-w-[1360px] gap-6 md:grid-cols-2 md:gap-10">
        <div className="space-y-3">
          <p className="flex items-center gap-2 text-lg font-bold text-navy">
            <span aria-hidden="true" className="flex h-8 w-8 items-center justify-center rounded-lg bg-dashboard text-xl text-navy">+</span>
            Digital Dentistry
          </p>
          <p className="max-w-sm text-sm leading-6 text-slate-600">
            AI-Based Dental Caries Detection and Severity Assessment
          </p>
        </div>
        <div className="space-y-2 border-t border-slate-100 pt-5 md:border-t-0 md:border-l md:pt-0 md:pl-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-navy">Research disclaimer</p>
        <p className="text-sm leading-6 text-slate-500">
          Research prototype only. Predictions are not confirmed
          dental diagnoses and should not replace professional
          dental assessment.
        </p>
        </div>
      </div>
    </footer>
    </>
  );
}
