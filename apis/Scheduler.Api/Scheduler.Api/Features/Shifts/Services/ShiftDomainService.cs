using Dapper;
using Microsoft.AspNetCore.Http;
using Scheduler.Api.Features.Schedules.Models;
using Scheduler.Api.Features.Shifts.Handlers;
using Scheduler.Api.Features.Shifts.Models;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Shifts.Services;

public class ShiftDomainService
{
  private readonly IDbConnectionFactory _db;
  private readonly ValidateShiftOverlapHandler _validateShiftOverlap;
  private readonly CreateShiftHandler _createShiftHandler;
  private readonly UpdateShiftHandler _updateShiftHandler;

  public ShiftDomainService(
    IDbConnectionFactory db,
    ValidateShiftOverlapHandler validateShiftOverlap,
    CreateShiftHandler createShiftHandler,
    UpdateShiftHandler updateShiftHandler)
  {
    _db = db;
    _validateShiftOverlap = validateShiftOverlap;
    _createShiftHandler = createShiftHandler;
    _updateShiftHandler = updateShiftHandler;
  }

  public async Task CreateShift(int scheduleId, CreateShiftRequest request, int currentUserEmployeeId)
  {
    using var connection = _db.CreateConnection();

    var isManager = await connection.ExecuteScalarAsync<int?>(@"
      SELECT 1
      FROM ScheduleManagers
      WHERE ScheduleId = @scheduleId
        AND ManagerId = @managerId
    ", new { scheduleId, managerId = currentUserEmployeeId });

    if (isManager is null)
      throw new ShiftValidationException(
        "Not authorized to manage this schedule.",
        "not_authorized_for_schedule",
        StatusCodes.Status403Forbidden);

    var isAssigned = await connection.ExecuteScalarAsync<int?>(@"
      SELECT 1
      FROM ScheduleEmployees
      WHERE ScheduleId = @scheduleId
        AND EmployeeId = @employeeId
    ", new { scheduleId, employeeId = request.EmployeeId });

    if (isAssigned is null)
      throw new ShiftValidationException(
        "Employee is not assigned to this schedule.",
        "employee_not_assigned_to_schedule");

    await _validateShiftOverlap.EnsureNoOverlap(
      request.EmployeeId,
      request.Start,
      request.DurationHours,
      connection: connection);

    await _createShiftHandler.Handle(
      scheduleId,
      request.EmployeeId,
      request.Start,
      request.DurationHours,
      connection);
  }

  public async Task<bool> UpdateShift(int shiftId, UpdateShiftRequest request, int currentUserEmployeeId)
  {
    using var connection = _db.CreateConnection();

    var shift = await connection.QuerySingleOrDefaultAsync<(int Id, int ScheduleId, int EmployeeId)>(@"
      SELECT Id, ScheduleId, EmployeeId
      FROM Shifts
      WHERE Id = @shiftId
    ", new { shiftId });

    if (shift.Id == 0)
      return false;

    var isManager = await connection.ExecuteScalarAsync<int?>(@"
      SELECT 1
      FROM ScheduleManagers
      WHERE ScheduleId = @scheduleId
        AND ManagerId = @managerId
    ", new
    {
      scheduleId = shift.ScheduleId,
      managerId = currentUserEmployeeId,
    });

    if (isManager is null)
      throw new ShiftValidationException(
        "Not authorized to manage this schedule.",
        "not_authorized_for_schedule",
        StatusCodes.Status403Forbidden);

    await _validateShiftOverlap.EnsureNoOverlap(
      shift.EmployeeId,
      request.Start,
      request.DurationHours,
      shiftId,
      connection);

    return await _updateShiftHandler.Handle(
      shiftId,
      request.Start,
      request.DurationHours,
      connection);
  }
}
