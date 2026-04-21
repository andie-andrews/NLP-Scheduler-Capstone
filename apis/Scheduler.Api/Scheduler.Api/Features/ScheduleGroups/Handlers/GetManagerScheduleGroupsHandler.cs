using Dapper;
using Scheduler.Api.Infrastructure.Data;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.ScheduleGroups.Handlers;

public class GetManagerScheduleGroupsHandler
{
  private readonly IDbConnectionFactory _db;

  public GetManagerScheduleGroupsHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<IEnumerable<ScheduleGroup>> Handle(int managerId)
  {
    using var connection = _db.CreateConnection();

    var sql = @"
      SELECT s.Id, s.Name
      FROM ScheduleGroups s
      JOIN ScheduleGroupManagers sm ON sm.ScheduleGroupId = s.Id
      WHERE sm.ManagerId = @managerId
      ORDER BY s.Name";

    return await connection.QueryAsync<ScheduleGroup>(sql, new { managerId });
  }
}
