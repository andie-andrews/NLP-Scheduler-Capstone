using Dapper;
using Scheduler.Api.Features.Employee.Queries;
using Scheduler.Api.Infrastructure.Data;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Schedules.Handlers;

public class GetSchedulesHandler
{
  private readonly IDbConnectionFactory _db;

  public GetSchedulesHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<IEnumerable<Schedule>> Handle()
  {
    using var connection = _db.CreateConnection();

    var sql = @"
            SELECT Id, Name
            FROM Schedules
            ORDER BY Name 
        ";

    return await connection.QueryAsync<Schedule>(sql);
  }

  public async Task<IEnumerable<Schedule>> Handle(string query)
  {
    using var connection = _db.CreateConnection();

    var sql = @"
SELECT Id, Name
FROM Schedules
WHERE Name LIKE @query
ORDER BY Name 
";

    var parameters = new
    {
      Query = $"%{query.Trim()}%"
    };


    return await connection.QueryAsync<Schedule>(
      sql,
      parameters);
  }
}