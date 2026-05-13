using System.Text.Json.Serialization;

namespace MySemesterApp.Models // <-- Change to your actual project namespace!
{
    // Matches your UserCreate Pydantic schema
    public class UserCreate
    {
        public string Email { get; set; } = string.Empty;
        public string Password { get; set; } = string.Empty;
    }

    // Matches your Token Pydantic schema
    public class TokenResponse
    {
        [JsonPropertyName("access_token")]
        public string AccessToken { get; set; } = string.Empty;

        [JsonPropertyName("token_type")]
        public string TokenType { get; set; } = string.Empty;
    }
}