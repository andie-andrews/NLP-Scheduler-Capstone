namespace Assistant.Api.Models;

public sealed class AuthUser
{
  public string? Role { get; init; }
  public int? EmployeeId { get; init; }
  public required string Token { get; init; }
}
