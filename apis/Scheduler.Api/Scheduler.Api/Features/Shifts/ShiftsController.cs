using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Schedules.Models;
using Scheduler.Api.Features.Shifts.Handlers;
using Scheduler.Api.Features.Shifts.Models;
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
  private readonly UpdateShiftHandler _updateShiftHandler;
  public ShiftsController(
    GetScheduleShiftsHandler getShifts,
    CreateShiftHandler createShift, 
    GetEmployeeShiftsHandler getEmployeeShifts,
    DeleteShiftHandler deleteShiftHandler,
    UpdateShiftHandler updateShiftHandler)
  {
    _getShifts = getShifts;
    _createShiftHandler = createShift;
    _getEmployeeShifts = getEmployeeShifts;
    _deleteShiftHandler = deleteShiftHandler;
    _updateShiftHandler = updateShiftHandler;
  }

  /// <summary>
  /// Get all shifts for an employee.
  /// </summary>
  /// <param name="employeeId">Employee ID</param>
  /// <param name="startDate">Optional inclusive start date filter</param>
  /// <param name="endDate">Optional inclusive end date filter</param>
  [HttpGet("employees/{employeeId}/shifts")]
  [ProducesResponseType(typeof(IEnumerable<Shift>), 200)]
  [ProducesResponseType(403)]
  public async Task<IActionResult> GetEmployeeShifts(
    [FromRoute] int employeeId,
    [FromQuery] DateTime? startDate,
    [FromQuery] DateTime? endDate)
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

    var result = await _getEmployeeShifts.Handle(employeeId, startDate, endDate);
    return Ok(result);
  }

  /// <summary>
  /// Get all shifts for a schedule.
  /// </summary>
  /// <param name="scheduleId">Schedule ID</param>
  /// <param name="startDate">Optional inclusive start date filter</param>
  /// <param name="endDate">Optional inclusive end date filter</param>
  [HttpGet("schedules/{scheduleId}/shifts")]
  [ProducesResponseType(typeof(IEnumerable<Shift>), 200)]
  [ProducesResponseType(403)]
  public async Task<IActionResult> GetShifts(
    [FromRoute] int scheduleId,
    [FromQuery] DateTime? startDate,
    [FromQuery] DateTime? endDate)
  {
    int? employeeId = null;

    if (!User.IsInRole("Supervisor"))
    {
        var employeeIdClaim = User.FindFirst("employeeId");
        if (employeeIdClaim == null)
            return Forbid();

        employeeId = int.Parse(employeeIdClaim.Value);
    }

    var result = await _getShifts.Handle(scheduleId, startDate, endDate, employeeId);
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
  public async Task<IActionResult> CreateShift([FromRoute] int scheduleId, CreateShiftRequest request)
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

  /// <summary>
  /// Update a shift (Supervisor only).
  /// </summary>
  [HttpPut("shifts/{shiftId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(200)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> UpdateShift([FromRoute] int shiftId, UpdateShiftRequest request)
  {
    var userEmployeeId = int.Parse(User.FindFirst("employeeId")!.Value);
    var wasUpdated = await _updateShiftHandler.Handle(
      shiftId,
      request.Start,
      request.DurationHours,
      userEmployeeId
    );

    if (!wasUpdated)
      return NotFound();

    return Ok();
  }
}
