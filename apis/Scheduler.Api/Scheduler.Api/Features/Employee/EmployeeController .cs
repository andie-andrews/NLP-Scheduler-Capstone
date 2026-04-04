using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Employee.Handlers;
using Scheduler.Api.Features.Employee.Models;
using Scheduler.Api.Features.Employee.Queries;

namespace Scheduler.Api.Features.Employee;

[Authorize]
[ApiController]
[Route("api/employees")]
public class EmployeeController : ControllerBase
{
  private readonly GetEmployeeByNameHandler _getByNameHandler;
  private readonly GetEmployeeByIdHandler _getEmployeeByIdHandler;
  private readonly GetAllEmployeesHandler _getAllHandler;
  private readonly CreateEmployeeHandler _createEmployeeHandler;
  private readonly DeleteEmployeeHandler _deleteEmployeeHandler;
  private readonly UpdateEmployeeHandler _updateEmployeeHandler;

  public EmployeeController(
    GetEmployeeByNameHandler getByNameHandler,
    GetEmployeeByIdHandler getEmployeeByIdHandler,
    GetAllEmployeesHandler getAllHandler,
    CreateEmployeeHandler createEmployeeHandler,
    DeleteEmployeeHandler deleteEmployeeHandler,
    UpdateEmployeeHandler updateEmployeeHandler)
  {
    _getByNameHandler = getByNameHandler;
    _getEmployeeByIdHandler = getEmployeeByIdHandler;
    _getAllHandler = getAllHandler;
    _createEmployeeHandler = createEmployeeHandler;
    _deleteEmployeeHandler = deleteEmployeeHandler;
    _updateEmployeeHandler = updateEmployeeHandler;
  }

  [HttpGet("{employeeId}")]
  public async Task<IActionResult> GetEmployee(int employeeId)
  {
    var jwtEmployeeId = int.Parse(User.FindFirst("employeeId")!.Value);
    var role = User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value;

    if (role != "Supervisor" && jwtEmployeeId != employeeId)
      return Forbid();

    var result = await _getEmployeeByIdHandler.Handle(employeeId);

    if (result == null)
      return NotFound();

    return Ok(result);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpGet]
  public async Task<IActionResult> GetEmployees([FromQuery] string? query)
  {
    // 🔹 No query → return all
    if (string.IsNullOrWhiteSpace(query))
    {
      var all = await _getAllHandler.Handle();
      return Ok(all);
    }

    // 🔹 Split query
    var parts = query.Split(' ', StringSplitOptions.RemoveEmptyEntries);

    string? firstName = null;
    string? lastName = null;

    if (parts.Length == 1)
    {
      firstName = parts[0];
      lastName = parts[0];
    }
    else
    {
      firstName = parts[0];
      lastName = parts[1];
    }

    var result = await _getByNameHandler.Handle(
      new EmployeeQueries.GetEmployeeByNameQuery(firstName, lastName));

    return Ok(result);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpPost]
  public async Task<IActionResult> CreateEmployee(CreateEmployeeRequest request)
  {
    var id = await _createEmployeeHandler.Handle(request);
    return CreatedAtAction(nameof(GetEmployee), new { employeeId = id }, null);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpDelete("{employeeId}")]
  public async Task<IActionResult> DeleteEmployee(int employeeId)
  {
    var result = await _deleteEmployeeHandler.Handle(employeeId);
    if (!result)
      return NotFound();

    return NoContent();
  }

  [Authorize(Roles = "Supervisor")]
  [HttpPut("{employeeId}")]
  public async Task<IActionResult> PutEmployee(int employeeId, UpdateEmployeeRequest request)
  {
    var updated = await _updateEmployeeHandler.Handle(employeeId, request);
    if (!updated)
      return NotFound();

    return NoContent();
  }
}