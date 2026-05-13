using System.Net.Http.Headers;

namespace MySemesterApp.Services;

public class TokenHandler : DelegatingHandler
{
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        // 1. Get the token from the device's secure vault
        var token = await SecureStorage.Default.GetAsync("auth_token");

        // 2. If we have a token, attach it to the Authorization header
        if (!string.IsNullOrEmpty(token))
        {
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        }

        // 3. Send the request on its way!
        return await base.SendAsync(request, cancellationToken);
    }
}