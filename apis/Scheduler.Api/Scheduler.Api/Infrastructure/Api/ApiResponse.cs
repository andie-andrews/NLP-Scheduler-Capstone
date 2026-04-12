using Microsoft.AspNetCore.Mvc;

namespace Scheduler.Api.Infrastructure.Api;

public record ApiError(string Code, string Message);

public class ApiResponse<T>
{
  public bool Success { get; init; }
  public T? Data { get; init; }
  public IReadOnlyList<ApiError> Errors { get; init; } = Array.Empty<ApiError>();

  public static ApiResponse<T> Ok(T? data) => new()
  {
    Success = true,
    Data = data,
    Errors = Array.Empty<ApiError>(),
  };

  public static ApiResponse<T> Fail(params ApiError[] errors) => new()
  {
    Success = false,
    Data = default,
    Errors = errors,
  };
}

public static class ApiResponse
{
  public static ApiResponse<object?> Ok(object? data = null) => ApiResponse<object?>.Ok(data);

  public static ApiResponse<object?> Fail(string code, string message)
    => ApiResponse<object?>.Fail(new ApiError(code, message));

  public static IActionResult Error(
    ControllerBase controller,
    int statusCode,
    string code,
    string message)
    => controller.StatusCode(statusCode, Fail(code, message));

  public static IActionResult Error<T>(
    ControllerBase controller,
    int statusCode,
    string code,
    string message,
    T? data)
    => controller.StatusCode(statusCode, new ApiResponse<T>
    {
      Success = false,
      Data = data,
      Errors = new[] { new ApiError(code, message) },
    });
}
