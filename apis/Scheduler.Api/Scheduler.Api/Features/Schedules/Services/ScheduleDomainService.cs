using Scheduler.Api.Features.Schedules.Handlers;
using Scheduler.Api.Features.Schedules.Models;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.Schedules.Services;

public class ScheduleDomainService
{
  private readonly GetSchedulesHandler _getSchedules;
  private readonly GetScheduleEmployeesHandler _getEmployees;
  private readonly GetEmployeeSchedulesHandler _getEmployeeSchedulesHandler;
  private readonly GetManagerSchedulesHandler _getManagerSchedulesHandler;
  private readonly AddEmployeeToScheduleHandler _addEmployeeToScheduleHandler;
  private readonly DeleteEmployeeToScheduleHandler _deleteEmployeeToScheduleHandler;
  private readonly CreateScheduleHandler _createScheduleHandler;
  private readonly UpdateScheduleHandler _updateScheduleHandler;
  private readonly DeleteScheduleHandler _deleteScheduleHandler;

  public ScheduleDomainService(
    GetSchedulesHandler getSchedules,
    GetScheduleEmployeesHandler getEmployees,
    GetEmployeeSchedulesHandler getEmployeeSchedulesHandler,
    GetManagerSchedulesHandler getManagerSchedulesHandler,
    CreateScheduleHandler createScheduleHandler,
    UpdateScheduleHandler updateScheduleHandler,
    DeleteScheduleHandler deleteScheduleHandler,
    AddEmployeeToScheduleHandler addEmployeeToScheduleHandler,
    DeleteEmployeeToScheduleHandler deleteEmployeeToScheduleHandler)
  {
    _getSchedules = getSchedules;
    _getEmployees = getEmployees;
    _getEmployeeSchedulesHandler = getEmployeeSchedulesHandler;
    _getManagerSchedulesHandler = getManagerSchedulesHandler;
    _createScheduleHandler = createScheduleHandler;
    _updateScheduleHandler = updateScheduleHandler;
    _deleteScheduleHandler = deleteScheduleHandler;
    _addEmployeeToScheduleHandler = addEmployeeToScheduleHandler;
    _deleteEmployeeToScheduleHandler = deleteEmployeeToScheduleHandler;
  }

  public Task<IEnumerable<Schedule>> GetSchedules(string? query = null)
    => string.IsNullOrWhiteSpace(query) ? _getSchedules.Handle() : _getSchedules.Handle(query);

  public Task<int> CreateSchedule(CreateScheduleRequest request, int managerId)
    => _createScheduleHandler.Handle(request.Name, managerId);

  public Task UpdateSchedule(int scheduleId, UpdateScheduleRequest request)
    => _updateScheduleHandler.Handle(scheduleId, request.Name);

  public Task DeleteSchedule(int scheduleId)
    => _deleteScheduleHandler.Handle(scheduleId);

  public Task<IEnumerable<Scheduler.Api.Infrastructure.Domain.Models.Employee>> GetScheduleEmployees(int scheduleId)
    => _getEmployees.Handle(scheduleId);

  public Task<IEnumerable<Schedule>> GetEmployeeSchedules(int employeeId)
    => _getEmployeeSchedulesHandler.Handle(employeeId);

  public Task<IEnumerable<Schedule>> GetManagerSchedules(int managerId)
    => _getManagerSchedulesHandler.Handle(managerId);

  public Task AddEmployee(int scheduleId, int employeeId)
    => _addEmployeeToScheduleHandler.Handle(scheduleId, employeeId);

  public Task RemoveEmployee(int scheduleId, int employeeId)
    => _deleteEmployeeToScheduleHandler.Handle(scheduleId, employeeId);
}
