/*
  DACPAC Post-Deployment script.
  - Cleans up legacy restaurant seed rows from earlier iterations (if present)
  - Executes current restaurant seed upsert script
*/

SET NOCOUNT ON;

/* Legacy cleanup from prior seed drafts */
IF OBJECT_ID('dbo.Employees', 'U') IS NOT NULL
BEGIN
  DECLARE @LegacyEmployees TABLE (FirstName NVARCHAR(50), LastName NVARCHAR(50), PRIMARY KEY (FirstName, LastName));

  INSERT INTO @LegacyEmployees (FirstName, LastName)
  VALUES
    ('Nora', 'Lead'),
    ('Caleb', 'Floor'),
    ('Zoe', 'Ops');

  IF OBJECT_ID('dbo.ScheduleEmployees', 'U') IS NOT NULL
  BEGIN
    DELETE se
    FROM ScheduleEmployees se
    JOIN Employees e ON e.Id = se.EmployeeId
    JOIN @LegacyEmployees le
      ON le.FirstName = e.FirstName
     AND le.LastName = e.LastName;
  END

  IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL
  BEGIN
    DELETE u
    FROM Users u
    JOIN Employees e ON e.Id = u.EmployeeId
    JOIN @LegacyEmployees le
      ON le.FirstName = e.FirstName
     AND le.LastName = e.LastName;
  END

  DELETE e
  FROM Employees e
  JOIN @LegacyEmployees le
    ON le.FirstName = e.FirstName
   AND le.LastName = e.LastName;
END

:r .\Seed.RestaurantScenario.sql
