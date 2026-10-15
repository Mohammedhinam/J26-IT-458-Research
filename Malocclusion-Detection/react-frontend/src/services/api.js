
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

async function parseResponse(response) {
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail;

    throw new Error(
      typeof detail === "string"
        ? detail
        : `API request failed (${response.status})`
    );
  }

  return data;
}

export async function checkHealth(signal) {
  const response = await fetch(
    `${API_BASE_URL}/health`,
    { signal }
  );

  return parseResponse(response);
}

export async function predictDentalImage(file, signal) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${API_BASE_URL}/predict`,
    {
      method: "POST",
      body: formData,
      signal,
    }
  );

  return parseResponse(response);
}

export async function generateGradCAM(
  file,
  condition,
  signal
) {
  const formData = new FormData();

  formData.append("file", file);
  formData.append("condition", condition);

  const response = await fetch(
    `${API_BASE_URL}/explain`,
    {
      method: "POST",
      body: formData,
      signal,
    }
  );

  return parseResponse(response);
}
