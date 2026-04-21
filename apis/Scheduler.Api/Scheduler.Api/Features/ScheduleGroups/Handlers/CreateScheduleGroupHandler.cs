using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.ScheduleGroups.Handlers
{
  public class CreateScheduleGroupHandler
  {
    private readonly IDbConnectionFactory _db;

    public CreateScheduleGroupHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task<int> Handle(string name, int managerId)
    {
      using var connection = _db.CreateConnection();

      var sql = @"
            INSERT INTO ScheduleGroups (Name)
            VALUES (@name);

            DECLARE @scheduleGroupId INT = CAST(SCOPE_IDENTITY() as int);

            INSERT INTO ScheduleGroupManagers (ScheduleGroupId, ManagerId)
            VALUES (@scheduleGroupId, @managerId);

            SELECT @scheduleGroupId;
        ";

      return await connection.ExecuteScalarAsync<int>(sql, new { name, managerId });
    }
  }
}
