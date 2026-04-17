using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Schedules.Models;
using Scheduler.Api.Features.Schedules.Services;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Schedules;

[Authorize]
[ApiController]
[Route("api/schedules")]
public class ScheduleController : ControllerBase
{
  private readonly ScheduleDomainService _scheduleDomainService;

  public ScheduleController(ScheduleDomainService scheduleDomainService)
  {
    _scheduleDomainService = scheduleDomainService;
  }

  [Authorize(Roles = "Supervisor")]
  [HttpGet]
  [ProducesResponseType(typeof(IEnumerable<Schedule>), 200)]
  public async Task<IActionResult> GetSchedules([FromQuery] string? query)
  {
    var result = await _scheduleDomainService.GetSchedules(query);
    return Ok(result);
  }

  [HttpGet("{scheduleId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(typeof(Schedule), 200)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> GetSchedule([FromRoute] int scheduleId)
  {
    var result = await _scheduleDomainService.GetSchedules();
    return Ok(result);
  }

  [HttpPost]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(typeof(Schedule), 201)]
  public async Task<IActionResult> CreateSchedule([FromBody] CreateScheduleRequest request)
  {
    var employeeIdClaim = User.FindFirst("employeeId")?.Value;
    if (!int.TryParse(employeeIdClaim, out var managerId))
      return Unauthorized("Missing or invalid employeeId claim.");

    var id = await _scheduleDomainService.CreateSchedule(request, managerId);
    return Ok(new { id });
  }

  [HttpPut("{scheduleId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> UpdateSchedule([FromRoute] int scheduleId, [FromBody] UpdateScheduleRequest request)
  {
    await _scheduleDomainService.UpdateSchedule(scheduleId, request);
    return Ok();
  }

  [HttpDelete("{scheduleId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> DeleteSchedule([FromRoute] int scheduleId)
  {
    await _scheduleDomainService.DeleteSchedule(scheduleId);
    return Ok();
  }

  [HttpGet("{scheduleId}/scheduleEmployees")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(typeof(Infrastructure.Domain.Models.Employee), 200)]
  public async Task<IActionResult> GetEmployees([FromRoute] int scheduleId)
  {
    var result = await _scheduleDomainService.GetScheduleEmployees(scheduleId);
    return Ok(result);
  }

  [HttpGet("/api/employees/{employeeId}/employeeSchedules")]
  [ProducesResponseType(typeof(IEnumerable<Schedule>), 200)]
  [ProducesResponseType(403)]
  public async Task<IActionResult> GetEmployeeSchedules([FromRoute] int employeeId)
  {
    if (!User.IsInRole("Supervisor"))
    {
      var employeeIdClaim = User.FindFirst("employeeId")?.Value;
      if (!int.TryParse(employeeIdClaim, out var userEmployeeId))
        return Forbid();

      if (userEmployeeId != employeeId)
        return Forbid();
    }

    var result = await _scheduleDomainService.GetEmployeeSchedules(employeeId);
    return Ok(result);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpGet("/api/managers/{managerId}/managerSchedules")]
  [ProducesResponseType(typeof(IEnumerable<Schedule>), 200)]
  public async Task<IActionResult> GetManagerSchedules([FromRoute] int managerId)
  {
    var result = await _scheduleDomainService.GetManagerSchedules(managerId);
    return Ok(result);
  }

  [HttpPost("{scheduleId}/scheduleEmployees/{employeeId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(204)]
  [ProducesResponseType(typeof(Schedule), 201)]
  public async Task<IActionResult> AddScheduledEmployee([FromRoute] int scheduleId, [FromRoute] int employeeId)
  {
    await _scheduleDomainService.AddEmployee(scheduleId, employeeId);
    return Ok();
  }

  [HttpDelete("{scheduleId}/scheduleEmployees/{employeeId}")]
  [Authorize(Roles = "Supervisor")]
  public async Task<IActionResult> DeleteScheduledEmployee([FromRoute] int scheduleId, [FromRoute] int employeeId)
  {
    await _scheduleDomainService.RemoveEmployee(scheduleId, employeeId);
    return Ok();
  }
}
