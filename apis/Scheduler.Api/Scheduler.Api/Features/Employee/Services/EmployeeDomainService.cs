using Scheduler.Api.Features.Employee.Handlers;
using Scheduler.Api.Features.Employee.Models;
using Scheduler.Api.Features.Employee.Queries;

namespace Scheduler.Api.Features.Employee.Services;

public class EmployeeDomainService
{
  private readonly GetEmployeeByNameHandler _getByNameHandler;
  private readonly GetEmployeeByIdHandler _getEmployeeByIdHandler;
  private readonly GetAllEmployeesHandler _getAllHandler;
  private readonly CreateEmployeeHandler _createEmployeeHandler;
  private readonly DeleteEmployeeHandler _deleteEmployeeHandler;
  private readonly UpdateEmployeeHandler _updateEmployeeHandler;

  public EmployeeDomainService(
    GetEmployeeByNameHandler getByNameHandler,
    GetEmployeeByIdHandler getEmployeeByIdHandler,
    GetAllEmployeesHandler getAllHandler,
    CreateEmployeeHandler createEmployeeHandler,
    DeleteEmployeeHandler deleteEmployeeHandler,
    UpdateEmployeeHandler updateEmployeeHandler)
  {
    _getByNameHandler = getByNameHandler;
    _getEmployeeByIdHandler = getEmployeeByIdHandler;
    _getAllHandler = getAllHandler;
    _createEmployeeHandler = createEmployeeHandler;
    _deleteEmployeeHandler = deleteEmployeeHandler;
    _updateEmployeeHandler = updateEmployeeHandler;
  }

  public Task<Scheduler.Api.Infrastructure.Domain.Models.Employee?> GetEmployee(int employeeId)
    => _getEmployeeByIdHandler.Handle(employeeId);

  public Task<IEnumerable<Scheduler.Api.Infrastructure.Domain.Models.Employee>> GetEmployees(string? query)
  {
    if (string.IsNullOrWhiteSpace(query))
      return _getAllHandler.Handle();

    var parts = query.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    var firstName = parts.Length > 0 ? parts[0] : null;
    var lastName = parts.Length > 1 ? parts[1] : null;

    return _getByNameHandler.Handle(new EmployeeQueries.GetEmployeeByNameQuery(firstName, lastName));
  }

  public Task<int> CreateEmployee(CreateEmployeeRequest request)
    => _createEmployeeHandler.Handle(request);

  public Task<bool> DeleteEmployee(int employeeId)
    => _deleteEmployeeHandler.Handle(employeeId);

  public Task<bool> UpdateEmployee(int employeeId, UpdateEmployeeRequest request)
    => _updateEmployeeHandler.Handle(employeeId, request);
}
