namespace Scheduler.Api.Infrastructure.Domain.Models
{
  public class Shift
  {
    public int Id { get; set; }

    public int ScheduleId { get; set; }

    public int EmployeeId { get; set; }

    public DateTime Start { get; set; }

    public int DurationHours { get; set; }
  }
}
