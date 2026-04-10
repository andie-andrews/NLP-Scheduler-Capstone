using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Shifts.Handlers;

public class UpdateShiftHandler
{
  private readonly IDbConnectionFactory _db;

  public UpdateShiftHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<bool> Handle(int shiftId, DateTime start, int durationHours, int currentUserEmployeeId)
  {
    using var connection = _db.CreateConnection();

    var shift = await connection.QuerySingleOrDefaultAsync<(int Id, int ScheduleId)>(@"
      SELECT Id, ScheduleId
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
      managerId = currentUserEmployeeId
    });

    if (isManager is null)
      throw new Exception("Not authorized to manage this schedule");

    var rows = await connection.ExecuteAsync(@"
      UPDATE Shifts
      SET Start = @start,
          DurationHours = @durationHours
      WHERE Id = @shiftId
    ", new
    {
      shiftId,
      start,
      durationHours
    });

    return rows > 0;
  }
}
