import { useState } from 'react';
import { getHealth } from '../services/api.js';

const labels = ['No Caries', 'Early-Stage Caries', 'Advanced Caries'];

export default function Home() {
  const [status, setStatus] = useState('Not checked');
  const [checking, setChecking] = useState(false);

  async function checkBackend() {
    setChecking(true);
    try {
      const health = await getHealth();
      setStatus(health.status === 'ok' ? 'Connected' : 'Unexpected response');
    } catch {
      setStatus('Unavailable. Start the FastAPI backend and try again.');
    } finally {
      setChecking(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-16 text-slate-900">
      <section className="mx-auto max-w-3xl space-y-6">
        <p className="font-medium text-teal-700">Individual research project</p>
        <h1 className="text-4xl font-bold">Dental Caries Detection</h1>
        <p className="text-lg text-slate-600">AI-Based Dental Caries Detection and Severity Assessment</p>
        <p>Planned: YOLOv8 localization, MobileNetV2 and EfficientNet-B0 severity classification, and Grad-CAM explanations.</p>
        <ul className="flex flex-wrap gap-3">
          {labels.map((label) => <li key={label} className="rounded-lg border border-teal-200 bg-teal-50 px-4 py-2">{label}</li>)}
        </ul>
        <p className="text-slate-600">Project scaffold ready. Image analysis is not implemented yet.</p>
        <button onClick={checkBackend} disabled={checking} className="rounded-lg bg-teal-700 px-4 py-2 font-medium text-white hover:bg-teal-800 disabled:opacity-50">
          {checking ? 'Checking...' : 'Check backend health'}
        </button>
        <p role="status">Backend: {status}</p>
      </section>
    </main>
  );
}
