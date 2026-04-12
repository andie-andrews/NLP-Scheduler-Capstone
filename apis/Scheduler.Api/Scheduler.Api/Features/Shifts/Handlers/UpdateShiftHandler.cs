using Dapper;
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
      ", new
      {
        shiftId,
        start,
        durationHours,
      });

      return rows > 0;
    }
    finally
    {
      if (ownsConnection)
        connection.Dispose();
    }
  }
}
