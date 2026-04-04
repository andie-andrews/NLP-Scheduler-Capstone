using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Schedules.Handlers
{
  public class DeleteScheduleHandler
  {
    private readonly IDbConnectionFactory _db;

    public DeleteScheduleHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task Handle(int id)
    {
      using var connection = _db.CreateConnection();
      connection.Open();
      using var transaction = connection.BeginTransaction();
      {

      }
      try
      {
        await connection.ExecuteAsync(
          "DELETE FROM Shifts WHERE ScheduleId = @id",
          new { id }, transaction);

        await connection.ExecuteAsync(
          "DELETE FROM ScheduleEmployees WHERE ScheduleId = @id",
          new { id }, transaction);

        await connection.ExecuteAsync(
          "DELETE FROM ScheduleManagers WHERE ScheduleId = @id",
          new { id }, transaction);

        await connection.ExecuteAsync(
          "DELETE FROM Schedules WHERE Id = @id",
          new { id }, transaction);

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
