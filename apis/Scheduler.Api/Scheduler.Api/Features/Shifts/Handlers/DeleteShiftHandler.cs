using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Shifts.Handlers
{
  public class DeleteShiftHandler
  {
    private readonly IDbConnectionFactory _db;

    public DeleteShiftHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task<bool> Handle(int shiftId)
    {
      using var connection = _db.CreateConnection();
      connection.Open();

      var rows = await connection.ExecuteAsync(
        "DELETE FROM Shifts WHERE Id = @shiftId",
        new { shiftId });

      return rows > 0;
    }
  }
}
