using Dapper;
using Scheduler.Api.Features.Employee.Models;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Employee.Handlers;

public class UpdateEmployeeHandler
{
  private readonly IDbConnectionFactory _db;

  public UpdateEmployeeHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<bool> Handle(int employeeId, UpdateEmployeeRequest request)
  {
    using var connection = _db.CreateConnection();

    var sql = @"
            UPDATE Employees
            SET FirstName = @FirstName,
                LastName = @LastName,
                RoleId = @RoleId
            WHERE Id = @Id
        ";

    var rows = await connection.ExecuteAsync(sql, new { request.FirstName, request.LastName, request.RoleId, Id = employeeId });
    return rows > 0;
  }
}