namespace Assistant.Api.Contracts;

public sealed class ChatRequest
{
  public string Message { get; set; } = string.Empty;
  public string? ConversationId { get; set; }
}
