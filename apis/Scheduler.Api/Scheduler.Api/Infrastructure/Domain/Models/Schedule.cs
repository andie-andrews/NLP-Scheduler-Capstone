namespace Scheduler.Api.Infrastructure.Domain.Models;

public class Schedule
{
  public int Id { get; set; }

  public string Name { get; set; } = default!;

  public DateTime StartDate { get; set; }

  public DateTime EndDate { get; set; }
}