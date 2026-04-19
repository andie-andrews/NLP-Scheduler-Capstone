using System.Text.Json.Nodes;

namespace Assistant.Api.Models;

public sealed class SessionRecord
{
  public required JsonObject Session { get; set; }
  public DateTimeOffset LastSeenUtc { get; set; }
}
