namespace Scheduler.Api.Infrastructure.Domain.Models;

public class Employee
{
  public int Id { get; set; }

  public string FirstName { get; set; } = default!;

  public string LastName { get; set; } = default!;

  public string Email { get; set; } = default!;

  public byte RoleId { get; set; }

  public string FullName => $"{FirstName} {LastName}";
}
