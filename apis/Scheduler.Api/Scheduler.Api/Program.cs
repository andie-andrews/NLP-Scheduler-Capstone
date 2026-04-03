using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using Scheduler.Api.Features.Auth.Handlers;
using Scheduler.Api.Features.Employee.Handlers;
using Scheduler.Api.Features.Schedules.Handlers;
using Scheduler.Api.Infrastructure.Domain.Services;
using System.Text;

var builder = WebApplication.CreateBuilder(args);
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
      ValidIssuer = builder.Configuration["Jwt:Issuer"],
      IssuerSigningKey = new SymmetricSecurityKey(
        Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]))
    };
  });

builder.Services.AddAuthorization();

// Add services to the container.
builder.Services.AddScoped<IDbConnectionFactory, SqlConnectionFactory>();

builder.Services.AddScoped<JwtService>();
builder.Services.AddScoped<HealthHandler>();
builder.Services.AddScoped<GetEmployeeByNameHandler>();
builder.Services.AddScoped<AuthHandler>();


builder.Services.AddScoped<GetMyScheduleHandler>();
builder.Services.AddScoped<GetSchedulesHandler>();
builder.Services.AddScoped<GetScheduleEmployeesHandler>();
builder.Services.AddScoped<GetScheduleShiftsHandler>();
builder.Services.AddScoped<CreateShiftHandler>();

builder.Services.AddControllers();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

HealthEndpoint.Map(app);

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();


app.Run();
