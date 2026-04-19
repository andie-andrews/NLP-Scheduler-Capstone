using System.Text.Json.Nodes;

namespace Assistant.Api.Models;

public sealed class OpenApiOperation
{
  public required string OperationId { get; init; }
  public required string Method { get; init; }
  public required string PathTemplate { get; init; }
  public string Description { get; init; } = string.Empty;
  public IReadOnlyList<string> PathParameters { get; init; } = [];
  public IReadOnlyList<string> QueryParameters { get; init; } = [];
  public IReadOnlyList<string> BodyProperties { get; init; } = [];
  public IReadOnlyList<string> RequiredParameters { get; init; } = [];
  public required JsonObject ToolParameterSchema { get; init; }
}
