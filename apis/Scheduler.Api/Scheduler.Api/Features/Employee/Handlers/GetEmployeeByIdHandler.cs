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

      var sql = @"
            SELECT Id, FirstName, LastName, RoleId
            FROM Employees
            WHERE Id = @id
        ";

      return await connection.QueryFirstOrDefaultAsync<Infrastructure.Domain.Models.Employee>(sql, new { id });
    }
  }
}
