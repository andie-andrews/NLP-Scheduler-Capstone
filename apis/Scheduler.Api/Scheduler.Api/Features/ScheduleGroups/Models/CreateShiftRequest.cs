namespace Scheduler.Api.Features.ScheduleGroups.Models
{
  public class CreateShiftRequest
  {
    public int EmployeeId { get; set; }
    public DateTime Start { get; set; }
    public int DurationHours { get; set; }
  }
}
