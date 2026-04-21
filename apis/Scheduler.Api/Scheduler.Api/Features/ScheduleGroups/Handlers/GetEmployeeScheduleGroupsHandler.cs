using Dapper;
using Scheduler.Api.Infrastructure.Data;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.ScheduleGroups.Handlers;

public class GetEmployeeScheduleGroupsHandler
{
  private readonly IDbConnectionFactory _db;

  public GetEmployeeScheduleGroupsHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<IEnumerable<ScheduleGroup>> Handle(int employeeId)
  {
    using var connection = _db.CreateConnection();

    var sql = @"
      SELECT s.Id, s.Name
      FROM ScheduleGroups s
      JOIN ScheduleGroupEmployees se ON se.ScheduleGroupId = s.Id
      WHERE se.EmployeeId = @employeeId
      ORDER BY s.Name";

    return await connection.QueryAsync<ScheduleGroup>(sql, new { employeeId });
  }
}
