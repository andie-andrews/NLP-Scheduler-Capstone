using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Employee.Models;
using Scheduler.Api.Features.Employee.Services;
using Scheduler.Api.Features.Schedules.Handlers;
using Scheduler.Api.Features.Shifts.Handlers;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Employee.Api.Controllers;

[Authorize]
[ApiController]
[Route("api/employees")]
public class EmployeesController : ControllerBase
{
  private readonly EmployeeDomainService _employeeDomainService;
  private readonly GetEmployeeShiftsHandler _employeeShiftsHandler;
  private readonly GetEmployeeSchedulesHandler _employeeSchedulesHandler;

  public EmployeesController(
    EmployeeDomainService employeeDomainService,
    GetEmployeeShiftsHandler employeeShiftsHandler,
    GetEmployeeSchedulesHandler employeeSchedulesHandler)
  {
    _employeeDomainService = employeeDomainService;
    _employeeShiftsHandler = employeeShiftsHandler;
    _employeeSchedulesHandler = employeeSchedulesHandler;
  }

  [HttpGet("{employeeId:int}")]
  [ProducesResponseType(typeof(Employee), 200)]
  [ProducesResponseType(403)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> GetEmployee([FromRoute] int employeeId)
  {
    if (!User.IsInRole("Supervisor"))
    {
      var employeeIdClaim = User.FindFirst("employeeId")?.Value;
      if (!int.TryParse(employeeIdClaim, out var jwtEmployeeId) || jwtEmployeeId != employeeId)
      {
        return Forbid();
      }
    }

    var result = await _employeeDomainService.GetEmployee(employeeId);

    if (result == null)
    {
      return NotFound();
    }

    return Ok(result);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpGet]
  [ProducesResponseType(typeof(IEnumerable<Employee>), 200)]
  public async Task<IActionResult> GetEmployees([FromQuery] string? query)
  {
    var result = await _employeeDomainService.GetEmployees(query);
    return Ok(result);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpPost]
  [ProducesResponseType(201)]
  public async Task<IActionResult> CreateEmployee([FromBody] CreateEmployeeRequest request)
  {
    var id = await _employeeDomainService.CreateEmployee(request);
    return CreatedAtAction(nameof(GetEmployee), new { employeeId = id }, null);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpPut("{employeeId:int}")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> PutEmployee([FromRoute] int employeeId, [FromBody] UpdateEmployeeRequest request)
  {
    var updated = await _employeeDomainService.UpdateEmployee(employeeId, request);
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
    var result = await _employeeDomainService.DeleteEmployee(employeeId);
    if (!result)
    {
      return NotFound();
    }

    return NoContent();
  }

  [HttpGet("{employeeId:int}/shifts")]
  [ProducesResponseType(typeof(IEnumerable<Shift>), 200)]
  [ProducesResponseType(403)]
  public async Task<IActionResult> GetEmployeeShifts(
    [FromRoute] int employeeId,
    [FromQuery] DateTime? startDate,
    [FromQuery] DateTime? endDate)
  {
    if (!User.IsInRole("Supervisor"))
    {
      var employeeIdClaim = User.FindFirst("employeeId")?.Value;
      if (!int.TryParse(employeeIdClaim, out var jwtEmployeeId) || jwtEmployeeId != employeeId)
      {
        return Forbid();
      }
    }

    var result = await _employeeShiftsHandler.Handle(employeeId, startDate, endDate);
    return Ok(result);
  }

  [HttpGet("{employeeId:int}/employeeSchedules")]
  [ProducesResponseType(typeof(IEnumerable<Schedule>), 200)]
  [ProducesResponseType(403)]
  public async Task<IActionResult> GetEmployeeSchedules([FromRoute] int employeeId)
  {
    if (!User.IsInRole("Supervisor"))
    {
      var employeeIdClaim = User.FindFirst("employeeId")?.Value;
      if (!int.TryParse(employeeIdClaim, out var jwtEmployeeId) || jwtEmployeeId != employeeId)
      {
        return Forbid();
      }
    }

    var result = await _employeeSchedulesHandler.Handle(employeeId);
    return Ok(result);
  }
}
