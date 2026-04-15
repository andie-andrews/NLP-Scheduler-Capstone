/*
  DACPAC Post-Deployment script.
  - Cleans up legacy restaurant seed rows from earlier iterations (if present)
  - Executes current restaurant seed upsert script
*/

SET NOCOUNT ON;

/* Legacy cleanup from prior seed drafts */
IF OBJECT_ID('dbo.Employees', 'U') IS NOT NULL
BEGIN
  IF EXISTS (SELECT 1 FROM Employees WHERE FirstName = 'Nora' AND LastName = 'Lead')
  BEGIN
    IF OBJECT_ID('dbo.ScheduleEmployees', 'U') IS NOT NULL
    BEGIN
      DELETE se
      FROM ScheduleEmployees se
      JOIN Employees e ON e.Id = se.EmployeeId
      WHERE e.FirstName = 'Nora' AND e.LastName = 'Lead';
    END

    IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL
    BEGIN
      DELETE u
      FROM Users u
      JOIN Employees e ON e.Id = u.EmployeeId
      WHERE e.FirstName = 'Nora' AND e.LastName = 'Lead';
    END

    DELETE FROM Employees WHERE FirstName = 'Nora' AND LastName = 'Lead';
  END

  IF EXISTS (SELECT 1 FROM Employees WHERE FirstName = 'Caleb' AND LastName = 'Floor')
  BEGIN
    IF OBJECT_ID('dbo.ScheduleEmployees', 'U') IS NOT NULL
    BEGIN
      DELETE se
      FROM ScheduleEmployees se
      JOIN Employees e ON e.Id = se.EmployeeId
      WHERE e.FirstName = 'Caleb' AND e.LastName = 'Floor';
    END

    IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL
    BEGIN
      DELETE u
      FROM Users u
      JOIN Employees e ON e.Id = u.EmployeeId
      WHERE e.FirstName = 'Caleb' AND e.LastName = 'Floor';
    END

    DELETE FROM Employees WHERE FirstName = 'Caleb' AND LastName = 'Floor';
  END

  IF EXISTS (SELECT 1 FROM Employees WHERE FirstName = 'Zoe' AND LastName = 'Ops')
  BEGIN
    IF OBJECT_ID('dbo.ScheduleEmployees', 'U') IS NOT NULL
    BEGIN
      DELETE se
      FROM ScheduleEmployees se
      JOIN Employees e ON e.Id = se.EmployeeId
      WHERE e.FirstName = 'Zoe' AND e.LastName = 'Ops';
    END

    IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL
    BEGIN
      DELETE u
      FROM Users u
      JOIN Employees e ON e.Id = u.EmployeeId
      WHERE e.FirstName = 'Zoe' AND e.LastName = 'Ops';
    END

    DELETE FROM Employees WHERE FirstName = 'Zoe' AND LastName = 'Ops';
  END
END

:r .\Seed.RestaurantScenario.sql
