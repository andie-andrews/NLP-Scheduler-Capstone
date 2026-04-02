using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.IdentityModel.Tokens;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Infrastructure.Domain.Services
{
  public class JwtService
  {
    private readonly IConfiguration _config;

    public JwtService(IConfiguration config)
    {
      _config = config;
    }

    public string GenerateToken(User user)
    {
      var claims = new List<Claim>
      {
        new Claim("employeeId", user.EmployeeId.ToString()),
        new Claim("firstName", user.FirstName),
        new Claim("lastName", user.LastName),
        new Claim("fullName", $"{user.FirstName} {user.LastName}"),
        new Claim("role", user.Role.ToString())
      };

      var key = new SymmetricSecurityKey(
        Encoding.UTF8.GetBytes(_config["Jwt:Key"]));

      var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

      var token = new JwtSecurityToken(
        issuer: _config["Jwt:Issuer"],
        claims: claims,
        expires: DateTime.UtcNow.AddHours(2),
        signingCredentials: creds);

      return new JwtSecurityTokenHandler().WriteToken(token);
    }
  }
}
