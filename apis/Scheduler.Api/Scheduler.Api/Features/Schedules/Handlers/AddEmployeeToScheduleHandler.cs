using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Schedules.Handlers
{
  public class AddEmployeeToScheduleHandler
  {
    private readonly IDbConnectionFactory _db;

    public AddEmployeeToScheduleHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task Handle(int scheduleId, int employeeId)
    {
      using var connection = _db.CreateConnection();

      var exists = await connection.ExecuteScalarAsync<int?>(@"
            SELECT 1 FROM ScheduleEmployees
            WHERE ScheduleId = @scheduleId
              AND EmployeeId = @employeeId
        ", new { scheduleId, employeeId });

      if (exists != null)
        return;

      await connection.ExecuteAsync(@"
            INSERT INTO ScheduleEmployees (ScheduleId, EmployeeId)
            VALUES (@scheduleId, @employeeId)
        ", new { scheduleId, employeeId });
    }
  }
}
