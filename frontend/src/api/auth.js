import apiClient from "./axiosClient";

export async function login(username, password) {
  // Le backend attend un formulaire OAuth2PasswordRequestForm, pas du JSON.
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);

  const { data } = await apiClient.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data; // { access_token, token_type }
}
