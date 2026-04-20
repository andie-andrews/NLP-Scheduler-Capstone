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

## 3) Add an IIS launch profile in `launchSettings.json`

The API project now includes an `IIS` profile:

- `commandName: "IIS"`
- `launchUrl: "schedulerapi/swagger"`
- `ASPNETCORE_PATHBASE=/schedulerapi`

This makes local debugging honor the virtual directory base path.

## 4) Run from Visual Studio

1. Open the API project properties.
2. Select the **IIS** profile from the run target dropdown.
3. Start debugging.

If configured correctly, Swagger should open under:

- `http://localhost/schedulerapi/swagger`
