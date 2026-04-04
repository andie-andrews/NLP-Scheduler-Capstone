namespace Scheduler.Api.Features.Employee.Models
{
  public class CreateEmployeeRequest
  {
    public string FirstName { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public int RoleId { get; set; }
  }
}
