/*
  Grants SQL access for local IIS app pool identities used by:
  - Scheduler.Api -> IIS APPPOOL\schedulerapi AppPool
  - Employee.Api  -> IIS APPPOOL\employeeapi AppPool

  Update the USE [SchedulerDb] statement if your database name is different.
*/

IF SUSER_ID(N'IIS APPPOOL\schedulerapi AppPool') IS NULL
BEGIN
  CREATE LOGIN [IIS APPPOOL\schedulerapi AppPool] FROM WINDOWS;
END;
GO

IF SUSER_ID(N'IIS APPPOOL\employeeapi AppPool') IS NULL
BEGIN
  CREATE LOGIN [IIS APPPOOL\employeeapi AppPool] FROM WINDOWS;
END;
GO

USE [SchedulerDb];
GO

IF USER_ID(N'IIS APPPOOL\schedulerapi AppPool') IS NULL
BEGIN
  CREATE USER [IIS APPPOOL\schedulerapi AppPool]
    FOR LOGIN [IIS APPPOOL\schedulerapi AppPool];
END;
GO

IF USER_ID(N'IIS APPPOOL\employeeapi AppPool') IS NULL
BEGIN
  CREATE USER [IIS APPPOOL\employeeapi AppPool]
    FOR LOGIN [IIS APPPOOL\employeeapi AppPool];
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.database_role_members drm
  JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
  JOIN sys.database_principals m ON drm.member_principal_id = m.principal_id
  WHERE r.name = N'db_datareader'
    AND m.name = N'IIS APPPOOL\schedulerapi AppPool'
)
BEGIN
  ALTER ROLE db_datareader ADD MEMBER [IIS APPPOOL\schedulerapi AppPool];
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.database_role_members drm
  JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
  JOIN sys.database_principals m ON drm.member_principal_id = m.principal_id
  WHERE r.name = N'db_datawriter'
    AND m.name = N'IIS APPPOOL\schedulerapi AppPool'
)
BEGIN
  ALTER ROLE db_datawriter ADD MEMBER [IIS APPPOOL\schedulerapi AppPool];
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.database_role_members drm
  JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
  JOIN sys.database_principals m ON drm.member_principal_id = m.principal_id
  WHERE r.name = N'db_datareader'
    AND m.name = N'IIS APPPOOL\employeeapi AppPool'
)
BEGIN
  ALTER ROLE db_datareader ADD MEMBER [IIS APPPOOL\employeeapi AppPool];
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.database_role_members drm
  JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
  JOIN sys.database_principals m ON drm.member_principal_id = m.principal_id
  WHERE r.name = N'db_datawriter'
    AND m.name = N'IIS APPPOOL\employeeapi AppPool'
)
BEGIN
  ALTER ROLE db_datawriter ADD MEMBER [IIS APPPOOL\employeeapi AppPool];
END;
GO
