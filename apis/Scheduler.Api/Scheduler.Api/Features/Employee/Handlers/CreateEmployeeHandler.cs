using Dapper;
using Scheduler.Api.Features.Employee.Models;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Employee.Handlers;

public class CreateEmployeeHandler
{
  private readonly IDbConnectionFactory _db;
  public CreateEmployeeHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<int> Handle(CreateEmployeeRequest request)
  {
    using var connection = _db.CreateConnection();
    var sql = @"
            INSERT INTO Employees (FirstName, LastName, Email, RoleId)
            VALUES (@FirstName, @LastName, @Email, @RoleId);
            SELECT CAST(SCOPE_IDENTITY() as int);
        ";

    return await connection.ExecuteScalarAsync<int>(sql, request);
  }
}
