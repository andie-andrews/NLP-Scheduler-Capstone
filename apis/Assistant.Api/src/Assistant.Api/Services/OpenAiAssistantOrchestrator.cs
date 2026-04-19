using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Assistant.Api.Models;

namespace Assistant.Api.Services;

/// <summary>
/// Orchestrates assistant interactions via OpenAI tool-calling grounded by OpenAPI-derived tools.
/// </summary>
public sealed class OpenAiAssistantOrchestrator
{
  private readonly HttpClient _httpClient;
  private readonly OpenApiToolRegistry _toolRegistry;
  private readonly SchedulerApiClient _schedulerApiClient;
  private readonly string _model;

  /// <summary>
  /// Initializes OpenAI client dependencies and validates required API configuration.
  /// </summary>
  public OpenAiAssistantOrchestrator(
    HttpClient httpClient,
    IConfiguration configuration,
    OpenApiToolRegistry toolRegistry,
    SchedulerApiClient schedulerApiClient)
  {
    _httpClient = httpClient;
    _toolRegistry = toolRegistry;
    _schedulerApiClient = schedulerApiClient;

    var apiKey = configuration["OPENAI_API_KEY"];
    if (string.IsNullOrWhiteSpace(apiKey))
    {
      throw new InvalidOperationException("OPENAI_API_KEY is required for OpenAI orchestration.");
    }

    _model = configuration["ASSISTANT_OPENAI_MODEL"] ?? "gpt-4o-mini";
    _httpClient.BaseAddress = new Uri("https://api.openai.com");
    _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);
  }

  /// <summary>
  /// Processes a user message, executes any model-selected tools, and returns assistant output + updated session.
  /// </summary>
  public async Task<OrchestratorResult> RunAsync(string userMessage, AuthUser user, JsonObject session, CancellationToken ct)
  {
    var messages = session["messages"] as JsonArray ?? [];
    session["messages"] = messages;

    messages.Add(new JsonObject
    {
      ["role"] = "user",
      ["content"] = userMessage,
    });

    var tools = _toolRegistry.GetTools();
    var systemPrompt = BuildSystemPrompt(user);

    var first = await CreateCompletionAsync(messages, tools, systemPrompt, ct);
    var assistantMessage = first["choices"]?[0]?["message"] as JsonObject
      ?? throw new InvalidOperationException("OpenAI returned no assistant message.");

    messages.Add(assistantMessage.DeepClone());

    var toolCalls = assistantMessage["tool_calls"] as JsonArray;
    if (toolCalls is not null && toolCalls.Count > 0)
    {
      foreach (var callNode in toolCalls)
      {
        if (callNode is not JsonObject toolCall) continue;

        var toolCallId = toolCall["id"]?.GetValue<string>() ?? Guid.NewGuid().ToString("N");
        var function = toolCall["function"] as JsonObject;
        var operationId = function?["name"]?.GetValue<string>();
        var argumentsRaw = function?["arguments"]?.GetValue<string>() ?? "{}";
        var arguments = JsonNode.Parse(argumentsRaw) as JsonObject ?? new JsonObject();

        if (string.IsNullOrWhiteSpace(operationId) || !_toolRegistry.TryGetOperation(operationId, out var operation))
        {
          messages.Add(new JsonObject
          {
            ["role"] = "tool",
            ["tool_call_id"] = toolCallId,
            ["content"] = JsonSerializer.Serialize(new { error = $"Unknown tool '{operationId}'" }),
          });
          continue;
        }

        JsonNode? toolResult;
        try
        {
          toolResult = await _schedulerApiClient.ExecuteOperationAsync(operation, arguments, user.Token, ct);
        }
        catch (Exception ex)
        {
          toolResult = new JsonObject
          {
            ["error"] = ex.Message,
          };
        }

        messages.Add(new JsonObject
        {
          ["role"] = "tool",
          ["tool_call_id"] = toolCallId,
          ["content"] = toolResult?.ToJsonString() ?? "{}",
        });
      }

      var followUp = await CreateCompletionAsync(messages, tools, systemPrompt, ct);
      var finalMessage = followUp["choices"]?[0]?["message"] as JsonObject
        ?? throw new InvalidOperationException("OpenAI returned no final assistant message.");

      messages.Add(finalMessage.DeepClone());
      return new OrchestratorResult
      {
        Response = new JsonObject
        {
          ["type"] = "assistant",
          ["message"] = ExtractTextContent(finalMessage),
          ["raw"] = finalMessage.DeepClone(),
        },
        Session = session,
      };
    }

    return new OrchestratorResult
    {
      Response = new JsonObject
      {
        ["type"] = "assistant",
        ["message"] = ExtractTextContent(assistantMessage),
        ["raw"] = assistantMessage.DeepClone(),
      },
      Session = session,
    };
  }

  /// <summary>
  /// Sends a chat completion request with system prompt, message history, and available tools.
  /// </summary>
  private async Task<JsonObject> CreateCompletionAsync(JsonArray messages, JsonArray tools, string systemPrompt, CancellationToken ct)
  {
    var payload = new JsonObject
    {
      ["model"] = _model,
      ["messages"] = BuildMessagesPayload(messages, systemPrompt),
      ["tools"] = tools,
      ["tool_choice"] = "auto",
      ["temperature"] = 0,
    };

    using var request = new HttpRequestMessage(HttpMethod.Post, "/v1/chat/completions")
    {
      Content = new StringContent(payload.ToJsonString(), Encoding.UTF8, "application/json"),
    };

    var response = await _httpClient.SendAsync(request, ct);
    var body = await response.Content.ReadAsStringAsync(ct);
    if (!response.IsSuccessStatusCode)
    {
      throw new InvalidOperationException($"OpenAI completion failed ({(int)response.StatusCode}): {body}");
    }

    return JsonNode.Parse(body)?.AsObject() ?? throw new InvalidOperationException("Invalid OpenAI JSON response.");
  }

  /// <summary>
  /// Prepends system prompt to conversation history for model requests.
  /// </summary>
  private static JsonArray BuildMessagesPayload(JsonArray history, string systemPrompt)
  {
    var payload = new JsonArray
    {
      new JsonObject
      {
        ["role"] = "system",
        ["content"] = systemPrompt,
      },
    };

    foreach (var entry in history)
    {
      payload.Add(entry?.DeepClone());
    }

    return payload;
  }

  /// <summary>
  /// Builds assistant instruction context with role and employee scoping rules.
  /// </summary>
  private static string BuildSystemPrompt(AuthUser user)
  {
    var role = user.Role ?? "Employee";
    var employeeId = user.EmployeeId?.ToString() ?? "UNKNOWN";
    return $"""
You are the scheduling assistant.
Use provided OpenAPI tools whenever a scheduler operation is needed.
Do not invent API calls; only use available tools.
User role: {role}
User employeeId: {employeeId}
If user asks about 'my' data, use employeeId from context when needed.
When tool output is returned, summarize clearly and concisely.
""";
  }

  /// <summary>
  /// Extracts plain-text assistant content from string or array-form response payloads.
  /// </summary>
  private static string ExtractTextContent(JsonObject assistantMessage)
  {
    if (assistantMessage["content"] is JsonValue textValue)
    {
      return textValue.GetValue<string>();
    }

    if (assistantMessage["content"] is JsonArray contentArray)
    {
      var parts = contentArray
        .OfType<JsonObject>()
        .Select(p => p["text"]?.GetValue<string>())
        .Where(s => !string.IsNullOrWhiteSpace(s));
      return string.Join("\n", parts!);
    }

    return string.Empty;
  }
}
