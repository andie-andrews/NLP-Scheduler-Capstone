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

  /// <summary>
  /// Get an employee by ID.
  /// </summary>
  /// <param name="employeeId">Employee ID</param>
  /// <returns>Employee details</returns>
  [HttpGet("{employeeId}")]
  [ProducesResponseType(typeof(Infrastructure.Domain.Models.Employee), 200)]
  [ProducesResponseType(403)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> GetEmployee([FromRoute] int employeeId)
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

  /// <summary>
  /// Get all employees or search by name (Supervisor only).
  /// </summary>
  /// <param name="query">Optional search query</param>
  /// <returns>List of employees</returns>
  [Authorize(Roles = "Supervisor")]
  [HttpGet]
  [ProducesResponseType(typeof(IEnumerable<Infrastructure.Domain.Models.Employee>), 200)]
  public async Task<IActionResult> GetEmployees([FromQuery] string? query)
  {
    if (string.IsNullOrWhiteSpace(query))
    {
      var all = await _getAllHandler.Handle();
      return Ok(all);
    }

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
      new EmployeeQueries.GetEmployeeByNameQuery(firstName, lastName, parts.Length > 1));

    return Ok(result);
  }

  /// <summary>
  /// Create a new employee (Supervisor only).
  /// </summary>
  /// <param name="request">Employee data</param>
  /// <returns>Created employee</returns>
  [Authorize(Roles = "Supervisor")]
  [HttpPost]
  [ProducesResponseType(201)]
  public async Task<IActionResult> CreateEmployee([FromBody] CreateEmployeeRequest request)
  {
    var id = await _createEmployeeHandler.Handle(request);
    return CreatedAtAction(nameof(GetEmployee), new { employeeId = id }, null);
  }

  /// <summary>
  /// Delete an employee (Supervisor only).
  /// </summary>
  /// <param name="employeeId">Employee ID</param>
  [Authorize(Roles = "Supervisor")]
  [HttpDelete("{employeeId}")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> DeleteEmployee([FromRoute] int employeeId)
  {
    var result = await _deleteEmployeeHandler.Handle(employeeId);
    if (!result)
      return NotFound();

    return NoContent();
  }

  /// <summary>
  /// Update an employee (Supervisor only).
  /// </summary>
  /// <param name="employeeId">Employee ID</param>
  /// <param name="request">Update data</param>
  [Authorize(Roles = "Supervisor")]
  [HttpPut("{employeeId}")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> PutEmployee([FromRoute] int employeeId, [FromBody] UpdateEmployeeRequest request)
  {
    var updated = await _updateEmployeeHandler.Handle(employeeId, request);
    if (!updated)
      return NotFound();

    return NoContent();
  }
}
