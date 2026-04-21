using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.ScheduleGroups.Handlers
{
  public class AddEmployeeToScheduleGroupHandler
  {
    private readonly IDbConnectionFactory _db;

    public AddEmployeeToScheduleGroupHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task Handle(int scheduleGroupId, int employeeId)
    {
      using var connection = _db.CreateConnection();

      var exists = await connection.ExecuteScalarAsync<int?>(@"
            SELECT 1 FROM ScheduleGroupEmployees
            WHERE ScheduleGroupId = @scheduleGroupId
              AND EmployeeId = @employeeId
        ", new { scheduleGroupId, employeeId });

      if (exists != null)
        return;

      await connection.ExecuteAsync(@"
            INSERT INTO ScheduleGroupEmployees (ScheduleGroupId, EmployeeId)
            VALUES (@scheduleGroupId, @employeeId)
        ", new { scheduleGroupId, employeeId });
    }
  }
}
