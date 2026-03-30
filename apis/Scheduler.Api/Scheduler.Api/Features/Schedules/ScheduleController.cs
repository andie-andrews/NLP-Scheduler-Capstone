using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

[Authorize]
[ApiController]
[Route("api/schedules")]
public class ScheduleController : ControllerBase
{
  [HttpGet]
  public IActionResult GetMySchedule()
  {
    var employeeId = User.FindFirst("employeeId")?.Value;
    return Ok($"Schedule for employee {employeeId}");
  }

  [Authorize(Roles = "Supervisor")]
  [HttpPost]
  public IActionResult CreateSchedule()
  {
    return Ok("Schedule created");
  }
}