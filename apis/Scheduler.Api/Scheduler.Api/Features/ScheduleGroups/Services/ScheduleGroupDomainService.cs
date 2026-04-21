using Scheduler.Api.Features.ScheduleGroups.Handlers;
using Scheduler.Api.Features.ScheduleGroups.Models;
using Scheduler.Api.Infrastructure.Domain.Models;

namespace Scheduler.Api.Features.ScheduleGroups.Services;

public class ScheduleGroupDomainService
{
  private readonly GetScheduleGroupsHandler _getScheduleGroups;
  private readonly GetScheduleGroupEmployeesHandler _getEmployees;
  private readonly GetEmployeeScheduleGroupsHandler _getEmployeeScheduleGroupsHandler;
  private readonly GetManagerScheduleGroupsHandler _getManagerScheduleGroupsHandler;
  private readonly AddEmployeeToScheduleGroupHandler _addEmployeeToScheduleGroupHandler;
  private readonly DeleteEmployeeFromScheduleGroupHandler _deleteEmployeeToScheduleHandler;
  private readonly CreateScheduleGroupHandler _createScheduleGroupHandler;
  private readonly UpdateScheduleGroupHandler _updateScheduleGroupHandler;
  private readonly DeleteScheduleGroupHandler _deleteScheduleGroupHandler;

  public ScheduleGroupDomainService(
    GetScheduleGroupsHandler getScheduleGroups,
    GetScheduleGroupEmployeesHandler getEmployees,
    GetEmployeeScheduleGroupsHandler getEmployeeScheduleGroupsHandler,
    GetManagerScheduleGroupsHandler getManagerScheduleGroupsHandler,
    CreateScheduleGroupHandler createScheduleGroupHandler,
    UpdateScheduleGroupHandler updateScheduleGroupHandler,
    DeleteScheduleGroupHandler deleteScheduleGroupHandler,
    AddEmployeeToScheduleGroupHandler addEmployeeToScheduleGroupHandler,
    DeleteEmployeeFromScheduleGroupHandler deleteEmployeeToScheduleHandler)
  {
    _getScheduleGroups = getScheduleGroups;
    _getEmployees = getEmployees;
    _getEmployeeScheduleGroupsHandler = getEmployeeScheduleGroupsHandler;
    _getManagerScheduleGroupsHandler = getManagerScheduleGroupsHandler;
    _createScheduleGroupHandler = createScheduleGroupHandler;
    _updateScheduleGroupHandler = updateScheduleGroupHandler;
    _deleteScheduleGroupHandler = deleteScheduleGroupHandler;
    _addEmployeeToScheduleGroupHandler = addEmployeeToScheduleGroupHandler;
    _deleteEmployeeToScheduleHandler = deleteEmployeeToScheduleHandler;
  }

  public Task<IEnumerable<ScheduleGroup>> GetScheduleGroups(string? query = null)
    => string.IsNullOrWhiteSpace(query) ? _getScheduleGroups.Handle() : _getScheduleGroups.Handle(query);

  public Task<int> CreateScheduleGroup(CreateScheduleGroupRequest request, int managerId)
    => _createScheduleGroupHandler.Handle(request.Name, managerId);

  public Task UpdateScheduleGroup(int scheduleGroupId, UpdateScheduleGroupRequest request)
    => _updateScheduleGroupHandler.Handle(scheduleGroupId, request.Name);

  public Task DeleteScheduleGroup(int scheduleGroupId)
    => _deleteScheduleGroupHandler.Handle(scheduleGroupId);

  public Task<IEnumerable<Scheduler.Api.Infrastructure.Domain.Models.Employee>> GetScheduleGroupEmployees(int scheduleGroupId)
    => _getEmployees.Handle(scheduleGroupId);

  public Task<IEnumerable<ScheduleGroup>> GetEmployeeScheduleGroups(int employeeId)
    => _getEmployeeScheduleGroupsHandler.Handle(employeeId);

  public Task<IEnumerable<ScheduleGroup>> GetManagerScheduleGroups(int managerId)
    => _getManagerScheduleGroupsHandler.Handle(managerId);

  public Task AddEmployee(int scheduleGroupId, int employeeId)
    => _addEmployeeToScheduleGroupHandler.Handle(scheduleGroupId, employeeId);

  public Task RemoveEmployee(int scheduleGroupId, int employeeId)
    => _deleteEmployeeToScheduleHandler.Handle(scheduleGroupId, employeeId);
}
