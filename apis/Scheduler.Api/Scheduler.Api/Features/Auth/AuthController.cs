using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Auth.Data;
using Scheduler.Api.Features.Auth.Models;
using Scheduler.Api.Infrastructure.Domain.Services;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
  private readonly JwtService _jwt;

  public AuthController(JwtService jwt)
  {
    _jwt = jwt;
  }

  [HttpPost("login")]
  public IActionResult Login(LoginRequestV1Model request)
  {
    // fake user store (for now)
    var user = FakeUsers.Users
      .FirstOrDefault(u =>
        u.Username == request.Username &&
        u.Password == request.Password);

    if (user == null)
      return Unauthorized();

    var token = _jwt.GenerateToken(user);

    return Ok(new { token });
  }
}