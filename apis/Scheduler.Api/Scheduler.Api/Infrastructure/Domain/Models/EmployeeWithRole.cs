namespace Scheduler.Api.Infrastructure.Domain.Models
{
  public class EmployeeWithRole
  {
    public int Id { get; set; }
    public string FirstName { get; set; } = default!;
    public string LastName { get; set; } = default!;
    public byte RoleId { get; set; }
    public string RoleName { get; set; } = default!;
  }
}
