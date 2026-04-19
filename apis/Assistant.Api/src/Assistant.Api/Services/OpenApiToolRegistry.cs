using System.Text.Json.Nodes;
using Assistant.Api.Models;

namespace Assistant.Api.Services;

/// <summary>
/// Loads Scheduler OpenAPI spec and converts operations into tool metadata for model tool-calling.
/// </summary>
public sealed class OpenApiToolRegistry
{
  private readonly Dictionary<string, OpenApiOperation> _operations;
  private readonly JsonArray _tools;

  /// <summary>
  /// Reads and parses the OpenAPI file into operation and tool registries.
  /// </summary>
  public OpenApiToolRegistry(IWebHostEnvironment env)
  {
    var specPath = Path.GetFullPath(Path.Combine(env.ContentRootPath, "..", "..", "..", "..", ".openapi", "scheduler.api.json"));
    if (!File.Exists(specPath))
    {
      throw new FileNotFoundException($"OpenAPI specification not found at '{specPath}'.");
    }

    var root = JsonNode.Parse(File.ReadAllText(specPath))?.AsObject() ?? throw new InvalidOperationException("Invalid OpenAPI spec JSON.");
    var components = root["components"]?.AsObject();
    var schemas = components?["schemas"]?.AsObject() ?? new JsonObject();
    var paths = root["paths"]?.AsObject() ?? new JsonObject();

    _operations = new Dictionary<string, OpenApiOperation>(StringComparer.OrdinalIgnoreCase);
    _tools = [];

    foreach (var pathEntry in paths)
    {
      if (pathEntry.Value is not JsonObject methods) continue;

      foreach (var methodEntry in methods)
      {
        var method = methodEntry.Key.ToUpperInvariant();
        if (methodEntry.Value is not JsonObject op) continue;

        var operationId = op["operationId"]?.GetValue<string>();
        if (string.IsNullOrWhiteSpace(operationId)) continue;

        var description = op["summary"]?.GetValue<string>()
          ?? op["description"]?.GetValue<string>()
          ?? operationId;

        var pathParams = new List<string>();
        var queryParams = new List<string>();
        var required = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var properties = new JsonObject();
        var bodyProperties = new List<string>();

        var parameters = op["parameters"] as JsonArray;
        if (parameters is not null)
        {
          foreach (var parameterNode in parameters)
          {
            if (parameterNode is not JsonObject parameter) continue;
            var name = parameter["name"]?.GetValue<string>();
            var location = parameter["in"]?.GetValue<string>();
            if (string.IsNullOrWhiteSpace(name) || string.IsNullOrWhiteSpace(location)) continue;

            var schema = parameter["schema"] as JsonObject ?? new JsonObject { ["type"] = "string" };
            properties[name] = schema.DeepClone();

            if ((parameter["required"]?.GetValue<bool>()).GetValueOrDefault())
            {
              required.Add(name);
            }

            if (location.Equals("path", StringComparison.OrdinalIgnoreCase))
            {
              pathParams.Add(name);
            }
            else if (location.Equals("query", StringComparison.OrdinalIgnoreCase))
            {
              queryParams.Add(name);
            }
          }
        }

        var requestSchema = ResolveRequestBodySchema(op, schemas);
        if (requestSchema is not null)
        {
          var requestProperties = requestSchema["properties"] as JsonObject;
          if (requestProperties is not null)
          {
            foreach (var prop in requestProperties)
            {
              properties[prop.Key] = prop.Value?.DeepClone();
              bodyProperties.Add(prop.Key);
            }
          }

          var requestRequired = requestSchema["required"] as JsonArray;
          if (requestRequired is not null)
          {
            foreach (var req in requestRequired)
            {
              var requiredName = req?.GetValue<string>();
              if (!string.IsNullOrWhiteSpace(requiredName)) required.Add(requiredName);
            }
          }
        }

        var toolSchema = new JsonObject
        {
          ["type"] = "object",
          ["properties"] = properties,
          ["required"] = new JsonArray(required.Select(r => JsonValue.Create(r)).ToArray()),
        };

        var operation = new OpenApiOperation
        {
          OperationId = operationId,
          Method = method,
          PathTemplate = pathEntry.Key,
          Description = description,
          PathParameters = pathParams,
          QueryParameters = queryParams,
          BodyProperties = bodyProperties,
          RequiredParameters = required.ToList(),
          ToolParameterSchema = toolSchema,
        };

        _operations[operationId] = operation;
        _tools.Add(new JsonObject
        {
          ["type"] = "function",
          ["function"] = new JsonObject
          {
            ["name"] = operation.OperationId,
            ["description"] = operation.Description,
            ["parameters"] = operation.ToolParameterSchema.DeepClone(),
          },
        });
      }
    }
  }

  /// <summary>
  /// Returns a clone of tool definitions to send to the model.
  /// </summary>
  public JsonArray GetTools() => _tools.DeepClone() as JsonArray ?? [];

  /// <summary>
  /// Resolves an operation by operationId.
  /// </summary>
  public bool TryGetOperation(string operationId, out OpenApiOperation operation)
    => _operations.TryGetValue(operationId, out operation!);

  /// <summary>
  /// Resolves request body schema and follows local component references.
  /// </summary>
  private static JsonObject? ResolveRequestBodySchema(JsonObject operation, JsonObject schemas)
  {
    var requestBody = operation["requestBody"] as JsonObject;
    var content = requestBody?["content"] as JsonObject;
    var appJson = content?["application/json"] as JsonObject;
    var schema = appJson?["schema"] as JsonObject;
    if (schema is null) return null;

    var reference = schema["$ref"]?.GetValue<string>();
    if (string.IsNullOrWhiteSpace(reference))
    {
      return schema;
    }

    var parts = reference.Split('/', StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length == 0) return null;

    var schemaName = parts[^1];
    return schemas[schemaName] as JsonObject;
  }
}
