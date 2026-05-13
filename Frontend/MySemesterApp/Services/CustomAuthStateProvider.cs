using System.Security.Claims;
using System.Text.Json;
using Microsoft.AspNetCore.Components.Authorization;

namespace MySemesterApp.Services;

public class CustomAuthStateProvider : AuthenticationStateProvider
{
    private const string TokenKey = "auth_token";

    // 1. This runs automatically when the app starts to check if the user is logged in
    public override async Task<AuthenticationState> GetAuthenticationStateAsync()
    {
        // Check the device's secure storage for a saved token
        var token = await SecureStorage.Default.GetAsync(TokenKey);

        if (string.IsNullOrEmpty(token))
        {
            // No token found? Treat as an anonymous (logged out) user
            return new AuthenticationState(new ClaimsPrincipal(new ClaimsIdentity()));
        }

        // Token found! Decode it and tell Blazor the user is authenticated
        var identity = new ClaimsIdentity(ParseClaimsFromJwt(token), "jwt");
        var user = new ClaimsPrincipal(identity);

        return new AuthenticationState(user);
    }

    // 2. We will call this from our Login Page when the user successfully logs in
    public async Task MarkUserAsAuthenticated(string token)
    {
        // Save the token to the device vault
        await SecureStorage.Default.SetAsync(TokenKey, token);
        
        var identity = new ClaimsIdentity(ParseClaimsFromJwt(token), "jwt");
        var user = new ClaimsPrincipal(identity);

        // Broadcast to the whole app that the user just logged in
        NotifyAuthenticationStateChanged(Task.FromResult(new AuthenticationState(user)));
    }

    // 3. We will call this from our Logout button
    public void MarkUserAsLoggedOut()
    {
        // Delete the token from the device
        SecureStorage.Default.Remove(TokenKey);
        
        var identity = new ClaimsIdentity(); // Empty = logged out
        var user = new ClaimsPrincipal(identity);

        // Broadcast to the whole app that the user just logged out
        NotifyAuthenticationStateChanged(Task.FromResult(new AuthenticationState(user)));
    }

    // --- HELPER METHODS TO READ THE JWT TOKEN ---
    private IEnumerable<Claim> ParseClaimsFromJwt(string jwt)
    {
        var payload = jwt.Split('.')[1];
        var jsonBytes = ParseBase64WithoutPadding(payload);
        var keyValuePairs = JsonSerializer.Deserialize<Dictionary<string, object>>(jsonBytes) 
                            ?? new Dictionary<string, object>();
        return keyValuePairs.Select(kvp => new Claim(kvp.Key, kvp.Value?.ToString() ?? string.Empty));
    }

    private byte[] ParseBase64WithoutPadding(string base64)
    {
        switch (base64.Length % 4)
        {
            case 2: base64 += "=="; break;
            case 3: base64 += "="; break;
        }
        return Convert.FromBase64String(base64);
    }
}