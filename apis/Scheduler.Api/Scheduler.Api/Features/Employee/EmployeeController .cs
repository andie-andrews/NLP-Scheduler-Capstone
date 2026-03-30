using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

[Authorize]
[ApiController]
[Route("api/employees")]
public class EmployeeController : ControllerBase
{
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
}