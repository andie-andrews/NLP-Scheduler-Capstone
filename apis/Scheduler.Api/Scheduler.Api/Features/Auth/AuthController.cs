  using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Auth.Handlers;
using Scheduler.Api.Features.Auth.Models;
using Scheduler.Api.Infrastructure.Domain.Services;

namespace Scheduler.Api.Features.Auth;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
  private readonly JwtService _jwt;
  private readonly AuthHandler _authHandler;

  public AuthController(JwtService jwt,
    AuthHandler authHandler)
  {
    _jwt = jwt;
    _authHandler = authHandler;
  }

  [HttpPost("login")]
  public async Task<IActionResult> Login(LoginRequestV1Model request)
  {
    var user = await _authHandler.Authenticate(request.Username, request.Password);

    if (user == null)
      return Unauthorized("Invalid credentials");

    var token = _jwt.GenerateToken(user);

    return Ok(new { token }); 
  }
}