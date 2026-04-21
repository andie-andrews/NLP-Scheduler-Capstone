using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Shifts.Handlers;
using Scheduler.Api.Features.Shifts.Models;
using Scheduler.Api.Features.Shifts.Services;
using Scheduler.Api.Infrastructure.Api;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Shifts;

[Authorize]
[ApiController]
[Route("api/")]
public class ShiftsController : ControllerBase
{
  private readonly GetScheduleShiftsHandler _getShifts;
  private readonly DeleteShiftHandler _deleteShiftHandler;
  private readonly ShiftDomainService _shiftDomainService;

  public ShiftsController(
    GetScheduleShiftsHandler getShifts,
    DeleteShiftHandler deleteShiftHandler,
    ShiftDomainService shiftCommandService)
  {
    _getShifts = getShifts;
    _deleteShiftHandler = deleteShiftHandler;
    _shiftDomainService = shiftCommandService;
  }

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

  [HttpPost("schedules/{scheduleId}/shifts")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(200)]
  public async Task<IActionResult> CreateShift([FromRoute] int scheduleId, CreateShiftRequest request)
  {
    var userEmployeeId = int.Parse(User.FindFirst("employeeId")!.Value);

    try
    {
      await _shiftDomainService.CreateShift(scheduleId, request, userEmployeeId);
    }
    catch (ShiftValidationException ex)
    {
      return ApiResponse.Error(this, ex.StatusCode, ex.ErrorCode, ex.Message);
    }

    return Ok(ApiResponse.Ok(new { message = "Shift created successfully." }));
  }

  [HttpDelete("shifts/{shiftId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(200)]
  public async Task<IActionResult> DeleteShift([FromRoute] int shiftId)
  {
    await _deleteShiftHandler.Handle(shiftId);
    return Ok();
  }

  [HttpPut("shifts/{shiftId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(200)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> UpdateShift([FromRoute] int shiftId, UpdateShiftRequest request)
  {
    var userEmployeeId = int.Parse(User.FindFirst("employeeId")!.Value);
    bool wasUpdated;

    try
    {
      wasUpdated = await _shiftDomainService.UpdateShift(shiftId, request, userEmployeeId);
    }
    catch (ShiftValidationException ex)
    {
      return ApiResponse.Error(this, ex.StatusCode, ex.ErrorCode, ex.Message);
    }

    if (!wasUpdated)
      return NotFound();

    return Ok(ApiResponse.Ok(new { message = "Shift updated successfully." }));
  }

  [HttpPatch("shifts/{shiftId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(200)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> PatchShift([FromRoute] int shiftId, PatchShiftRequest request)
  {
    var userEmployeeId = int.Parse(User.FindFirst("employeeId")!.Value);
    bool wasUpdated;

    try
    {
      wasUpdated = await _shiftDomainService.PatchShift(shiftId, request, userEmployeeId);
    }
    catch (ShiftValidationException ex)
    {
      return ApiResponse.Error(this, ex.StatusCode, ex.ErrorCode, ex.Message);
    }

    if (!wasUpdated)
      return NotFound();

    return Ok(ApiResponse.Ok(new { message = "Shift patched successfully." }));
  }
}
