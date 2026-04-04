using Dapper;
using Scheduler.Api.Infrastructure.Data;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Shifts.Handlers
{
  public class GetEmployeeShiftsHandler
  {
    private readonly IDbConnectionFactory _db;

    public GetEmployeeShiftsHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task<IEnumerable<Shift>> Handle(int employeeId, DateTime? weekStart)
    {
      using var connection = _db.CreateConnection();

      var start = weekStart ?? DateTime.UtcNow.Date;
      var startOfWeek = start.AddDays(-(int)start.DayOfWeek);
      var endOfWeek = startOfWeek.AddDays(7);

      var sql = @"
              SELECT Id, ScheduleId, EmployeeId, Start, DurationHours
              FROM Shifts
              WHERE EmployeeId = @employeeId
                AND Start >= @startOfWeek
                AND Start < @endOfWeek
          ";

      return await connection.QueryAsync<Shift>(sql, new
      {
        employeeId,
        startOfWeek,
        endOfWeek
      });
    }
  }
}
