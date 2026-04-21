using System.Data;
using Microsoft.Data.SqlClient;

namespace Employee.Api.Infrastructure.Data;

public interface IDbConnectionFactory
{
  IDbConnection CreateConnection();
}

public class SqlConnectionFactory : IDbConnectionFactory
{
  private readonly IConfiguration _config;

  public SqlConnectionFactory(IConfiguration config)
  {
    _config = config;
  }

  public IDbConnection CreateConnection()
  {
    var connectionString = _config.GetConnectionString("Default");
    return new SqlConnection(connectionString);
  }
}
