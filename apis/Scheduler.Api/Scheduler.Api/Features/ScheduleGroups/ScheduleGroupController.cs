using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.ScheduleGroups.Models;
using Scheduler.Api.Features.ScheduleGroups.Services;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.ScheduleGroups;

[Authorize]
[ApiController]
[Route("api/schedule-groups")]
public class ScheduleGroupController : ControllerBase
{
  private readonly ScheduleGroupDomainService _scheduleDomainService;

  public ScheduleGroupController(ScheduleGroupDomainService scheduleDomainService)
  {
    _scheduleDomainService = scheduleDomainService;
  }

  [Authorize(Roles = "Supervisor")]
  [HttpGet]
  [ProducesResponseType(typeof(IEnumerable<ScheduleGroup>), 200)]
  public async Task<IActionResult> GetScheduleGroups([FromQuery] string? query)
  {
    var result = await _scheduleDomainService.GetScheduleGroups(query);
    return Ok(result);
  }

  [HttpGet("{scheduleGroupId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(typeof(ScheduleGroup), 200)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> GetScheduleGroup([FromRoute] int scheduleGroupId)
  {
    var result = await _scheduleDomainService.GetScheduleGroups();
    return Ok(result);
  }

  [HttpPost]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(typeof(ScheduleGroup), 201)]
  public async Task<IActionResult> CreateScheduleGroup([FromBody] CreateScheduleGroupRequest request)
  {
    var employeeIdClaim = User.FindFirst("employeeId")?.Value;
    if (!int.TryParse(employeeIdClaim, out var managerId))
      return Unauthorized("Missing or invalid employeeId claim.");

    var id = await _scheduleDomainService.CreateScheduleGroup(request, managerId);
    return Ok(new { id });
  }

  [HttpPut("{scheduleGroupId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> UpdateScheduleGroup([FromRoute] int scheduleGroupId, [FromBody] UpdateScheduleGroupRequest request)
  {
    await _scheduleDomainService.UpdateScheduleGroup(scheduleGroupId, request);
    return Ok();
  }

  [HttpDelete("{scheduleGroupId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> DeleteScheduleGroup([FromRoute] int scheduleGroupId)
  {
    await _scheduleDomainService.DeleteScheduleGroup(scheduleGroupId);
    return Ok();
  }

  [HttpGet("{scheduleGroupId}/scheduleGroupEmployees")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(typeof(Infrastructure.Domain.Models.Employee), 200)]
  public async Task<IActionResult> GetEmployees([FromRoute] int scheduleGroupId)
  {
    var result = await _scheduleDomainService.GetScheduleGroupEmployees(scheduleGroupId);
    return Ok(result);
  }

  [Authorize(Roles = "Supervisor")]
  [HttpGet("/api/managers/{managerId}/managerScheduleGroups")]
  [ProducesResponseType(typeof(IEnumerable<ScheduleGroup>), 200)]
  public async Task<IActionResult> GetManagerScheduleGroups([FromRoute] int managerId)
  {
    var result = await _scheduleDomainService.GetManagerScheduleGroups(managerId);
    return Ok(result);
  }

  [HttpPost("{scheduleGroupId}/scheduleGroupEmployees/{employeeId}")]
  [Authorize(Roles = "Supervisor")]
  [ProducesResponseType(204)]
  [ProducesResponseType(typeof(ScheduleGroup), 201)]
  public async Task<IActionResult> AddScheduledEmployee([FromRoute] int scheduleGroupId, [FromRoute] int employeeId)
  {
    await _scheduleDomainService.AddEmployee(scheduleGroupId, employeeId);
    return Ok();
  }

  [HttpDelete("{scheduleGroupId}/scheduleGroupEmployees/{employeeId}")]
  [Authorize(Roles = "Supervisor")]
  public async Task<IActionResult> DeleteScheduledEmployee([FromRoute] int scheduleGroupId, [FromRoute] int employeeId)
  {
    await _scheduleDomainService.RemoveEmployee(scheduleGroupId, employeeId);
    return Ok();
  }
}
