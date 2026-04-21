using System.ComponentModel.DataAnnotations;

namespace Employee.Api.Features.Employees.Models;

public class Employee
{
  public int Id { get; set; }
  public string FirstName { get; set; } = string.Empty;
  public string LastName { get; set; } = string.Empty;
  public string Email { get; set; } = string.Empty;
  public byte RoleId { get; set; }
  public string FullName => $"{FirstName} {LastName}";
}

public class ScheduleGroup
{
  public int Id { get; set; }
  public string Name { get; set; } = string.Empty;
}

public class Shift
{
  public int Id { get; set; }
  public int ScheduleGroupId { get; set; }
  public int EmployeeId { get; set; }
  public DateTime Start { get; set; }
  public int DurationHours { get; set; }
}

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

public class UpdateEmployeeRequest
{
  [Required]
  public string FirstName { get; set; } = string.Empty;

  [Required]
  public string LastName { get; set; } = string.Empty;

  [Required]
  [EmailAddress]
  public string Email { get; set; } = string.Empty;

  [Range(1, 2)]
  public int? RoleId { get; set; }
}
