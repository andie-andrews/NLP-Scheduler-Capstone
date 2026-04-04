using Microsoft.AspNetCore.Mvc;

namespace Scheduler.Api.Features.Health;

public static class HealthEndpoint
{
  public static void Map(WebApplication app)
  {
    app.MapGet("/api/health", async ([FromServices] HealthHandler handler) =>
    {
      var result = await handler.Handle();
      return Results.Ok(result);
    });
  }
}