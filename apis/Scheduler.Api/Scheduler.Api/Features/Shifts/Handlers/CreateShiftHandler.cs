using Dapper;
using Scheduler.Api.Features.Shifts;
using Scheduler.Api.Infrastructure.Data;
using System.Data;

namespace Scheduler.Api.Features.Shifts.Handlers;

public class CreateShiftHandler
{
  private readonly IDbConnectionFactory _db;

  public CreateShiftHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task Handle(
    int scheduleGroupId,
    int employeeId,
    DateTime start,
    int duration,
    IDbConnection? connection = null,
    IDbTransaction? transaction = null)
  {
    var ownsConnection = connection is null;
    connection ??= _db.CreateConnection();

    try
    {
      var rows = await connection.ExecuteAsync(@"
        INSERT INTO Shifts (ScheduleGroupId, EmployeeId, Start, DurationHours)
        SELECT @scheduleGroupId, @employeeId, @start, @duration
        WHERE NOT EXISTS (
          SELECT 1
          FROM Shifts WITH (UPDLOCK, HOLDLOCK)
          WHERE EmployeeId = @employeeId
            AND Start < DATEADD(hour, @duration, @start)
            AND DATEADD(hour, DurationHours, Start) > @start
        )
      ", new
      {
        scheduleGroupId,
        employeeId,
        start,
        duration,
      }, transaction: transaction);

      if (rows == 0)
        throw new ShiftValidationException(
          "Shift overlaps an existing shift for this employee.",
          "overlapping_shift");
    }
    finally
    {
      if (ownsConnection)
        connection.Dispose();
    }
  }
}
