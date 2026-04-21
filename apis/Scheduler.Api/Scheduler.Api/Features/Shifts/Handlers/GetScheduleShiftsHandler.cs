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
    int scheduleGroupId, 
    DateTime? startDate,
    DateTime? endDate,
    int? employeeId)
  {
    using var connection = _db.CreateConnection();

    var today = DateTime.UtcNow.Date;
    var defaultStartOfWeek = today.AddDays(-(int)today.DayOfWeek);
    var effectiveStartDate = startDate?.Date;
    var effectiveEndDate = endDate?.Date;

    if (!effectiveStartDate.HasValue && !effectiveEndDate.HasValue)
    {
      effectiveStartDate = defaultStartOfWeek;
      effectiveEndDate = defaultStartOfWeek.AddDays(6);
    }
    else if (!effectiveStartDate.HasValue && effectiveEndDate.HasValue)
    {
      effectiveStartDate = effectiveEndDate.Value;
    }
    else if (effectiveStartDate.HasValue && !effectiveEndDate.HasValue)
    {
      effectiveEndDate = effectiveStartDate.Value;
    }

    var queryStart = effectiveStartDate!.Value;
    var queryEndExclusive = effectiveEndDate!.Value.AddDays(1);

    var sql = @"
            SELECT Id, ScheduleGroupId, EmployeeId, Start, DurationHours
            FROM Shifts
            WHERE ScheduleGroupId = @scheduleGroupId
              AND Start >= @queryStart
              AND Start < @queryEndExclusive
        ";

    if (employeeId.HasValue)
    {
        sql += " AND EmployeeId = @employeeId";
    }

    sql += " ORDER BY Start";

    return await connection.QueryAsync<Shift>(sql, new
    {
      scheduleGroupId,
      queryStart,
      queryEndExclusive,
      employeeId
    });
  }
}
