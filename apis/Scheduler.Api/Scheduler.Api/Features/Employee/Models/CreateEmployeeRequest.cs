using System.ComponentModel.DataAnnotations;

namespace Scheduler.Api.Features.Employee.Models
{
  public class CreateEmployeeRequest
  {
    [Required]
    public string FirstName { get; set; } = string.Empty;

    [Required]
    public string LastName { get; set; } = string.Empty;

    [Required]
    [EmailAddress]
    public string Email { get; set; } = string.Empty;

    [Range(1, 2)]
    public int RoleId { get; set; }
  }
}
