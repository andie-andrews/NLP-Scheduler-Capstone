using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Employee.Handlers;

public class DeleteEmployeeHandler
{
  private readonly IDbConnectionFactory _db;

  public DeleteEmployeeHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<bool> Handle(int employeeId)
  {
    using var connection = _db.CreateConnection();

    var param = new { Id = employeeId };
    connection.Open();
    using var transaction = connection.BeginTransaction();
    try
    {
      // Delete shifts for this employee
      await connection.ExecuteAsync(
        "DELETE FROM Shifts WHERE EmployeeId = @Id",
      param, transaction);

      // Delete schedule associations for this employee
      await connection.ExecuteAsync(
        "DELETE FROM ScheduleGroupEmployees WHERE EmployeeId = @Id",
        param, transaction);

      // Delete schedule associations for this employee
      await connection.ExecuteAsync(
        "DELETE FROM ScheduleGroupManagers WHERE ManagerId = @Id",
        param, transaction);


      // Delete the employee
      var rows = await connection.ExecuteAsync(
        "DELETE FROM Employees WHERE Id = @Id",
        param, transaction);

      transaction.Commit();
      return rows > 0;
    }
    catch
    {
      transaction.Rollback();
      throw;
    }
  }
}