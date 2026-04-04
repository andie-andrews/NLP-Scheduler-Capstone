namespace Scheduler.Api.Features.Employee.Models
{
  public class UpdateEmployeeRequest
  {
    public string FirstName { get; set; }
    public string LastName { get; set; }
    public int? RoleId { get; set; }
  }
}
