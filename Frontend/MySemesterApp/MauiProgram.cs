using Microsoft.Extensions.Logging;
using Microsoft.AspNetCore.Components.Authorization; // 🚨 Required for the Security Guard
using MySemesterApp.Services;  
using Radzen;
namespace MySemesterApp;

public static class MauiProgram
{
    public static MauiApp CreateMauiApp()
    {
        var builder = MauiApp.CreateBuilder();
        builder
            .UseMauiApp<App>()
            .ConfigureFonts(fonts =>
            {
                fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular");
            });

        builder.Services.AddMauiBlazorWebView();
        builder.Services.AddRadzenComponents();

        // --- DYNAMIC HTTPCLIENT LOGIC ---
        string backendUrl;

        if (DeviceInfo.DeviceType == DeviceType.Virtual && DeviceInfo.Platform == DevicePlatform.Android)
        {
            backendUrl = "http://10.0.2.2:8000/"; 
        }
        else
        {
            backendUrl = "http://127.0.0.1:8000/";
        }

        // 1. Register the TokenHandler (The Interceptor)
        builder.Services.AddTransient<TokenHandler>();

        // 2. Register HttpClient and tell it to use the TokenHandler
        builder.Services.AddScoped(sp => 
        {
            var handler = sp.GetRequiredService<TokenHandler>();
            handler.InnerHandler = new HttpClientHandler(); 
            
            return new HttpClient(handler) { BaseAddress = new Uri(backendUrl) };
        });

        // --- 🚨 AUTHENTICATION CORE (MISSING BEFORE) 🚨 ---
        builder.Services.AddAuthorizationCore(); 
        builder.Services.AddScoped<AuthenticationStateProvider, CustomAuthStateProvider>();
        // --------------------------------------------------

#if DEBUG
        builder.Services.AddBlazorWebViewDeveloperTools();
        builder.Logging.AddDebug();
#endif

        // Register our custom services
        builder.Services.AddScoped<AuthService>();
        
        return builder.Build();
    }
}