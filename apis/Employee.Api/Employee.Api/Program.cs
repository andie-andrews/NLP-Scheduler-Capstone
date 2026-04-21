using Employee.Api.Features.Employees.Services;
using Employee.Api.Infrastructure.Data;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

var jwtIssuer = builder.Configuration["Jwt:Issuer"]
  ?? throw new InvalidOperationException("Missing required configuration value: Jwt:Issuer");
var jwtKey = builder.Configuration["Jwt:Key"]
  ?? throw new InvalidOperationException("Missing required configuration value: Jwt:Key");
_ = builder.Configuration.GetConnectionString("Default")
  ?? throw new InvalidOperationException("Missing required configuration value: ConnectionStrings:Default");

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
  options.SwaggerDoc("v1", new OpenApiInfo
  {
    Title = "Employee.Api",
    Version = "v1"
  });

  options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
  {
    Name = "Authorization",
    Type = SecuritySchemeType.Http,
    Scheme = "bearer",
    BearerFormat = "JWT",
    In = ParameterLocation.Header,
    Description = "Enter: Bearer {your JWT token}"
  });

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
      Array.Empty<string>()
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
      IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey))
    };
  });

builder.Services.AddAuthorization();
builder.Services.AddScoped<IDbConnectionFactory, SqlConnectionFactory>();
builder.Services.AddScoped<EmployeeService>();
builder.Services.AddControllers();

var app = builder.Build();

var configuredPathBase = builder.Configuration["ASPNETCORE_PATHBASE"] ?? builder.Configuration["PathBase"];
if (!string.IsNullOrWhiteSpace(configuredPathBase))
{
  if (!configuredPathBase.StartsWith('/'))
  {
    configuredPathBase = $"/{configuredPathBase}";
  }

  app.UsePathBase(configuredPathBase);
}

app.UseSwagger(options =>
{
  options.PreSerializeFilters.Add((swaggerDocument, httpRequest) =>
  {
    var serverBasePath = httpRequest.PathBase.HasValue ? httpRequest.PathBase.Value : string.Empty;
    swaggerDocument.Servers =
    [
      new OpenApiServer { Url = $"{httpRequest.Scheme}://{httpRequest.Host.Value}{serverBasePath}" }
    ];
  });
});
app.UseSwaggerUI();

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.Run();
