using Dapper;
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
}