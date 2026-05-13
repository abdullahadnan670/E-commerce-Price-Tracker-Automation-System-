using System.Text.Json.Serialization;
namespace MySemesterApp.Models
{
    public class ProductDto
    {
        public int Id { get; set; }
        [JsonPropertyName("mission_id")]
        public int MissionId { get; set; }
        public string Category { get; set; } = string.Empty; // Matches the keyword
        public string Name { get; set; } = string.Empty;
        public string Price { get; set; } = string.Empty;
        public string Url { get; set; } = string.Empty;
        public string Source { get; set; } = string.Empty;
        public float? TargetPrice { get; set; }
        [JsonPropertyName("image_url")]
        public string? ImageUrl { get; set; }

    }
    public class PriceHistoryDto
{
    public int Id { get; set; }
    public float Price { get; set; }
    [JsonPropertyName("timestamp")]
    public DateTime Timestamp { get; set; }
}
}