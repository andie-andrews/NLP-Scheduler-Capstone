namespace Scheduler.Api.Features.Employee.Queries
{
  public class EmployeeQueries
  {
    public record GetEmployeeByNameQuery(string FirstName, string LastName);
  }
}
