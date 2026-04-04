using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Shifts.Handlers;

public class CreateShiftHandler
{
  private readonly IDbConnectionFactory _db;

  public CreateShiftHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task Handle(int scheduleId, int employeeId, DateTime start, int duration, int currentUserEmployeeId)
  {
    using var connection = _db.CreateConnection();

    var isManager = await connection.ExecuteScalarAsync<int?>(@"
            SELECT 1
            FROM ScheduleManagers
            WHERE ScheduleId = @scheduleId
              AND ManagerId = @managerId
        ", new { scheduleId, managerId = currentUserEmployeeId });

    if (isManager is null)
      throw new Exception("Not authorized to manage this schedule");

    // 👥 Validate employee is on schedule
    var isAssigned = await connection.ExecuteScalarAsync<int?>(@"
            SELECT 1
            FROM ScheduleEmployees
            WHERE ScheduleId = @scheduleId
              AND EmployeeId = @employeeId
        ", new { scheduleId, employeeId });

    if (isAssigned is null)
      throw new Exception("Employee not assigned to schedule");

    // ➕ Insert shift
    await connection.ExecuteAsync(@"
            INSERT INTO Shifts (ScheduleId, EmployeeId, Start, DurationHours)
            VALUES (@scheduleId, @employeeId, @start, @duration)
        ", new
    {
      scheduleId,
      employeeId,
      start,
      duration
    });
  }
}