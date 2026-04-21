using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.ScheduleGroups.Handlers
{
  public class DeleteEmployeeFromScheduleGroupHandler
  {
    private readonly IDbConnectionFactory _db;

    public DeleteEmployeeFromScheduleGroupHandler(IDbConnectionFactory db)
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

      if (exists == null)
        return;

      connection.Open();
      using var transaction = connection.BeginTransaction();
      try
      {
        await connection.ExecuteAsync(@"
            DELETE FROM Shifts
            WHERE ScheduleGroupId = @scheduleGroupId
              AND EmployeeId = @employeeId;

            DELETE FROM ScheduleGroupEmployees
            WHERE ScheduleGroupId = @scheduleGroupId
              AND EmployeeId = @employeeId;
        ", new { scheduleGroupId, employeeId }, transaction);
        transaction.Commit();
      }
      catch
      {
        transaction.Rollback();
        throw;
      }
    }
  }
}
