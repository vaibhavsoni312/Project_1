const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function signup(name, email, password) {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Signup failed");
  }

  return data; // { message, access_token, token_type }
}

export async function login(email, password) {
  // login route uses OAuth2PasswordRequestForm — needs form-urlencoded, not JSON
  const form = new URLSearchParams();
  form.append("username", email); // backend expects "username" field
  form.append("password", password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Login failed");
  }

  return data; // { message, access_token, token_type }
}
export async function uploadVideo(videoBlob, token) {
  const formData = new FormData();
  formData.append("file", videoBlob, "session.webm");

  const res = await fetch(`${API_BASE}/video/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      // Content-Type set MAT karna — FormData khud boundary header set karta hai
    },
    body: formData,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Video upload failed");
  }

  return data; // { message, video_id, final_scores, feedback }
}
export async function getSessions(token) {
  const res = await fetch(`${API_BASE}/video/my-sessions`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Failed to fetch sessions");
  }

  return data.sessions; // array
}