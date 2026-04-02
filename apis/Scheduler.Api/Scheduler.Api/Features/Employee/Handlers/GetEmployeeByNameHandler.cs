using Dapper;
using Scheduler.Api.Features.Employee.Queries;

namespace Scheduler.Api.Features.Employee.Handlers;

public class GetEmployeeByNameHandler
{
  private readonly IDbConnectionFactory _db;

  public GetEmployeeByNameHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<Infrastructure.Domain.Models.Employee?> Handle(EmployeeQueries.GetEmployeeByNameQuery query)
  {
    using var connection = _db.CreateConnection();

    var sql = @"
            SELECT TOP 1
                e.Id,
                e.FirstName,
                e.LastName,
                e.RoleId
            FROM Employees e
            WHERE e.FirstName = @FirstName
              AND e.LastName = @LastName
        ";

    Console.WriteLine($"FirstName: {query.FirstName}, LastName: {query.LastName}");
    var parameters = new
    {
      FirstName = query.FirstName?.Trim(),
      LastName = query.LastName?.Trim()
    };


    return await connection.QueryFirstOrDefaultAsync<Infrastructure.Domain.Models.Employee>(
      sql,
      parameters);
  }
}