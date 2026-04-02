using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Employee.Handlers;
using Scheduler.Api.Features.Employee.Queries;

//[Authorize]
[ApiController]
[Route("api/employees")]
public class EmployeeController : ControllerBase
{
  private readonly GetEmployeeByNameHandler _handler;

  public EmployeeController(GetEmployeeByNameHandler handler)
  {
    _handler = handler;
  }

  [HttpGet("me")]
  public IActionResult GetMe()
  {
    var employeeId = User.FindFirst("employeeId")?.Value;
    return Ok(new { employeeId });
  }

  [Authorize(Roles = "Supervisor")]
  [HttpGet("{id}")]
  public IActionResult GetEmployee(int id)
  {
    return Ok($"Supervisor accessing employee {id}");
  }

  [HttpGet("search")]
  public async Task<IActionResult> GetByName(
    [FromQuery] string firstName,
    [FromQuery] string lastName)
  {
    var result = await _handler.Handle(
      new EmployeeQueries.GetEmployeeByNameQuery(firstName, lastName));

    if (result == null)
      return NotFound();

    return Ok(result);
  }
}