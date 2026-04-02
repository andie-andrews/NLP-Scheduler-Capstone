using Microsoft.AspNetCore.Mvc;

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