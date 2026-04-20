using Assistant.Api.Contracts;
using Assistant.Api.Services;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

var origins = (builder.Configuration["ASSISTANT_API_ALLOW_ORIGINS"] ?? "*")
  .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

builder.Services.AddCors(options =>
{
  options.AddPolicy("AssistantApiCors", policy =>
  {
    if (origins.Length == 1 && origins[0] == "*")
    {
      policy.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod();
      return;
    }

    policy.WithOrigins(origins).AllowAnyHeader().AllowAnyMethod();
  });
});

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
  options.SwaggerDoc("v1", new OpenApiInfo
  {
    Title = "Assistant.Api",
    Version = "v1",
  });

  options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
  {
    Name = "Authorization",
    Type = SecuritySchemeType.Http,
    Scheme = "bearer",
    BearerFormat = "JWT",
    In = ParameterLocation.Header,
    Description = "Paste a JWT as: Bearer {token}",
  });

  options.AddSecurityRequirement(new OpenApiSecurityRequirement
  {
    {
      new OpenApiSecurityScheme
      {
        Reference = new OpenApiReference
        {
          Type = ReferenceType.SecurityScheme,
          Id = "Bearer",
        },
      },
      Array.Empty<string>()
    }
  });
});
builder.Services.AddSingleton<OpenApiToolRegistry>();
builder.Services.AddHttpClient<SchedulerApiClient>();
builder.Services.AddHttpClient<OpenAiAssistantOrchestrator>();
builder.Services.AddSingleton<ConversationSessionStore>();
builder.Services.AddSingleton<JwtPayloadDecoder>();

var app = builder.Build();

app.UseSwagger();
app.UseSwaggerUI();
app.UseCors("AssistantApiCors");

app.MapGet("/health", (ConversationSessionStore store) =>
{
  store.CleanupExpired();
  return Results.Ok(new
  {
    status = "ok",
    activeConversations = store.ActiveCount,
    sessionTtlSeconds = store.TtlSeconds,
  });
});

app.MapPost("/api/assistant/chat", async (
  ChatRequest payload,
  HttpRequest request,
  ConversationSessionStore store,
  JwtPayloadDecoder tokenDecoder,
  OpenAiAssistantOrchestrator orchestrator,
  CancellationToken cancellationToken) =>
{
  if (string.IsNullOrWhiteSpace(payload.Message))
  {
    return Results.BadRequest(new { error = "Message is required." });
  }

  try
  {
    var user = tokenDecoder.DecodeFromAuthorizationHeader(request.Headers.Authorization);
    var conversationId = string.IsNullOrWhiteSpace(payload.ConversationId) ? Guid.NewGuid().ToString() : payload.ConversationId;

    var session = store.GetOrCreate(conversationId, user);
    var result = await orchestrator.RunAsync(payload.Message, user, session, cancellationToken);
    store.Update(conversationId, result.Session);

    return Results.Ok(new ChatResponse
    {
      ConversationId = conversationId,
      Response = result.Response,
    });
  }
  catch (UnauthorizedAccessException)
  {
    return Results.Unauthorized();
  }
  catch (Exception ex)
  {
    return Results.Problem(detail: ex.Message, statusCode: 500);
  }
});

app.MapDelete("/api/assistant/chat/{conversationId}", (
  string conversationId,
  HttpRequest request,
  ConversationSessionStore store,
  JwtPayloadDecoder tokenDecoder) =>
{
  tokenDecoder.DecodeFromAuthorizationHeader(request.Headers.Authorization);
  store.Clear(conversationId);
  return Results.Ok(new { status = "cleared" });
});

app.Run();
