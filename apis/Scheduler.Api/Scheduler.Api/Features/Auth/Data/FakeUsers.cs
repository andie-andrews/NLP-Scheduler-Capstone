using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Auth.Data
{
  public static class FakeUsers
  {
    public static List<User> Users = new()
    {
      new User { Id = 1, Username = "employee1", Password = "password", Role = Infrastructure.Domain.Enums.Role.Employee, EmployeeId = 101 },
      new User { Id = 2, Username = "boss1", Password = "password", Role = Infrastructure.Domain.Enums.Role.Supervisor, EmployeeId = 201 }
    };
  }
}
