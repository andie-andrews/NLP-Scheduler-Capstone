using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Employee.Handlers
{

  public class GetAllEmployeesHandler
  {
    private readonly IDbConnectionFactory _db;

    public GetAllEmployeesHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task<IEnumerable<Infrastructure.Domain.Models.Employee>> Handle()
    {
      using var connection = _db.CreateConnection();
      var hasEmail = await connection.ExecuteScalarAsync<int>(
        "SELECT CASE WHEN COL_LENGTH('Employees', 'Email') IS NULL THEN 0 ELSE 1 END") == 1;

      var sql = hasEmail
        ? @"
            SELECT Id, FirstName, LastName, Email, RoleId
            FROM Employees
            ORDER BY FirstName, LastName
        "
        : @"
            SELECT Id, FirstName, LastName, CAST('' AS NVARCHAR(255)) AS Email, RoleId
            FROM Employees
            ORDER BY FirstName, LastName
        ";

      return await connection.QueryAsync<Infrastructure.Domain.Models.Employee>(sql);
    }
  }
}
