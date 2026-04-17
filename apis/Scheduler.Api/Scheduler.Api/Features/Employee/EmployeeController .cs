using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Employee.Models;
using Scheduler.Api.Features.Employee.Services;

namespace Scheduler.Api.Features.Employee;

[Authorize]
[ApiController]
[Route("api/employees")]
public class EmployeeController : ControllerBase
{
  private readonly EmployeeDomainService _employeeDomainService;

  public EmployeeController(EmployeeDomainService employeeDomainService)
  {
    _employeeDomainService = employeeDomainService;
  }

  [HttpGet("{employeeId}")]
  [ProducesResponseType(typeof(Infrastructure.Domain.Models.Employee), 200)]
  [ProducesResponseType(403)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> GetEmployee([FromRoute] int employeeId)
  {
    if (!User.IsInRole("Supervisor"))
    {
      var employeeIdClaim = User.FindFirst("employeeId")?.Value;
      if (!int.TryParse(employeeIdClaim, out var jwtEmployeeId))
        return Forbid();

      if (jwtEmployeeId != employeeId)
        return Forbid();
    }

    var result = await _employeeDomainService.GetEmployee(employeeId);

    if (result == null)
      return NotFound();

    return Ok(result);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpGet]
  [ProducesResponseType(typeof(IEnumerable<Infrastructure.Domain.Models.Employee>), 200)]
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
  [HttpDelete("{employeeId}")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> DeleteEmployee([FromRoute] int employeeId)
  {
    var result = await _employeeDomainService.DeleteEmployee(employeeId);
    if (!result)
      return NotFound();

    return NoContent();
  }

  [Authorize(Roles = "Supervisor")]
  [HttpPut("{employeeId}")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> PutEmployee([FromRoute] int employeeId, [FromBody] UpdateEmployeeRequest request)
  {
    var updated = await _employeeDomainService.UpdateEmployee(employeeId, request);
    if (!updated)
      return NotFound();

    return NoContent();
  }
}
