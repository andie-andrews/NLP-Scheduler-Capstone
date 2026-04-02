using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Schedules.Handlers;

namespace Scheduler.Api.Features.Schedules;

[Authorize]
[ApiController]
[Route("api/schedules")]
public class ScheduleController : ControllerBase
{
  private readonly GetMyScheduleHandler _handler;

  public ScheduleController(GetMyScheduleHandler handler)
  {
        _handler = handler;
  }
  [HttpGet("my")]
  public async Task<IActionResult> GetMy([FromQuery] DateTime? weekStart)
  {
    var employeeId = int.Parse(User.FindFirst("employeeId")!.Value);

    var start = weekStart ?? DateTime.UtcNow.Date;
    var result = await _handler.Handle(employeeId, start);

    return Ok(result);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpPost]
  public IActionResult CreateSchedule()
  {
    return Ok("Schedule created");
  }
}