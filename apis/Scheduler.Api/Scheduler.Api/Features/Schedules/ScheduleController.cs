using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Schedules.Handlers;
using Scheduler.Api.Features.Schedules.Models;

namespace Scheduler.Api.Features.Schedules;

[Authorize]
[ApiController]
[Route("api/schedules")]
public class ScheduleController : ControllerBase
{
  private readonly GetMyScheduleHandler _getMyScheduleHandler;
  private readonly GetSchedulesHandler _getSchedules;
  private readonly GetScheduleEmployeesHandler _getEmployees;
  private readonly GetScheduleShiftsHandler _getShifts;
  private readonly CreateShiftHandler _createShift;

  public ScheduleController(
    GetMyScheduleHandler getMyScheduleHandler, 
    GetSchedulesHandler getSchedules, 
    GetScheduleEmployeesHandler getEmployees, GetScheduleShiftsHandler getShifts, 
    CreateShiftHandler createShift)
  {
        _getMyScheduleHandler = getMyScheduleHandler;
        _getSchedules = getSchedules;
        _getEmployees = getEmployees;
        _getShifts = getShifts;
        _createShift = createShift;
  }
  [HttpGet("my")]
  public async Task<IActionResult> GetMy([FromQuery] DateTime? weekStart)
  {
    var employeeId = int.Parse(User.FindFirst("employeeId")!.Value);

    var start = weekStart ?? DateTime.UtcNow.Date;
    var result = await _getMyScheduleHandler.Handle(employeeId, start);

    return Ok(result);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpPost]
  [HttpGet]
  public async Task<IActionResult> GetSchedules()
  {
    var result = await _getSchedules.Handle();
    return Ok(result);
  }

  [HttpGet("{scheduleId}/employees")]
  public async Task<IActionResult> GetEmployees(int scheduleId)
  {
    var result = await _getEmployees.Handle(scheduleId);
    return Ok(result);
  }

  [HttpGet("{scheduleId}/shifts")]
  public async Task<IActionResult> GetShifts(int scheduleId, [FromQuery] DateTime? weekStart)
  {
    var result = await _getShifts.Handle(scheduleId, weekStart);
    return Ok(result);
  }

  [HttpPost("{scheduleId}/shifts")]
  [Authorize(Roles = "Supervisor")]
  public async Task<IActionResult> CreateShift(int scheduleId, [FromBody] CreateShiftRequest request)
  {
    var userEmployeeId = int.Parse(User.FindFirst("employeeId")!.Value);

    await _createShift.Handle(
      scheduleId,
      request.EmployeeId,
      request.Start,
      request.DurationHours,
      userEmployeeId
    );

    return Ok();
  }
}