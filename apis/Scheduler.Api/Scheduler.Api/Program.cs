using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using Scheduler.Api.Features.Auth.Handlers;
using Scheduler.Api.Features.Employee.Handlers;
using Scheduler.Api.Features.Schedules.Handlers;
using Scheduler.Api.Infrastructure.Domain.Services;
using System.Text;
using Scheduler.Api.Features.Health;
using Scheduler.Api.Features.Shifts.Handlers;
using Scheduler.Api.Features.Shifts.Services;
using Scheduler.Api.Features.Schedules.Services;
using Scheduler.Api.Features.Employee.Services;
using Scheduler.Api.Features.Auth.Services;
using Scheduler.Api.Infrastructure.Data;

var builder = WebApplication.CreateBuilder(args);

var jwtIssuer = builder.Configuration["Jwt:Issuer"]
  ?? throw new InvalidOperationException("Missing required configuration value: Jwt:Issuer");
var jwtKey = builder.Configuration["Jwt:Key"]
  ?? throw new InvalidOperationException("Missing required configuration value: Jwt:Key");
var defaultConnectionString = builder.Configuration.GetConnectionString("Default")
  ?? throw new InvalidOperationException("Missing required configuration value: ConnectionStrings:Default");
_ = defaultConnectionString;

var corsAllowedOrigins = builder.Configuration.GetSection("Cors:AllowedOrigins").Get<string[]>() ?? Array.Empty<string>();

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
  options.SwaggerDoc("v1", new OpenApiInfo
  {
    Title = "Scheduler.Api",
    Version = "v1"
  });

  // Add JWT Auth definition
  options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
  {
    Name = "Authorization",
    Type = SecuritySchemeType.Http,
    Scheme = "bearer",
    BearerFormat = "JWT",
    In = ParameterLocation.Header,
    Description = "Enter: Bearer {your JWT token}"
  });

  // 🔐 Apply it globally
  options.AddSecurityRequirement(new OpenApiSecurityRequirement
  {
    {
      new OpenApiSecurityScheme
      {
        Reference = new OpenApiReference
        {
          Type = ReferenceType.SecurityScheme,
          Id = "Bearer"
        }
      },
      new string[] {}
    }
  });
});
builder.Services.AddAuthentication("Bearer")
  .AddJwtBearer("Bearer", options =>
  {
    options.TokenValidationParameters = new TokenValidationParameters
    {
      ValidateIssuer = true,
      ValidateAudience = false,
      ValidateLifetime = true,
      ValidateIssuerSigningKey = true,
      ValidIssuer = jwtIssuer,
      IssuerSigningKey = new SymmetricSecurityKey(
        Encoding.UTF8.GetBytes(jwtKey))
    };
  });

builder.Services.AddAuthorization();
builder.Services.AddCors(options =>
{
  options.AddPolicy("SchedulerFrontend", policy =>
  {
    // In local development, allow the React dev server without requiring additional configuration.
    if (builder.Environment.IsDevelopment())
    {
      policy
        .AllowAnyOrigin()
        .AllowAnyHeader()
        .AllowAnyMethod();
      return;
    }

    if (corsAllowedOrigins.Length == 0)
    {
      policy
        .AllowAnyOrigin()
        .AllowAnyHeader()
        .AllowAnyMethod();
      return;
    }

    policy
      .WithOrigins(corsAllowedOrigins)
      .AllowAnyHeader()
      .AllowAnyMethod();
  });
});
builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Logging.AddDebug();



// Add services to the container.
builder.Services.AddScoped<IDbConnectionFactory, SqlConnectionFactory>();

builder.Services.AddScoped<JwtService>();
builder.Services.AddScoped<HealthHandler>();
builder.Services.AddScoped<GetEmployeeByNameHandler>();
builder.Services.AddScoped<AuthHandler>();
builder.Services.AddScoped<AuthDomainService>();


builder.Services.AddScoped<GetSchedulesHandler>();
builder.Services.AddScoped<GetScheduleEmployeesHandler>();
builder.Services.AddScoped<GetEmployeeSchedulesHandler>();
builder.Services.AddScoped<GetManagerSchedulesHandler>();
builder.Services.AddScoped<GetScheduleShiftsHandler>();
builder.Services.AddScoped<CreateShiftHandler>();
builder.Services.AddScoped<ValidateShiftOverlapHandler>();
builder.Services.AddScoped<CreateScheduleHandler>();
builder.Services.AddScoped<UpdateScheduleHandler>();
builder.Services.AddScoped<DeleteScheduleHandler>();
builder.Services.AddScoped<ScheduleDomainService>();
builder.Services.AddScoped<AddEmployeeToScheduleHandler>();
builder.Services.AddScoped<DeleteEmployeeToScheduleHandler>();
builder.Services.AddScoped<GetEmployeeByIdHandler>();
builder.Services.AddScoped<GetAllEmployeesHandler>();
builder.Services.AddScoped<GetEmployeeByNameHandler>();
builder.Services.AddScoped<GetEmployeeShiftsHandler>();
builder.Services.AddScoped<CreateEmployeeHandler>();
builder.Services.AddScoped<UpdateEmployeeHandler>();
builder.Services.AddScoped<DeleteEmployeeHandler>();
builder.Services.AddScoped<EmployeeDomainService>();
builder.Services.AddScoped<DeleteShiftHandler>();
builder.Services.AddScoped<UpdateShiftHandler>();
builder.Services.AddScoped<ShiftDomainService>();

builder.Services.AddControllers();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

HealthEndpoint.Map(app);

app.UseSwagger();
app.UseSwaggerUI();


app.UseHttpsRedirection();
app.UseCors("SchedulerFrontend");

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();
app.UseExceptionHandler(errorApp =>
{
  errorApp.Run(async context =>
  {
    var feature = context.Features.Get<Microsoft.AspNetCore.Diagnostics.IExceptionHandlerFeature>();
    var logger = context.RequestServices.GetRequiredService<ILogger<Program>>();

    if (feature?.Error != null)
    {
      logger.LogError(feature.Error, "Unhandled exception");
    }

    context.Response.StatusCode = 500;
    context.Response.ContentType = "application/json";

    await context.Response.WriteAsJsonAsync(new
    {
      error = "Internal server error",
      message = feature?.Error?.Message
    });
  });
});

app.Run();
