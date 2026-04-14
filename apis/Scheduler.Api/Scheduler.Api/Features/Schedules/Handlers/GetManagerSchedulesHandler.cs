using Dapper;
using Scheduler.Api.Infrastructure.Data;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Schedules.Handlers;

public class GetManagerSchedulesHandler
{
  private readonly IDbConnectionFactory _db;

  public GetManagerSchedulesHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<IEnumerable<Schedule>> Handle(int managerId)
  {
    using var connection = _db.CreateConnection();

    var sql = @"
      SELECT s.Id, s.Name
      FROM Schedules s
      JOIN ScheduleManagers sm ON sm.ScheduleId = s.Id
      WHERE sm.ManagerId = @managerId
      ORDER BY s.Name";

    return await connection.QueryAsync<Schedule>(sql, new { managerId });
  }
}
