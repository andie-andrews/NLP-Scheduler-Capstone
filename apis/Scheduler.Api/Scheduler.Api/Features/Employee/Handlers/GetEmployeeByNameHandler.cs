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
    var hasEmail = await connection.ExecuteScalarAsync<int>(
      "SELECT CASE WHEN COL_LENGTH('Employees', 'Email') IS NULL THEN 0 ELSE 1 END") == 1;

    Console.WriteLine($"FirstName: {query.FirstName}, LastName: {query.LastName}");
    var parameters = new
    {
      FirstName = query.FirstName?.Trim(),
      LastName = query.LastName?.Trim(),
      Query = query.FirstName?.Trim()
    };

    if (!string.IsNullOrWhiteSpace(query.FirstName) && !string.IsNullOrWhiteSpace(query.LastName))
    {
      var fullNameSql = hasEmail
        ? @"
      SELECT 
          Id,
          FirstName,
          LastName,
          Email,
          RoleId
      FROM Employees
      WHERE FirstName LIKE @FirstName + '%'
        AND LastName LIKE @LastName + '%'
      "
        : @"
      SELECT 
          Id,
          FirstName,
          LastName,
          CAST('' AS NVARCHAR(255)) AS Email,
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

    var fallbackSql = hasEmail
      ? @"
    SELECT 
        Id,
        FirstName,
        LastName,
        Email,
        RoleId
    FROM Employees
    WHERE
      (@FirstName IS NOT NULL AND FirstName LIKE @FirstName + '%')
      OR
      (@LastName IS NOT NULL AND LastName LIKE @LastName + '%')
      OR
      (@Query IS NOT NULL AND Email LIKE @Query + '%')
    "
      : @"
    SELECT 
        Id,
        FirstName,
        LastName,
        CAST('' AS NVARCHAR(255)) AS Email,
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
