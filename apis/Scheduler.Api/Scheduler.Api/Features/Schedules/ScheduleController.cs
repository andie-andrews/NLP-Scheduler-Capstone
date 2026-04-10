using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Schedules.Handlers;
using Scheduler.Api.Features.Schedules.Models;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Schedules;

[Authorize]
[ApiController]
[Route("api/schedules")]
public class ScheduleController : ControllerBase
{
  private readonly GetSchedulesHandler _getSchedules;
  private readonly GetScheduleEmployeesHandler _getEmployees;
  private readonly AddEmployeeToScheduleHandler _addEmployeeToScheduleHandler;
  private readonly DeleteEmployeeToScheduleHandler _deleteEmployeeToScheduleHandler;

  private readonly CreateScheduleHandler _createScheduleHandler;
  private readonly UpdateScheduleHandler _updateScheduleHandler;
  private readonly DeleteScheduleHandler _deleteScheduleHandler;

  public ScheduleController(
    GetSchedulesHandler getSchedules,
    GetScheduleEmployeesHandler getEmployees,
    CreateScheduleHandler createScheduleHandler,
    UpdateScheduleHandler updateScheduleHandler,
    DeleteScheduleHandler deleteScheduleHandler,
    AddEmployeeToScheduleHandler addEmployeeToScheduleHandler,
    DeleteEmployeeToScheduleHandler deleteEmployeeToScheduleHandler
  )
  {
    _getSchedules = getSchedules;
    _getEmployees = getEmployees;

    _createScheduleHandler = createScheduleHandler;
    _updateScheduleHandler = updateScheduleHandler;
    _deleteScheduleHandler = deleteScheduleHandler;
    _addEmployeeToScheduleHandler = addEmployeeToScheduleHandler;
    _deleteEmployeeToScheduleHandler = deleteEmployeeToScheduleHandler;
  }

  /// <summary>
  /// Gets all schedules. Only accessible by Supervisors.
  /// </summary>
  /// <returns>A list of schedules.</returns>
  [Authorize(Roles = "Supervisor")]
  [HttpGet]
  [ProducesResponseType(typeof(IEnumerable<Schedule>), 200)]
  public async Task<IActionResult> GetSchedules([FromQuery] string? query)
  {
    if (string.IsNullOrWhiteSpace(query))
    {
      var all = await _getSchedules.Handle();
      return Ok(all);
    }

    var result = await _getSchedules.Handle(query);
    return Ok(result);
  }

  /// <summary>
  /// Gets a schedule by its unique identifier.
  /// </summary>
  /// <param name="scheduleId">The unique identifier of the schedule.</param>
  /// <returns>The schedule if found; otherwise, 404.</returns>
  [HttpGet("{scheduleId}")]
  [ProducesResponseType(typeof(Schedule), 200)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> GetSchedule([FromRoute] int scheduleId)
  {
    var result = await _getSchedules.Handle();
    return Ok(result);
  }

  /// <summary>
  /// Creates a new schedule.
  /// </summary>
  /// <param name="request">The schedule creation data.</param>
  /// <returns>The ID of the created schedule.</returns>
  [HttpPost]
  [ProducesResponseType(typeof(Schedule), 201)]
  public async Task<IActionResult> CreateSchedule([FromBody] CreateScheduleRequest request)
  {
    var id = await _createScheduleHandler.Handle(request.Name);
    return Ok(new { id });
  }

  /// <summary>
  /// Updates an existing schedule.
  /// </summary>
  /// <param name="scheduleId">The unique identifier of the schedule to update.</param>
  /// <param name="request">The updated schedule data.</param>
  /// <returns>No content if successful; otherwise, 404.</returns>
  [HttpPut("{scheduleId}")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> UpdateSchedule([FromRoute] int scheduleId, [FromBody] UpdateScheduleRequest request)
  {
    await _updateScheduleHandler.Handle(scheduleId, request.Name);
    return Ok();
  }

  /// <summary>
  /// Deletes a schedule by its unique identifier.
  /// </summary>
  /// <param name="scheduleId">The unique identifier of the schedule to delete.</param>
  /// <returns>No content if successful; otherwise, 404.</returns>
  [HttpDelete("{scheduleId}")]
  [ProducesResponseType(204)]
  [ProducesResponseType(404)]
  public async Task<IActionResult> DeleteSchedule([FromRoute] int scheduleId)
  {
    await _deleteScheduleHandler.Handle(scheduleId);
    return Ok();
  }

  /// <summary>
  /// Gets all employees assigned to a schedule.
  /// </summary>
  /// <param name="scheduleId">The unique identifier of the schedule.</param>
  /// <returns>A list of employees assigned to the schedule.</returns>
  [HttpGet("{scheduleId}/scheduleEmployees")]
  [ProducesResponseType(typeof(Infrastructure.Domain.Models.Employee), 200)]
  public async Task<IActionResult> GetEmployees([FromRoute] int scheduleId)
  {
    var result = await _getEmployees.Handle(scheduleId);
    return Ok(result);
  }

  /// <summary>
  /// Adds an employee to a schedule.
  /// </summary>
  /// <param name="scheduleId">The unique identifier of the schedule.</param>
  /// <param name="employeeId">The unique identifier of the employee to add.</param>
  /// <returns>No content if successful.</returns>
  [HttpPost("{scheduleId}/scheduleEmployees/{employeeId}")]
  [ProducesResponseType(204)]
  [ProducesResponseType(typeof(Schedule), 201)]
  public async Task<IActionResult> AddScheduledEmployee([FromRoute] int scheduleId, [FromRoute] int employeeId)
  {
    await _addEmployeeToScheduleHandler.Handle(scheduleId, employeeId);
    return Ok();
  }

  /// <summary>
  /// Removes an employee from a schedule.
  /// </summary>
  /// <param name="scheduleId">The unique identifier of the schedule.</param>
  /// <param name="employeeId">The unique identifier of the employee to remove.</param>
  /// <returns>No content if successful.</returns>
  [HttpDelete("{scheduleId}/scheduleEmployees/{employeeId}")]
  public async Task<IActionResult> DeleteScheduledEmployee([FromRoute] int scheduleId, [FromRoute] int employeeId)
  {
    await _deleteEmployeeToScheduleHandler.Handle(scheduleId, employeeId);
    return Ok();
  }
}