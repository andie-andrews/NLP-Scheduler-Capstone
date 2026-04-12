using Microsoft.AspNetCore.Http;

namespace Scheduler.Api.Features.Shifts;

public class ShiftValidationException : Exception
{
  public int StatusCode { get; }
  public string ErrorCode { get; }

  public ShiftValidationException(
    string message,
    string errorCode = "validation_error",
    int statusCode = StatusCodes.Status400BadRequest) : base(message)
  {
    ErrorCode = errorCode;
    StatusCode = statusCode;
  }
}
