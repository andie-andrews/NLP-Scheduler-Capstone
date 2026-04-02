using Scheduler.Api.Infrastructure.Domain.Enums;

namespace Scheduler.Api.Infrastructure.Domain.Models
{
  public class User
  {
    public int Id { get; set; }
    public string Username { get; set; }
    public string Password { get; set; } // plain for now (capstone)
    public Scheduler.Api.Infrastructure.Domain.Enums.Role Role { get; set; }
    public int EmployeeId { get; set; }
  }
}
