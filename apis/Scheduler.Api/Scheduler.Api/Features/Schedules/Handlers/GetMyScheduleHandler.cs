using Dapper;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Schedules.Handlers;

public class GetMyScheduleHandler
{
  private readonly IDbConnectionFactory _db;

  public GetMyScheduleHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<IEnumerable<Shift>> Handle(int employeeId, DateTime weekStart)
  {
    using var connection = _db.CreateConnection();

    // normalize to start of week (Sunday)
    var startOfWeek = weekStart.AddDays(-(int)weekStart.DayOfWeek);
    var endOfWeek = startOfWeek.AddDays(7);

    var sql = @"
            SELECT 
                Id,
                ScheduleId,
                EmployeeId,
                Start,
                DurationHours
            FROM Shifts
            WHERE EmployeeId = @employeeId
              AND Start >= @startOfWeek
              AND Start < @endOfWeek
            ORDER BY Start
        ";

    return await connection.QueryAsync<Shift>(sql, new
    {
      employeeId,
      startOfWeek,
      endOfWeek
    });
  }
}