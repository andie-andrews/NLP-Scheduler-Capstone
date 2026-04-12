using Dapper;
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
    int scheduleId,
    int employeeId,
    DateTime start,
    int duration,
    IDbConnection? connection = null)
  {
    var ownsConnection = connection is null;
    connection ??= _db.CreateConnection();

    try
    {
      await connection.ExecuteAsync(@"
        INSERT INTO Shifts (ScheduleId, EmployeeId, Start, DurationHours)
        VALUES (@scheduleId, @employeeId, @start, @duration)
      ", new
      {
        scheduleId,
        employeeId,
        start,
        duration,
      });
    }
    finally
    {
      if (ownsConnection)
        connection.Dispose();
    }
  }
}
