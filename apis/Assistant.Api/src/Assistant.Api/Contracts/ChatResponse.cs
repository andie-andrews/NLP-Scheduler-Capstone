using System.Text.Json.Nodes;

namespace Assistant.Api.Contracts;

public sealed class ChatResponse
{
  public required string ConversationId { get; init; }
  public required JsonNode? Response { get; init; }
}
