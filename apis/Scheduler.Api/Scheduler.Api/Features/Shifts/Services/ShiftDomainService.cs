using Dapper;
using Microsoft.AspNetCore.Http;
using Scheduler.Api.Features.Schedules.Models;
using Scheduler.Api.Features.Shifts.Handlers;
using Scheduler.Api.Features.Shifts.Models;
using Scheduler.Api.Infrastructure.Data;
using System.Data;

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
    if (connection.State != ConnectionState.Open)
      connection.Open();
    using var transaction = connection.BeginTransaction(IsolationLevel.Serializable);

    var isManager = await connection.ExecuteScalarAsync<int?>(@"
      SELECT 1
      FROM ScheduleManagers
      WHERE ScheduleId = @scheduleId
        AND ManagerId = @managerId
    ", new { scheduleId, managerId = currentUserEmployeeId }, transaction: transaction);

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
    ", new { scheduleId, employeeId = request.EmployeeId }, transaction: transaction);

    if (isAssigned is null)
      throw new ShiftValidationException(
        "Employee is not assigned to this schedule.",
        "employee_not_assigned_to_schedule");

    await _validateShiftOverlap.EnsureNoOverlap(
      request.EmployeeId,
      request.Start,
      request.DurationHours,
      connection: connection,
      transaction: transaction);

    await _createShiftHandler.Handle(
      scheduleId,
      request.EmployeeId,
      request.Start,
      request.DurationHours,
      connection,
      transaction);

    transaction.Commit();
  }

  public async Task<bool> UpdateShift(int shiftId, UpdateShiftRequest request, int currentUserEmployeeId)
  {
    var patchRequest = new PatchShiftRequest
    {
      EmployeeId = null,
      Start = request.Start,
      DurationHours = request.DurationHours,
    };
    return await PatchShift(shiftId, patchRequest, currentUserEmployeeId);
  }

  public async Task<bool> PatchShift(int shiftId, PatchShiftRequest request, int currentUserEmployeeId)
  {
    if (request.EmployeeId is null && request.Start is null && request.DurationHours is null)
      throw new ShiftValidationException(
        "Provide at least one field to patch.",
        "empty_patch_request",
        StatusCodes.Status400BadRequest);

    using var connection = _db.CreateConnection();
    if (connection.State != ConnectionState.Open)
      connection.Open();
    using var transaction = connection.BeginTransaction(IsolationLevel.Serializable);

    var shift = await connection.QuerySingleOrDefaultAsync<(int Id, int ScheduleId, int EmployeeId, DateTime Start, int DurationHours)>(@"
      SELECT Id, ScheduleId, EmployeeId, Start, DurationHours
      FROM Shifts
      WHERE Id = @shiftId
    ", new { shiftId }, transaction: transaction);

    if (shift.Id == 0)
    {
      transaction.Commit();
      return false;
    }

    var isManager = await connection.ExecuteScalarAsync<int?>(@"
      SELECT 1
      FROM ScheduleManagers
      WHERE ScheduleId = @scheduleId
        AND ManagerId = @managerId
    ", new
    {
      scheduleId = shift.ScheduleId,
      managerId = currentUserEmployeeId,
    }, transaction: transaction);

    if (isManager is null)
      throw new ShiftValidationException(
        "Not authorized to manage this schedule.",
        "not_authorized_for_schedule",
        StatusCodes.Status403Forbidden);

    var employeeId = request.EmployeeId ?? shift.EmployeeId;
    var start = request.Start ?? shift.Start;
    var durationHours = request.DurationHours ?? shift.DurationHours;

    var isAssigned = await connection.ExecuteScalarAsync<int?>(@"
      SELECT 1
      FROM ScheduleEmployees
      WHERE ScheduleId = @scheduleId
        AND EmployeeId = @employeeId
    ", new { scheduleId = shift.ScheduleId, employeeId }, transaction: transaction);

    if (isAssigned is null)
      throw new ShiftValidationException(
        "Employee is not assigned to this schedule.",
        "employee_not_assigned_to_schedule");

    await _validateShiftOverlap.EnsureNoOverlap(
      employeeId,
      start,
      durationHours,
      shiftId,
      connection,
      transaction);

    var wasUpdated = await _updateShiftHandler.Handle(
      shiftId,
      employeeId,
      start,
      durationHours,
      connection,
      transaction);

    transaction.Commit();
    return wasUpdated;
  }
}
