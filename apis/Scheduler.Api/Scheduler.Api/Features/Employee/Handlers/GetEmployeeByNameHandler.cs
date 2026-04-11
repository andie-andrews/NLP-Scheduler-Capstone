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

    Console.WriteLine($"FirstName: {query.FirstName}, LastName: {query.LastName}");
    var parameters = new
    {
      FirstName = query.FirstName?.Trim(),
      LastName = query.LastName?.Trim()
    };

    if (!string.IsNullOrWhiteSpace(query.FirstName) && !string.IsNullOrWhiteSpace(query.LastName))
    {
      var fullNameSql = @"
      SELECT 
          Id,
          FirstName,
          LastName,
          RoleId
      FROM Employees
      WHERE FirstName LIKE @FirstName + '%'
        AND LastName LIKE @LastName + '%'
      ";

      var fullNameMatches = (await connection.QueryAsync<Infrastructure.Domain.Models.Employee>(
        fullNameSql,
        parameters)).ToList();

      if (fullNameMatches.Count > 0)
        return fullNameMatches;
    }

    var fallbackSql = @"
    SELECT 
        Id,
        FirstName,
        LastName,
        RoleId
    FROM Employees
    WHERE
      (@FirstName IS NOT NULL AND FirstName LIKE @FirstName + '%')
      OR
      (@LastName IS NOT NULL AND LastName LIKE @LastName + '%')
    ";

    return await connection.QueryAsync<Infrastructure.Domain.Models.Employee>(
      fallbackSql,
      parameters);
  }
}
