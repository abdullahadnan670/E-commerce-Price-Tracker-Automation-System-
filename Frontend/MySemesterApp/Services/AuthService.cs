using System.Net.Http.Json;
using MySemesterApp.Models; // <-- Change to your actual namespace

namespace MySemesterApp.Services
{
    public class AuthService
    {
        private readonly HttpClient _httpClient;

        public AuthService(HttpClient httpClient)
        {
            _httpClient = httpClient;
        }

        public async Task<bool> SignupAsync(UserCreate user)
        {
            // Calls http://127.0.0.1:8000/signup
            var response = await _httpClient.PostAsJsonAsync("signup", user);
            return response.IsSuccessStatusCode;
        }

        public async Task<string?> LoginAsync(string email, string password)
        {
            // FastAPI's OAuth2 expects form data, not JSON, for logging in
            var loginData = new FormUrlEncodedContent(new[]
            {
                new KeyValuePair<string, string>("username", email),
                new KeyValuePair<string, string>("password", password)
            });

            // Calls http://127.0.0.1:8000/login
            var response = await _httpClient.PostAsync("login", loginData);

            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadFromJsonAsync<TokenResponse>();
                return result?.AccessToken;
            }

            return null; // Login failed
        }
    }
}