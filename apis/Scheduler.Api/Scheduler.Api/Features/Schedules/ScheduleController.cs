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

  [Authorize(Roles = "Supervisor")]
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

  [HttpPost]
  [Authorize(Roles = "Supervisor")]
  public async Task<IActionResult> CreateSchedule([FromBody] CreateScheduleRequest request)
  {
    var id = await _createScheduleHandler.Handle(request.Name);
    return Ok(new { id });
  }

  [HttpPut("{scheduleId}")]
  [Authorize(Roles = "Supervisor")]
  public async Task<IActionResult> UpdateSchedule(int scheduleId, [FromBody] UpdateScheduleRequest request)
  {
    await _updateScheduleHandler.Handle(scheduleId, request.Name);
    return Ok();
  }

  [HttpDelete("{scheduleId}")]
  [Authorize(Roles = "Supervisor")]
  public async Task<IActionResult> DeleteSchedule(int scheduleId)
  {
    await _deleteScheduleHandler.Handle(scheduleId);
    return Ok();
  }

  [HttpPost("{scheduleId}/scheduleEmployees/{employeeId}")]
  public async Task<IActionResult> AddScheduledEmployee(int scheduleId, int employeeId)
  {
    await _addEmployeeToScheduleHandler.Handle(scheduleId, employeeId);
    return Ok();
  }

  [HttpDelete("{scheduleId}/scheduleEmployees/{employeeId}")]
  public async Task<IActionResult> DeleteScheduledEmployee(int scheduleId, int employeeId)
  {
    await _deleteEmployeeToScheduleHandler.Handle(scheduleId, employeeId);
    return Ok();
  }
}