using Dapper;
using Scheduler.Api.Infrastructure.Data;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Schedules.Handlers;

public class GetEmployeeSchedulesHandler
{
  private readonly IDbConnectionFactory _db;

  public GetEmployeeSchedulesHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<IEnumerable<Schedule>> Handle(int employeeId)
  {
    using var connection = _db.CreateConnection();

    var sql = @"
      SELECT s.Id, s.Name
      FROM Schedules s
      JOIN ScheduleEmployees se ON se.ScheduleId = s.Id
      WHERE se.EmployeeId = @employeeId
      ORDER BY s.Name";

    return await connection.QueryAsync<Schedule>(sql, new { employeeId });
  }
}
