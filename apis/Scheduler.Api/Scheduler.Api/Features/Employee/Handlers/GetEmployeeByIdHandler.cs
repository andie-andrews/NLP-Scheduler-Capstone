using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Employee.Handlers
{
  public class GetEmployeeByIdHandler
  {
    private readonly IDbConnectionFactory _db;

    public GetEmployeeByIdHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task<Infrastructure.Domain.Models.Employee?> Handle(int id)
    {
      using var connection = _db.CreateConnection();
      var hasEmail = await connection.ExecuteScalarAsync<int>(
        "SELECT CASE WHEN COL_LENGTH('Employees', 'Email') IS NULL THEN 0 ELSE 1 END") == 1;

      var sql = hasEmail
        ? @"
            SELECT Id, FirstName, LastName, Email, RoleId
            FROM Employees
            WHERE Id = @id
        "
        : @"
            SELECT Id, FirstName, LastName, CAST('' AS NVARCHAR(255)) AS Email, RoleId
            FROM Employees
            WHERE Id = @id
        ";

      return await connection.QueryFirstOrDefaultAsync<Infrastructure.Domain.Models.Employee>(sql, new { id });
    }
  }
}
