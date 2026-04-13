namespace Scheduler.Api.Features.Shifts.Models;

public class UpdateShiftRequest
{
  public DateTime Start { get; set; }
  public int DurationHours { get; set; }
}
