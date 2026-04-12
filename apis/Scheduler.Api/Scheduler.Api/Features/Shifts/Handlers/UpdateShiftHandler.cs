using Dapper;
using Scheduler.Api.Features.Shifts;
using Scheduler.Api.Infrastructure.Data;
using System.Data;

namespace Scheduler.Api.Features.Shifts.Handlers;

public class UpdateShiftHandler
{
  private readonly IDbConnectionFactory _db;

  public UpdateShiftHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<bool> Handle(
    int shiftId,
    DateTime start,
    int durationHours,
    IDbConnection? connection = null)
  {
    var ownsConnection = connection is null;
    connection ??= _db.CreateConnection();

    try
    {
      var rows = await connection.ExecuteAsync(@"
        UPDATE Shifts
        SET Start = @start,
            DurationHours = @durationHours
        WHERE Id = @shiftId
          AND NOT EXISTS (
            SELECT 1
            FROM Shifts
            WHERE EmployeeId = (
              SELECT EmployeeId
              FROM Shifts
              WHERE Id = @shiftId
            )
              AND Id <> @shiftId
              AND Start < DATEADD(hour, @durationHours, @start)
              AND DATEADD(hour, DurationHours, Start) > @start
          )
      ", new
      {
        shiftId,
        start,
        durationHours,
      });

      if (rows == 0)
      {
        var shiftExists = await connection.ExecuteScalarAsync<int?>(@"
          SELECT 1
          FROM Shifts
          WHERE Id = @shiftId
        ", new { shiftId });

        if (shiftExists is not null)
          throw new ShiftValidationException(
            "Shift overlaps an existing shift for this employee.",
            "overlapping_shift");
      }

      return rows > 0;
    }
    finally
    {
      if (ownsConnection)
        connection.Dispose();
    }
  }
}
