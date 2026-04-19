using System.Text.Json.Nodes;

namespace Assistant.Api.Models;

public sealed class OrchestratorResult
{
  public required JsonNode? Response { get; init; }
  public required JsonObject Session { get; init; }
}
