using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.ScheduleGroups.Handlers
{
  public class DeleteScheduleGroupHandler
  {
    private readonly IDbConnectionFactory _db;

    public DeleteScheduleGroupHandler(IDbConnectionFactory db)
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
          "DELETE FROM Shifts WHERE ScheduleGroupId = @id",
          new { id }, transaction);

        await connection.ExecuteAsync(
          "DELETE FROM ScheduleGroupEmployees WHERE ScheduleGroupId = @id",
          new { id }, transaction);

        await connection.ExecuteAsync(
          "DELETE FROM ScheduleGroupManagers WHERE ScheduleGroupId = @id",
          new { id }, transaction);

        await connection.ExecuteAsync(
          "DELETE FROM ScheduleGroups WHERE Id = @id",
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
