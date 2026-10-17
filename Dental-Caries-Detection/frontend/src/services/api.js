
const API_BASE_URL = 'http://127.0.0.1:8000';

// Existing health-check function
export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}

// New dental caries prediction function
export async function predictCaries(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/caries/predict`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let message = `Prediction failed: ${response.status}`;

    try {
      const errorData = await response.json();
      message = errorData.detail || message;
    } catch {
      // Use the default error message
    }

    throw new Error(message);
  }

  return response.json();
}


export async function getGradcam(file, region) {
  const formData = new FormData();

  formData.append('file', file);
  formData.append('region', String(region));

  const response = await fetch(
    `${API_BASE_URL}/api/caries/gradcam`,
    {
      method: 'POST',
      body: formData,
    }
  );

  if (!response.ok) {
    let message = `Grad-CAM generation failed: ${response.status}`;

    try {
      const errorData = await response.json();
      message = errorData.detail || message;
    } catch {
      // Use the default error message
    }

    throw new Error(message);
  }

  return response.json();
}
