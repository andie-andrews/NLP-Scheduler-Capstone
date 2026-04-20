using System.Collections.Concurrent;
using System.Text.Json.Nodes;
using Assistant.Api.Models;

namespace Assistant.Api.Services;

/// <summary>
/// Stores per-conversation session state in memory and evicts stale sessions by TTL.
/// </summary>
public sealed class ConversationSessionStore
{
  private readonly ConcurrentDictionary<string, SessionRecord> _sessions = new();
  private readonly TimeSpan _ttl;

  /// <summary>
  /// Initializes the in-memory store with TTL from configuration.
  /// </summary>
  public ConversationSessionStore(IConfiguration configuration)
  {
    var ttlSeconds = configuration.GetValue("ASSISTANT_SESSION_TTL_SECONDS", 60 * 60 * 8);
    _ttl = TimeSpan.FromSeconds(ttlSeconds);
  }

  /// <summary>
  /// Gets the configured session TTL in seconds.
  /// </summary>
  public int TtlSeconds => (int)_ttl.TotalSeconds;

  /// <summary>
  /// Returns the number of active (non-expired) sessions.
  /// </summary>
  public int ActiveCount
  {
    get
    {
      CleanupExpired();
      return _sessions.Count;
    }
  }

  /// <summary>
  /// Gets an existing session or creates one and refreshes caller context.
  /// </summary>
  public JsonObject GetOrCreate(string conversationId, AuthUser user)
  {
    CleanupExpired();

    var record = _sessions.GetOrAdd(conversationId, _ => new SessionRecord
    {
      LastSeenUtc = DateTimeOffset.UtcNow,
      Session = new JsonObject
      {
        ["memory"] = new JsonObject(),
        ["role"] = user.Role,
        ["employee_id"] = user.EmployeeId,
      },
    });

    record.LastSeenUtc = DateTimeOffset.UtcNow;
    record.Session["role"] = user.Role;
    record.Session["employee_id"] = user.EmployeeId;

    return record.Session;
  }

  /// <summary>
  /// Persists the latest session payload for the conversation.
  /// </summary>
  public void Update(string conversationId, JsonObject session)
  {
    _sessions[conversationId] = new SessionRecord
    {
      LastSeenUtc = DateTimeOffset.UtcNow,
      Session = session,
    };
  }

  /// <summary>
  /// Removes a conversation from the session store.
  /// </summary>
  public void Clear(string conversationId)
  {
    _sessions.TryRemove(conversationId, out _);
  }

  /// <summary>
  /// Evicts sessions whose last-seen timestamp is older than TTL.
  /// </summary>
  public void CleanupExpired()
  {
    var cutoff = DateTimeOffset.UtcNow - _ttl;
    foreach (var kvp in _sessions)
    {
      if (kvp.Value.LastSeenUtc < cutoff)
      {
        _sessions.TryRemove(kvp.Key, out _);
      }
    }
  }
}
