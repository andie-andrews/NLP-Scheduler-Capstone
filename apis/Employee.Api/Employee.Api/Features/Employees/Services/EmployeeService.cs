using Dapper;
using Employee.Api.Infrastructure.Data;
using CreateEmployeeRequestModel = Employee.Api.Features.Employees.Models.CreateEmployeeRequest;
using EmployeeModel = Employee.Api.Features.Employees.Models.Employee;
using ScheduleGroupModel = Employee.Api.Features.Employees.Models.ScheduleGroup;
using ShiftModel = Employee.Api.Features.Employees.Models.Shift;
using UpdateEmployeeRequestModel = Employee.Api.Features.Employees.Models.UpdateEmployeeRequest;

namespace Employee.Api.Features.Employees.Services;

public class EmployeeService
{
  private readonly IDbConnectionFactory _db;

  public EmployeeService(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<EmployeeModel?> GetEmployeeById(int employeeId)
  {
    using var connection = _db.CreateConnection();
    var hasEmail = await HasEmailColumn(connection);

    var sql = hasEmail
      ? @"
          SELECT Id, FirstName, LastName, Email, RoleId
          FROM Employees
          WHERE Id = @employeeId
      "
      : @"
          SELECT Id, FirstName, LastName, CAST('' AS NVARCHAR(255)) AS Email, RoleId
          FROM Employees
          WHERE Id = @employeeId
      ";

    return await connection.QueryFirstOrDefaultAsync<EmployeeModel>(sql, new { employeeId });
  }

  public async Task<IEnumerable<EmployeeModel>> GetEmployees(string? query)
  {
    using var connection = _db.CreateConnection();
    var hasEmail = await HasEmailColumn(connection);

    if (string.IsNullOrWhiteSpace(query))
    {
      var allEmployeesSql = hasEmail
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

      return await connection.QueryAsync<EmployeeModel>(allEmployeesSql);
    }

    var parts = query.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    var firstName = parts.Length > 0 ? parts[0].Trim() : null;
    var lastName = parts.Length > 1 ? parts[1].Trim() : null;

    var parameters = new
    {
      FirstName = firstName,
      LastName = lastName,
      Query = firstName
    };

    if (!string.IsNullOrWhiteSpace(firstName) && !string.IsNullOrWhiteSpace(lastName))
    {
      var fullNameSql = hasEmail
        ? @"
            SELECT Id, FirstName, LastName, Email, RoleId
            FROM Employees
            WHERE FirstName LIKE @FirstName + '%'
              AND LastName LIKE @LastName + '%'
        "
        : @"
            SELECT Id, FirstName, LastName, CAST('' AS NVARCHAR(255)) AS Email, RoleId
            FROM Employees
            WHERE FirstName LIKE @FirstName + '%'
              AND LastName LIKE @LastName + '%'
        ";

      var fullNameMatches = (await connection.QueryAsync<EmployeeModel>(fullNameSql, parameters)).ToList();
      if (fullNameMatches.Count > 0)
      {
        return fullNameMatches;
      }
    }

    var fallbackSql = hasEmail
      ? @"
          SELECT Id, FirstName, LastName, Email, RoleId
          FROM Employees
          WHERE
            (@FirstName IS NOT NULL AND FirstName LIKE @FirstName + '%')
            OR (@LastName IS NOT NULL AND LastName LIKE @LastName + '%')
            OR (@Query IS NOT NULL AND Email LIKE @Query + '%')
      "
      : @"
          SELECT Id, FirstName, LastName, CAST('' AS NVARCHAR(255)) AS Email, RoleId
          FROM Employees
          WHERE
            (@FirstName IS NOT NULL AND FirstName LIKE @FirstName + '%')
            OR (@LastName IS NOT NULL AND LastName LIKE @LastName + '%')
      ";

    return await connection.QueryAsync<EmployeeModel>(fallbackSql, parameters);
  }

  public async Task<int> CreateEmployee(CreateEmployeeRequestModel request)
  {
    using var connection = _db.CreateConnection();
    var hasEmail = await HasEmailColumn(connection);

    var sql = hasEmail
      ? @"
          INSERT INTO Employees (FirstName, LastName, Email, RoleId)
          VALUES (@FirstName, @LastName, @Email, @RoleId);
          SELECT CAST(SCOPE_IDENTITY() as int);
      "
      : @"
          INSERT INTO Employees (FirstName, LastName, RoleId)
          VALUES (@FirstName, @LastName, @RoleId);
          SELECT CAST(SCOPE_IDENTITY() as int);
      ";

    return await connection.ExecuteScalarAsync<int>(sql, request);
  }

  public async Task<bool> UpdateEmployee(int employeeId, UpdateEmployeeRequestModel request)
  {
    using var connection = _db.CreateConnection();
    var hasEmail = await HasEmailColumn(connection);

    var sql = hasEmail
      ? @"
          UPDATE Employees
          SET FirstName = @FirstName,
              LastName = @LastName,
              Email = @Email,
              RoleId = @RoleId
          WHERE Id = @Id
      "
      : @"
          UPDATE Employees
          SET FirstName = @FirstName,
              LastName = @LastName,
              RoleId = @RoleId
          WHERE Id = @Id
      ";

    var rows = await connection.ExecuteAsync(sql, new
    {
      request.FirstName,
      request.LastName,
      request.Email,
      request.RoleId,
      Id = employeeId
    });

    return rows > 0;
  }

  public async Task<bool> DeleteEmployee(int employeeId)
  {
    using var connection = _db.CreateConnection();

    var param = new { Id = employeeId };
    connection.Open();
    using var transaction = connection.BeginTransaction();

    try
    {
      await connection.ExecuteAsync("DELETE FROM Shifts WHERE EmployeeId = @Id", param, transaction);
      await connection.ExecuteAsync("DELETE FROM ScheduleGroupEmployees WHERE EmployeeId = @Id", param, transaction);
      await connection.ExecuteAsync("DELETE FROM ScheduleGroupManagers WHERE ManagerId = @Id", param, transaction);

      var rows = await connection.ExecuteAsync("DELETE FROM Employees WHERE Id = @Id", param, transaction);
      transaction.Commit();

      return rows > 0;
    }
    catch
    {
      transaction.Rollback();
      throw;
    }
  }

  public async Task<IEnumerable<ShiftModel>> GetEmployeeShifts(int employeeId, DateTime? startDate, DateTime? endDate)
  {
    using var connection = _db.CreateConnection();

    var today = DateTime.UtcNow.Date;
    var defaultStartOfWeek = today.AddDays(-(int)today.DayOfWeek);
    var effectiveStartDate = startDate?.Date;
    var effectiveEndDate = endDate?.Date;

    if (!effectiveStartDate.HasValue && !effectiveEndDate.HasValue)
    {
      effectiveStartDate = defaultStartOfWeek;
      effectiveEndDate = defaultStartOfWeek.AddDays(6);
    }
    else if (!effectiveStartDate.HasValue && effectiveEndDate.HasValue)
    {
      effectiveStartDate = effectiveEndDate.Value;
    }
    else if (effectiveStartDate.HasValue && !effectiveEndDate.HasValue)
    {
      effectiveEndDate = effectiveStartDate.Value;
    }

    var queryStart = effectiveStartDate!.Value;
    var queryEndExclusive = effectiveEndDate!.Value.AddDays(1);

    var sql = @"
        SELECT Id, ScheduleGroupId, EmployeeId, Start, DurationHours
        FROM Shifts
        WHERE EmployeeId = @employeeId
          AND Start >= @queryStart
          AND Start < @queryEndExclusive
    ";

    return await connection.QueryAsync<ShiftModel>(sql, new
    {
      employeeId,
      queryStart,
      queryEndExclusive
    });
  }

  public async Task<IEnumerable<ScheduleGroupModel>> GetEmployeeScheduleGroups(int employeeId)
  {
    using var connection = _db.CreateConnection();

    var sql = @"
      SELECT s.Id, s.Name
      FROM ScheduleGroups s
      JOIN ScheduleGroupEmployees se ON se.ScheduleGroupId = s.Id
      WHERE se.EmployeeId = @employeeId
      ORDER BY s.Name";

    return await connection.QueryAsync<ScheduleGroupModel>(sql, new { employeeId });
  }

  private static async Task<bool> HasEmailColumn(System.Data.IDbConnection connection)
  {
    return await connection.ExecuteScalarAsync<int>(
      "SELECT CASE WHEN COL_LENGTH('Employees', 'Email') IS NULL THEN 0 ELSE 1 END") == 1;
  }
}
