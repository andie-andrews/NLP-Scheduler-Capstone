using Dapper;
namespace Scheduler.Api.Features.Schedules.Handlers
{
  public class UpdateScheduleHandler
  {
    private readonly IDbConnectionFactory _db;

    public UpdateScheduleHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task Handle(int id, string name)
    {
      using var connection = _db.CreateConnection();

      var sql = @"
            UPDATE Schedules
            SET Name = @name
            WHERE Id = @id
        ";

      await connection.ExecuteAsync(sql, new { id, name });
    }
  }
}
