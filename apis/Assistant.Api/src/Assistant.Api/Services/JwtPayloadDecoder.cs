using System.Text;
using System.Text.Json;
using Assistant.Api.Models;

namespace Assistant.Api.Services;

/// <summary>
/// Decodes bearer JWT payload fields used by assistant orchestration context.
/// </summary>
public sealed class JwtPayloadDecoder
{
  /// <summary>
  /// Extracts role and employeeId from an Authorization header value.
  /// </summary>
  public AuthUser DecodeFromAuthorizationHeader(string? authorization)
  {
    if (string.IsNullOrWhiteSpace(authorization) || !authorization.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
    {
      throw new UnauthorizedAccessException("Missing Bearer token");
    }

    var token = authorization["Bearer ".Length..].Trim();
    if (string.IsNullOrWhiteSpace(token))
    {
      throw new UnauthorizedAccessException("Invalid Bearer token");
    }

    try
    {
      var segments = token.Split('.');
      if (segments.Length < 2)
      {
        throw new UnauthorizedAccessException("Invalid JWT format");
      }

      var payloadJson = Encoding.UTF8.GetString(Base64UrlDecode(segments[1]));
      using var payload = JsonDocument.Parse(payloadJson);

      var root = payload.RootElement;
      string? role = root.TryGetProperty("role", out var roleProp) ? roleProp.GetString() : null;
      int? employeeId = null;

      if (root.TryGetProperty("employeeId", out var employeeProp))
      {
        if (employeeProp.ValueKind == JsonValueKind.Number && employeeProp.TryGetInt32(out var parsed))
        {
          employeeId = parsed;
        }
        else if (employeeProp.ValueKind == JsonValueKind.String && int.TryParse(employeeProp.GetString(), out parsed))
        {
          employeeId = parsed;
        }
      }

      return new AuthUser
      {
        Role = role,
        EmployeeId = employeeId,
        Token = token,
      };
    }
    catch (UnauthorizedAccessException)
    {
      throw;
    }
    catch (Exception ex)
    {
      throw new UnauthorizedAccessException($"Unable to decode token: {ex.Message}", ex);
    }
  }

  /// <summary>
  /// Decodes a base64url-encoded JWT segment into bytes.
  /// </summary>
  private static byte[] Base64UrlDecode(string input)
  {
    var s = input.Replace('-', '+').Replace('_', '/');
    switch (s.Length % 4)
    {
      case 2:
        s += "==";
        break;
      case 3:
        s += "=";
        break;
    }

    return Convert.FromBase64String(s);
  }
}
