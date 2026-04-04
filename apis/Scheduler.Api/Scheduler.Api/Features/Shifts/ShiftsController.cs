using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Schedules.Models;
using Scheduler.Api.Features.Shifts.Handlers;

namespace Scheduler.Api.Features.Shifts;

[Authorize]
[ApiController]
[Route("api/")]
public class ShiftsController : ControllerBase
{
  private readonly GetScheduleShiftsHandler _getShifts;
  private readonly GetEmployeeShiftsHandler _getEmployeeShifts;
  private readonly CreateShiftHandler _createShiftHandler;
  private readonly DeleteShiftHandler _deleteShiftHandler;
  public ShiftsController(
    GetScheduleShiftsHandler getShifts,
    CreateShiftHandler createShift, 
    GetEmployeeShiftsHandler getEmployeeShifts,
    DeleteShiftHandler deleteShiftHandler)
  {
    _getShifts = getShifts;
    _createShiftHandler = createShift;
    _getEmployeeShifts = getEmployeeShifts;
    _deleteShiftHandler = deleteShiftHandler;
  }

  [HttpGet("employees/{employeeId}/shifts")]
  public async Task<IActionResult> GetEmployeeShifts(int employeeId, [FromQuery] DateTime? weekStart)
  {
    if (!User.IsInRole("Supervisor"))
    {
      var employeeIdClaim = User.FindFirst("employeeId");
      if (employeeIdClaim == null)
        return Forbid();

      var userEmployeeId = int.Parse(employeeIdClaim.Value);

      if(userEmployeeId != employeeId)
        return Forbid();
    }

    var result = await _getEmployeeShifts.Handle(employeeId, weekStart);
    return Ok(result);
  }

  [HttpGet("schedules/{scheduleId}/shifts")]
  public async Task<IActionResult> GetShifts(int scheduleId, [FromQuery] DateTime? weekStart)
  {
    int? employeeId = null;

    if (!User.IsInRole("Supervisor"))
    {
        var employeeIdClaim = User.FindFirst("employeeId");
        if (employeeIdClaim == null)
            return Forbid();

        employeeId = int.Parse(employeeIdClaim.Value);
    }

    var result = await _getShifts.Handle(scheduleId, weekStart, employeeId);
    return Ok(result);
  }

  [HttpPost("schedules/{scheduleId}/shifts")]
  [Authorize(Roles = "Supervisor")]
  public async Task<IActionResult> CreateShift(int scheduleId, [FromBody] CreateShiftRequest request)
  {
    var userEmployeeId = int.Parse(User.FindFirst("employeeId")!.Value);

    await _createShiftHandler.Handle(
      scheduleId,
      request.EmployeeId,
      request.Start,
      request.DurationHours,
      userEmployeeId
    );

    return Ok();
  }

  [HttpDelete("shifts/{shiftId}")]
  [Authorize (Roles = "Supervisor")]
  public async Task<IActionResult> DeleteShift(int shiftId)
  {
    await _deleteShiftHandler.Handle(shiftId);
    return Ok();
  }
}