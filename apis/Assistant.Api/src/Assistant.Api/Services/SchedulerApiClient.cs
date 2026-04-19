using System.Net.Http.Headers;
using System.Text;
using System.Text.Json.Nodes;
using Assistant.Api.Models;

namespace Assistant.Api.Services;

/// <summary>
/// Executes Scheduler API operations selected by the model from OpenAPI-derived tools.
/// </summary>
public sealed class SchedulerApiClient
{
  private readonly HttpClient _httpClient;

  /// <summary>
  /// Configures the Scheduler API base URL.
  /// </summary>
  public SchedulerApiClient(HttpClient httpClient, IConfiguration configuration)
  {
    _httpClient = httpClient;
    var baseUrl = configuration["SCHEDULER_API_BASE_URL"] ?? "http://localhost:5048";
    _httpClient.BaseAddress = new Uri(baseUrl.TrimEnd('/'));
  }

  /// <summary>
  /// Executes a single OpenAPI operation by mapping tool arguments to path/query/body.
  /// </summary>
  public async Task<JsonNode?> ExecuteOperationAsync(OpenApiOperation operation, JsonObject arguments, string token, CancellationToken ct)
  {
    var path = operation.PathTemplate;

    foreach (var pathParam in operation.PathParameters)
    {
      if (!arguments.TryGetPropertyValue(pathParam, out var value) || value is null)
      {
        throw new InvalidOperationException($"Missing required path parameter '{pathParam}' for {operation.OperationId}.");
      }

      path = path.Replace($"{{{pathParam}}}", Uri.EscapeDataString(value.ToString()), StringComparison.Ordinal);
    }

    var queryParts = new List<string>();
    foreach (var queryParam in operation.QueryParameters)
    {
      if (!arguments.TryGetPropertyValue(queryParam, out var value) || value is null)
      {
        continue;
      }

      queryParts.Add($"{Uri.EscapeDataString(queryParam)}={Uri.EscapeDataString(value.ToString())}");
    }

    if (queryParts.Count > 0)
    {
      path = $"{path}?{string.Join('&', queryParts)}";
    }

    JsonObject? body = null;
    if (operation.BodyProperties.Count > 0)
    {
      body = new JsonObject();
      foreach (var property in operation.BodyProperties)
      {
        if (arguments.TryGetPropertyValue(property, out var value) && value is not null)
        {
          body[property] = value.DeepClone();
        }
      }
    }

    using var request = new HttpRequestMessage(new HttpMethod(operation.Method), path);
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

    if (body is not null)
    {
      request.Content = new StringContent(body.ToJsonString(), Encoding.UTF8, "application/json");
    }

    var response = await _httpClient.SendAsync(request, ct);
    var responseBody = await response.Content.ReadAsStringAsync(ct);

    if (!response.IsSuccessStatusCode)
    {
      throw new InvalidOperationException(
        $"Scheduler API call failed for {operation.OperationId} ({(int)response.StatusCode}): {responseBody}");
    }

    if (string.IsNullOrWhiteSpace(responseBody))
    {
      return null;
    }

    return JsonNode.Parse(responseBody);
  }
}
