using Employee.Api.Features.Employees.Models;
using EmployeeModel = Employee.Api.Features.Employees.Models.Employee;
using ScheduleGroupModel = Employee.Api.Features.Employees.Models.ScheduleGroup;
using ShiftModel = Employee.Api.Features.Employees.Models.Shift;
using Employee.Api.Features.Employees.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Employee.Api.Controllers;

[Authorize]
[ApiController]
[Route("api/employees")]
public class EmployeesController : ControllerBase
{
  private readonly EmployeeService _employeeService;

  public EmployeesController(EmployeeService employeeService)
  {
    _employeeService = employeeService;
  }

  [HttpGet("{employeeId:int}")]
  [ProducesResponseType(typeof(EmployeeModel), 200)]
  [ProducesResponseType(403)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> GetEmployee([FromRoute] int employeeId)
  {
    if (!User.IsInRole("Supervisor") && !IsCurrentUser(employeeId))
    {
      return Forbid();
    }

    var result = await _employeeService.GetEmployeeById(employeeId);
    if (result == null)
    {
      return NotFound();
    }

    return Ok(result);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpGet]
  [ProducesResponseType(typeof(IEnumerable<EmployeeModel>), 200)]
  public async Task<IActionResult> GetEmployees([FromQuery] string? query)
  {
    var result = await _employeeService.GetEmployees(query);
    return Ok(result);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpPost]
  [ProducesResponseType(201)]
  public async Task<IActionResult> CreateEmployee([FromBody] CreateEmployeeRequest request)
  {
    var id = await _employeeService.CreateEmployee(request);
    return CreatedAtAction(nameof(GetEmployee), new { employeeId = id }, null);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpPut("{employeeId:int}")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> PutEmployee([FromRoute] int employeeId, [FromBody] UpdateEmployeeRequest request)
  {
    var updated = await _employeeService.UpdateEmployee(employeeId, request);
    if (!updated)
    {
      return NotFound();
    }

    return NoContent();
  }

  [Authorize(Roles = "Supervisor")]
  [HttpDelete("{employeeId:int}")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> DeleteEmployee([FromRoute] int employeeId)
  {
    var result = await _employeeService.DeleteEmployee(employeeId);
    if (!result)
    {
      return NotFound();
    }

    return NoContent();
  }

  [HttpGet("{employeeId:int}/shifts")]
  [ProducesResponseType(typeof(IEnumerable<ShiftModel>), 200)]
  [ProducesResponseType(403)]
  public async Task<IActionResult> GetEmployeeShifts(
    [FromRoute] int employeeId,
    [FromQuery] DateTime? startDate,
    [FromQuery] DateTime? endDate)
  {
    if (!User.IsInRole("Supervisor") && !IsCurrentUser(employeeId))
    {
      return Forbid();
    }

    var result = await _employeeService.GetEmployeeShifts(employeeId, startDate, endDate);
    return Ok(result);
  }

  [HttpGet("{employeeId:int}/employeeScheduleGroups")]
  [ProducesResponseType(typeof(IEnumerable<ScheduleGroupModel>), 200)]
  [ProducesResponseType(403)]
  public async Task<IActionResult> GetEmployeeScheduleGroups([FromRoute] int employeeId)
  {
    if (!User.IsInRole("Supervisor") && !IsCurrentUser(employeeId))
    {
      return Forbid();
    }

    var result = await _employeeService.GetEmployeeScheduleGroups(employeeId);
    return Ok(result);
  }

  private bool IsCurrentUser(int employeeId)
  {
    var employeeIdClaim = User.FindFirst("employeeId")?.Value;
    return int.TryParse(employeeIdClaim, out var jwtEmployeeId) && jwtEmployeeId == employeeId;
  }
}
