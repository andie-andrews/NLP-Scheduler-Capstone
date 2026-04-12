using Dapper;
using Scheduler.Api.Infrastructure.Data;
using System.Data;

namespace Scheduler.Api.Features.Shifts.Handlers;

public class ValidateShiftOverlapHandler
{
  private readonly IDbConnectionFactory _db;

  public ValidateShiftOverlapHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task EnsureNoOverlap(
    int employeeId,
    DateTime start,
    int durationHours,
    int? excludeShiftId = null,
    IDbConnection? connection = null)
  {
    var end = start.AddHours(durationHours);
    var ownsConnection = connection is null;
    connection ??= _db.CreateConnection();

    try
    {
      var overlapping = await connection.QuerySingleOrDefaultAsync<(int Id, int ScheduleId, DateTime Start, int DurationHours)>(@"
        SELECT TOP 1 Id, ScheduleId, Start, DurationHours
        FROM Shifts
        WHERE EmployeeId = @employeeId
          AND (@excludeShiftId IS NULL OR Id <> @excludeShiftId)
          AND Start < @newEnd
          AND DATEADD(hour, DurationHours, Start) > @newStart
        ORDER BY Start ASC
      ", new
      {
        employeeId,
        newStart = start,
        newEnd = end,
        excludeShiftId,
      });

      if (overlapping.Id == 0)
        return;

      var existingEnd = overlapping.Start.AddHours(overlapping.DurationHours);
      var message =
        $"Shift overlaps existing shift (ShiftId {overlapping.Id}) in schedule {overlapping.ScheduleId}: " +
        $"{overlapping.Start:yyyy-MM-dd HH:mm} - {existingEnd:yyyy-MM-dd HH:mm}.";

      throw new ShiftValidationException(message, "overlapping_shift");
    }
    finally
    {
      if (ownsConnection)
        connection.Dispose();
    }
  }
}
