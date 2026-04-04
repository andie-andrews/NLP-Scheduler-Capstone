using Dapper;
using Scheduler.Api.Infrastructure.Data;

namespace Scheduler.Api.Features.Health;

public class HealthHandler
{
  private readonly IDbConnectionFactory _db;

  public HealthHandler(IDbConnectionFactory db)
  {
    _db = db;
  }

  public async Task<object> Handle()
  {
    try
    {
      using var connection = _db.CreateConnection();

      // simple DB check
      var result = await connection.ExecuteScalarAsync<int>("SELECT 1");

      return new
      {
        status = "Healthy",
        database = result == 1 ? "Up" : "Unknown"
      };
    }
    catch (Exception ex)
    {
      return new
      {
        status = "Unhealthy",
        database = "Down",
        error = ex.Message
      };
    }
  }
}