using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Schedules.Handlers
{
  public class DeleteEmployeeToScheduleHandler
  {
    private readonly IDbConnectionFactory _db;

    public DeleteEmployeeToScheduleHandler(IDbConnectionFactory db)
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

      if (exists == null)
        return;

      connection.Open();
      using var transaction = connection.BeginTransaction();
      try
      {
        await connection.ExecuteAsync(@"
            DELETE FROM Shifts
            WHERE ScheduleId = @scheduleId
              AND EmployeeId = @employeeId;

            DELETE FROM ScheduleEmployees
            WHERE ScheduleId = @scheduleId
              AND EmployeeId = @employeeId;
        ", new { scheduleId, employeeId }, transaction);
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
