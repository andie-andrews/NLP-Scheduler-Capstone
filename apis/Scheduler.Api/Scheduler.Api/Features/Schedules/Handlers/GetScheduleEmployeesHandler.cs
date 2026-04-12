using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Schedules.Handlers;

public class GetScheduleEmployeesHandler
{
  private readonly IDbConnectionFactory _db;

  public GetScheduleEmployeesHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<IEnumerable<Infrastructure.Domain.Models.Employee>> Handle(int scheduleId)
  {
    using var connection = _db.CreateConnection();
    var hasEmail = await connection.ExecuteScalarAsync<int>(
      "SELECT CASE WHEN COL_LENGTH('Employees', 'Email') IS NULL THEN 0 ELSE 1 END") == 1;

    var sql = hasEmail
      ? @"
            SELECT e.Id, e.FirstName, e.LastName, e.Email, e.RoleId
            FROM Employees e
            JOIN ScheduleEmployees se ON se.EmployeeId = e.Id
            WHERE se.ScheduleId = @scheduleId
        "
      : @"
            SELECT e.Id, e.FirstName, e.LastName, CAST('' AS NVARCHAR(255)) AS Email, e.RoleId
            FROM Employees e
            JOIN ScheduleEmployees se ON se.EmployeeId = e.Id
            WHERE se.ScheduleId = @scheduleId
        ";

    return await connection.QueryAsync<Infrastructure.Domain.Models.Employee>(sql, new { scheduleId });
  }
}
