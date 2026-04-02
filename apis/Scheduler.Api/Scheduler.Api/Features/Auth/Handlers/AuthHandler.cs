using Dapper;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Auth.Handlers
{
  public class AuthHandler
  {
    private readonly IDbConnectionFactory _db;

    public AuthHandler(IDbConnectionFactory db)
    {
      _db = db;
    }

    public async Task<User?> Authenticate(string username, string password)
    {
      using var connection = _db.CreateConnection();

      var sql = @"
        SELECT 
            u.Id,
            u.Username,
            u.Password,
            u.Role,
            u.EmployeeId,
            ee.FirstName,
            ee.LastName
        FROM Users u
        INNER JOIN Employees ee ON u.EmployeeId = ee.Id
        WHERE u.Username = @Username
          AND u.Password = @Password
    ";

      return await connection.QueryFirstOrDefaultAsync<User>(
        sql,
        new { Username = username, Password = password });
    }
  }
}
