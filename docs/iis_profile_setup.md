# Creating Local IIS Profiles for `Scheduler.Api` and `Employee.Api`

Use these steps when you want the APIs available at:

- `http://localhost/schedulerapi`
- `http://localhost/employeeapi`

## 1) Enable IIS on your machine

On Windows, enable:

- **Internet Information Services**
- **ASP.NET 4.8** (if needed for tools)
- **IIS Management Console**

Then restart if prompted.

## 2) Create IIS applications

For each API, open **IIS Manager** and add an application under your target website (commonly `Default Web Site`):

### Scheduler API

- **Alias**: `schedulerapi`
- **Physical path**: Scheduler API published folder
- **Application pool**: `schedulerapi AppPool` (No Managed Code)

### Employee API

- **Alias**: `employeeapi`
- **Physical path**: Employee API published folder
- **Application pool**: `employeeapi AppPool` (No Managed Code)

## 3) Grant SQL access to IIS app pool identities

If your connection string uses integrated security (`Trusted_Connection=True`), run:

- `apis/Scheduler.Api/Scheduler.Database/IisAppPoolSqlAccess.sql`

This script grants `db_datareader` + `db_datawriter` permissions for both:

- `IIS APPPOOL\schedulerapi AppPool`
- `IIS APPPOOL\employeeapi AppPool`

> If your DB name is not `SchedulerDb`, update the `USE [SchedulerDb]` line before running.

## 4) Seed starter data

The database seed script is in:

- `apis/Scheduler.Api/Scheduler.Database/PostDeployment.sql`

That script inserts baseline roles and a supervisor user for local testing.

## 5) Add IIS launch profiles in `launchSettings.json`

Both API projects include an `IIS` profile with `ASPNETCORE_PATHBASE`:

- Scheduler API path base: `/schedulerapi`
- Employee API path base: `/employeeapi`

## 6) Run from Visual Studio

1. Open the API project you want to debug.
2. Select the **IIS** profile from the run target dropdown.
3. Start debugging.

Swagger URLs should be:

- `http://localhost/schedulerapi/swagger`
- `http://localhost/employeeapi/swagger`

## Troubleshooting

If Visual Studio shows:

- `The IIS settings are missing the App Url property.`

Confirm these values are present:

- `Properties/launchSettings.json` → `iisSettings.iis.applicationUrl`
- `*.csproj.user` contains `UseIIS=True` and correct `IISUrl`

If the error persists, close Visual Studio, delete the solution `.vs` folder, reopen the solution, and pick the `IIS` profile again.
