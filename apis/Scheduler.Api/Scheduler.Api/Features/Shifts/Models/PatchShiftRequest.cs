namespace Scheduler.Api.Features.Shifts.Models;

public class PatchShiftRequest
{
  public int? EmployeeId { get; set; }
  public DateTime? Start { get; set; }
  public int? DurationHours { get; set; }
}
