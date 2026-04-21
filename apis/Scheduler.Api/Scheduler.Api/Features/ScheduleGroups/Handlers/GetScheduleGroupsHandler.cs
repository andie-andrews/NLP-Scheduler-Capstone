using Dapper;
using Scheduler.Api.Features.Employee.Queries;
using Scheduler.Api.Infrastructure.Data;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.ScheduleGroups.Handlers;

public class GetScheduleGroupsHandler
{
  private readonly IDbConnectionFactory _db;

  public GetScheduleGroupsHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<IEnumerable<ScheduleGroup>> Handle()
  {
    using var connection = _db.CreateConnection();

    var sql = @"
            SELECT Id, Name
            FROM ScheduleGroups
            ORDER BY Name 
        ";

    return await connection.QueryAsync<ScheduleGroup>(sql);
  }

  public async Task<IEnumerable<ScheduleGroup>> Handle(string query)
  {
    using var connection = _db.CreateConnection();

    var sql = @"
SELECT Id, Name
FROM ScheduleGroups
WHERE Name LIKE @query
ORDER BY Name 
";

    var parameters = new
    {
      Query = $"%{query.Trim()}%"
    };


    return await connection.QueryAsync<ScheduleGroup>(
      sql,
      parameters);
  }
}