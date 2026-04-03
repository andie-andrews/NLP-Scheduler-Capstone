using Dapper;

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

    var sql = @"
            SELECT e.Id, e.FirstName, e.LastName, e.RoleId
            FROM Employees e
            JOIN ScheduleEmployees se ON se.EmployeeId = e.Id
            WHERE se.ScheduleId = @scheduleId
        ";

    return await connection.QueryAsync<Infrastructure.Domain.Models.Employee>(sql, new { scheduleId });
  }
}