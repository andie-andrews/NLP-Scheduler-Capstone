using Dapper;
using Scheduler.Api.Features.Employee.Queries;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Employee.Handlers;

public class GetEmployeeByNameHandler
{
  private readonly IDbConnectionFactory _db;

  public GetEmployeeByNameHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<IEnumerable<Infrastructure.Domain.Models.Employee>> Handle(EmployeeQueries.GetEmployeeByNameQuery query)
  {
    using var connection = _db.CreateConnection();

    var sql = @"
    SELECT 
        Id,
        FirstName,
        LastName,
        RoleId
    FROM Employees
    WHERE
      (
        @IsFullNameQuery = 1
        AND FirstName LIKE @FirstName + '%'
        AND LastName LIKE @LastName + '%'
      )
      OR
      (
        @IsFullNameQuery = 0
        AND (
          (@FirstName IS NOT NULL AND FirstName LIKE @FirstName + '%')
          OR
          (@LastName IS NOT NULL AND LastName LIKE @LastName + '%')
        )
      )
";

    Console.WriteLine($"FirstName: {query.FirstName}, LastName: {query.LastName}");
    var parameters = new
    {
      FirstName = query.FirstName?.Trim(),
      LastName = query.LastName?.Trim(),
      query.IsFullNameQuery
    };


    return await connection.QueryAsync<Infrastructure.Domain.Models.Employee>(
      sql,
      parameters);
  }
}
