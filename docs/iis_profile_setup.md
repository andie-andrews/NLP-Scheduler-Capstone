# Creating a Local IIS Profile for `Scheduler.Api`

Use these steps when you want the API available at:

- `http://localhost/schedulerapi`

## 1) Enable IIS on your machine

On Windows, enable:

- **Internet Information Services**
- **ASP.NET 4.8** (if needed for tools)
- **IIS Management Console**

Then restart if prompted.

## 2) Create the IIS site and virtual directory/application

1. Open **IIS Manager**.
2. Right-click **Default Web Site** (or your target site) and choose **Add Application...**.
3. Set:
   - **Alias**: `schedulerapi`
   - **Physical path**: your published API output folder
4. Choose or create an app pool with **No Managed Code** (for ASP.NET Core hosting model behind ANCM).
5. Apply and start the site/application.

## 3) Grant SQL access to the IIS app pool identity

If your connection string uses `Trusted_Connection=True`, run this in SQL Server so the IIS app pool can log in:

```sql
CREATE LOGIN [IIS APPPOOL\schedulerapi AppPool] FROM WINDOWS;
GO
USE [SchedulerDb];
GO
CREATE USER [IIS APPPOOL\schedulerapi AppPool] FOR LOGIN [IIS APPPOOL\schedulerapi AppPool];
GO
ALTER ROLE db_datareader ADD MEMBER [IIS APPPOOL\schedulerapi AppPool];
ALTER ROLE db_datawriter ADD MEMBER [IIS APPPOOL\schedulerapi AppPool];
```

## 4) Seed starter data

The database seed script is in:

- `apis/Scheduler.Api/Scheduler.Database/PostDeployment.sql`

That script inserts baseline roles and a supervisor user for local testing.

## 5) Add an IIS launch profile in `launchSettings.json`

The API project now includes an `IIS` profile:

- `commandName: "IIS"`
- `applicationUrl: "http://localhost/schedulerapi"`
- `launchUrl: "swagger"`
- `ASPNETCORE_PATHBASE=/schedulerapi`

This makes local debugging honor the virtual directory base path.

## 6) Run from Visual Studio

1. Open the API project properties.
2. Select the **IIS** profile from the run target dropdown.
3. Start debugging.

If configured correctly, Swagger should open under:

- `http://localhost/schedulerapi/swagger`

## Troubleshooting

If Visual Studio shows:

- `The IIS settings are missing the App Url property.`

Confirm these values are present:

- `Properties/launchSettings.json` → `iisSettings.iis.applicationUrl = "http://localhost/schedulerapi"`
- `Scheduler.Api.csproj.user`:

- `<UseIIS>True</UseIIS>`
- `<UseIISExpress>False</UseIISExpress>`
- `<IISUrl>http://localhost/schedulerapi</IISUrl>`

If the error persists, close Visual Studio, delete the solution `.vs` folder, reopen the solution, and pick the `IIS` profile again.
