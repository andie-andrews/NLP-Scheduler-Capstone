using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Schedules.Models;
using Scheduler.Api.Features.Shifts.Handlers;
using Scheduler.Api.Infrastructure.Domain.Models;

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

  /// <summary>
  /// Get all shifts for an employee.
  /// </summary>
  /// <param name="employeeId">Employee ID</param>
  /// <param name="weekStart">Optional week start filter</param>
  [HttpGet("employees/{employeeId}/shifts")]
  [ProducesResponseType(typeof(IEnumerable<Shift>), 200)]
  [ProducesResponseType(403)]
  public async Task<IActionResult> GetEmployeeShifts([FromRoute] int employeeId, [FromQuery] DateTime? weekStart)
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

  /// <summary>
  /// Get all shifts for a schedule.
  /// </summary>
  /// <param name="scheduleId">Schedule ID</param>
  /// <param name="weekStart">Optional week start filter</param>
  [HttpGet("schedules/{scheduleId}/shifts")]
  [ProducesResponseType(typeof(IEnumerable<Shift>), 200)]
  [ProducesResponseType(403)]
  public async Task<IActionResult> GetShifts([FromRoute] int scheduleId, [FromQuery] DateTime? weekStart)
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

  /// <summary>
  /// Create a new shift for a schedule (Supervisor only).
  /// </summary>
  /// <param name="scheduleId">Schedule ID</param>
  /// <param name="request">Shift data</param>
  [HttpPost("schedules/{scheduleId}/shifts")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(200)]
  public async Task<IActionResult> CreateShift([FromRoute] int scheduleId, [FromBody] CreateShiftRequest request)
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

  /// <summary>
  /// Delete a shift (Supervisor only).
  /// </summary>
  /// <param name="shiftId">Shift ID</param>
  [HttpDelete("shifts/{shiftId}")]
  [Authorize (Roles = "Supervisor")]
  [ProducesResponseType(200)]
  public async Task<IActionResult> DeleteShift([FromRoute] int shiftId)
  {
    await _deleteShiftHandler.Handle(shiftId);
    return Ok();
  }
}