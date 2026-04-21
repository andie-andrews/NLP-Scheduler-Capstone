using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.ScheduleGroups.Handlers
{
  public class UpdateScheduleGroupHandler
  {
    private readonly IDbConnectionFactory _db;

    public UpdateScheduleGroupHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task Handle(int id, string name)
    {
      using var connection = _db.CreateConnection();

      var sql = @"
            UPDATE ScheduleGroups
            SET Name = @name
            WHERE Id = @id
        ";

      await connection.ExecuteAsync(sql, new { id, name });
    }
  }
}
