using Dapper;
using Scheduler.Api.Infrastructure.Data;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Shifts.Handlers;

public class GetScheduleShiftsHandler
{
  private readonly IDbConnectionFactory _db;

  public GetScheduleShiftsHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<IEnumerable<Shift>> Handle(
    int scheduleId, 
    DateTime? weekStart, 
    int? employeeId)
  {
    using var connection = _db.CreateConnection();

    var start = weekStart ?? DateTime.UtcNow.Date;
    var startOfWeek = start.AddDays(-(int)start.DayOfWeek);
    var endOfWeek = startOfWeek.AddDays(7);

    var sql = @"
            SELECT Id, ScheduleId, EmployeeId, Start, DurationHours
            FROM Shifts
            WHERE ScheduleId = @scheduleId
              AND Start >= @startOfWeek
              AND Start < @endOfWeek
        ";

    if (employeeId.HasValue)
    {
        sql += " AND EmployeeId = @employeeId";
    }

    sql += " ORDER BY Start";

    return await connection.QueryAsync<Shift>(sql, new
    {
      scheduleId,
      startOfWeek,
      endOfWeek,
      employeeId
    });
  }
}