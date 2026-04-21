using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.ScheduleGroups.Handlers;

public class GetScheduleGroupEmployeesHandler
{
  private readonly IDbConnectionFactory _db;

  public GetScheduleGroupEmployeesHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<IEnumerable<Infrastructure.Domain.Models.Employee>> Handle(int scheduleGroupId)
  {
    using var connection = _db.CreateConnection();
    var hasEmail = await connection.ExecuteScalarAsync<int>(
      "SELECT CASE WHEN COL_LENGTH('Employees', 'Email') IS NULL THEN 0 ELSE 1 END") == 1;

    var sql = hasEmail
      ? @"
            SELECT e.Id, e.FirstName, e.LastName, e.Email, e.RoleId
            FROM Employees e
            JOIN ScheduleGroupEmployees se ON se.EmployeeId = e.Id
            WHERE se.ScheduleGroupId = @scheduleGroupId
        "
      : @"
            SELECT e.Id, e.FirstName, e.LastName, CAST('' AS NVARCHAR(255)) AS Email, e.RoleId
            FROM Employees e
            JOIN ScheduleGroupEmployees se ON se.EmployeeId = e.Id
            WHERE se.ScheduleGroupId = @scheduleGroupId
        ";

    return await connection.QueryAsync<Infrastructure.Domain.Models.Employee>(sql, new { scheduleGroupId });
  }
}
