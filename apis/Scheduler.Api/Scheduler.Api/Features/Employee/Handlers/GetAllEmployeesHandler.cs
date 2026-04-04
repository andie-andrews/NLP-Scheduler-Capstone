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

      var sql = @"
            SELECT Id, FirstName, LastName, RoleId
            FROM Employees
            ORDER BY FirstName, LastName
        ";

      return await connection.QueryAsync<Infrastructure.Domain.Models.Employee>(sql);
    }
  }
}
