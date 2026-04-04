using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Schedules.Handlers
{
  public class CreateScheduleHandler
  {
    private readonly IDbConnectionFactory _db;

    public CreateScheduleHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task<int> Handle(string name)
    {
      using var connection = _db.CreateConnection();

      var sql = @"
            INSERT INTO Schedules (Name)
            VALUES (@name);

            SELECT CAST(SCOPE_IDENTITY() as int);
        ";

      return await connection.ExecuteScalarAsync<int>(sql, new { name });
    }
  }
}
