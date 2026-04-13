using Microsoft.AspNetCore.Mvc;
using Scheduler.Api.Features.Auth.Models;
using Scheduler.Api.Features.Auth.Services;

namespace Scheduler.Api.Features.Auth;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
  private readonly AuthDomainService _authDomainService;

  public AuthController(AuthDomainService authDomainService)
  {
    _authDomainService = authDomainService;
  }

  [HttpPost("login")]
  public async Task<IActionResult> Login(LoginRequestV1Model request)
  {
    var token = await _authDomainService.Login(request);

    if (token is null)
      return Unauthorized("Invalid credentials");

    return Ok(new { token });
  }
}
