using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Employee.Handlers;
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

  public EmployeeController(
    GetEmployeeByNameHandler getByNameHandler,
    GetEmployeeByIdHandler getEmployeeByIdHandler,
    GetAllEmployeesHandler getAllHandler)
  {
    _getByNameHandler = getByNameHandler;
    _getEmployeeByIdHandler = getEmployeeByIdHandler;
    _getAllHandler = getAllHandler;
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
}