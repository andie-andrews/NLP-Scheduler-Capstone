using Scheduler.Api.Features.Auth.Handlers;
using Scheduler.Api.Features.Auth.Models;
using Scheduler.Api.Infrastructure.Domain.Services;

namespace Scheduler.Api.Features.Auth.Services;

public class AuthDomainService
{
  private readonly AuthHandler _authHandler;
  private readonly JwtService _jwtService;

  public AuthDomainService(AuthHandler authHandler, JwtService jwtService)
  {
    _authHandler = authHandler;
    _jwtService = jwtService;
  }

  public async Task<string?> Login(LoginRequestV1Model request)
  {
    var user = await _authHandler.Authenticate(request.Username, request.Password);
    if (user is null)
      return null;

    return _jwtService.GenerateToken(user);
  }
}
