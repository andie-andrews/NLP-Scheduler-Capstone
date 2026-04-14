/*
  Restaurant scenario pre-deploy seed for SchedulerDb.
  - Upserts schedules: Kitchen, Bartenders, Servers, Hostesses, Managers, Busers
  - Upserts employees for restaurant scenario
  - Enforces Boss Man as the only supervisor in seeded dataset
  - Upserts Users for every seeded employee (username = first name, password = first name)
  - Upserts Boss user as Boss/Password with Supervisor role
  - Syncs schedule/manager and schedule/employee mappings
  - Re-runnable and safe to execute multiple times
*/

SET NOCOUNT ON;

DECLARE @EmployeeRoleId INT = 1;
DECLARE @SupervisorRoleId INT = 2;

IF OBJECT_ID('dbo.Roles', 'U') IS NOT NULL
BEGIN
  IF EXISTS (SELECT 1 FROM Roles WHERE Name = 'Employee')
    SELECT @EmployeeRoleId = Id FROM Roles WHERE Name = 'Employee';

  IF EXISTS (SELECT 1 FROM Roles WHERE Name = 'Supervisor')
    SELECT @SupervisorRoleId = Id FROM Roles WHERE Name = 'Supervisor';
END

/* Desired schedules */
DECLARE @Schedules TABLE (Name NVARCHAR(100) PRIMARY KEY);
INSERT INTO @Schedules (Name)
VALUES
  ('Kitchen'),
  ('Bartenders'),
  ('Servers'),
  ('Hostesses'),
  ('Managers'),
  ('Busers');

MERGE INTO Schedules AS tgt
USING @Schedules AS src
  ON tgt.Name = src.Name
WHEN NOT MATCHED BY TARGET THEN
  INSERT (Name) VALUES (src.Name);

/* Desired employees */
DECLARE @Employees TABLE (
  FirstName NVARCHAR(50),
  LastName NVARCHAR(50),
  RoleId INT,
  IsBoss BIT,
  PRIMARY KEY (FirstName, LastName)
);

INSERT INTO @Employees (FirstName, LastName, RoleId, IsBoss)
VALUES
  ('Boss', 'Man', @SupervisorRoleId, 1),

  ('Kai', 'Grill', @EmployeeRoleId, 0),
  ('Mia', 'Prep', @EmployeeRoleId, 0),
  ('Noah', 'Saute', @EmployeeRoleId, 0),

  ('Luca', 'Shaker', @EmployeeRoleId, 0),
  ('Ava', 'Collins', @EmployeeRoleId, 0),
  ('Ethan', 'Rocks', @EmployeeRoleId, 0),

  ('Olivia', 'Tray', @EmployeeRoleId, 0),
  ('Mason', 'Table', @EmployeeRoleId, 0),
  ('Isla', 'Service', @EmployeeRoleId, 0),

  ('Harper', 'Door', @EmployeeRoleId, 0),
  ('James', 'Seating', @EmployeeRoleId, 0),
  ('Emma', 'Welcome', @EmployeeRoleId, 0),

  ('Leo', 'Polish', @EmployeeRoleId, 0),
  ('Sofia', 'Reset', @EmployeeRoleId, 0),
  ('Henry', 'Clears', @EmployeeRoleId, 0);

MERGE INTO Employees AS tgt
USING @Employees AS src
  ON tgt.FirstName = src.FirstName AND tgt.LastName = src.LastName
WHEN MATCHED THEN
  UPDATE SET tgt.RoleId = src.RoleId
WHEN NOT MATCHED BY TARGET THEN
  INSERT (FirstName, LastName, RoleId)
  VALUES (src.FirstName, src.LastName, src.RoleId);

/* Ensure seeded set has only Boss Man as supervisor */
UPDATE e
SET e.RoleId = CASE WHEN s.IsBoss = 1 THEN @SupervisorRoleId ELSE @EmployeeRoleId END
FROM Employees e
JOIN @Employees s
  ON s.FirstName = e.FirstName
 AND s.LastName = e.LastName;

DECLARE @BossManId INT;
SELECT TOP 1 @BossManId = e.Id
FROM Employees e
WHERE e.FirstName = 'Boss' AND e.LastName = 'Man'
ORDER BY e.Id;

/* Boss Man manages all schedules */
MERGE INTO ScheduleManagers AS tgt
USING (
  SELECT s.Id AS ScheduleId, @BossManId AS ManagerId
  FROM Schedules s
  JOIN @Schedules wanted ON wanted.Name = s.Name
) AS src
  ON tgt.ScheduleId = src.ScheduleId
 AND tgt.ManagerId = src.ManagerId
WHEN NOT MATCHED BY TARGET THEN
  INSERT (ScheduleId, ManagerId)
  VALUES (src.ScheduleId, src.ManagerId)
WHEN NOT MATCHED BY SOURCE
  AND tgt.ScheduleId IN (
    SELECT s.Id FROM Schedules s JOIN @Schedules wanted ON wanted.Name = s.Name
  )
THEN DELETE;

/* Schedule employee roster: 3 per non-manager schedule */
DECLARE @ScheduleRoster TABLE (
  FirstName NVARCHAR(50),
  LastName NVARCHAR(50),
  ScheduleName NVARCHAR(100),
  PRIMARY KEY (FirstName, LastName, ScheduleName)
);

INSERT INTO @ScheduleRoster (FirstName, LastName, ScheduleName)
VALUES
  ('Kai', 'Grill', 'Kitchen'),
  ('Mia', 'Prep', 'Kitchen'),
  ('Noah', 'Saute', 'Kitchen'),

  ('Luca', 'Shaker', 'Bartenders'),
  ('Ava', 'Collins', 'Bartenders'),
  ('Ethan', 'Rocks', 'Bartenders'),

  ('Olivia', 'Tray', 'Servers'),
  ('Mason', 'Table', 'Servers'),
  ('Isla', 'Service', 'Servers'),

  ('Harper', 'Door', 'Hostesses'),
  ('James', 'Seating', 'Hostesses'),
  ('Emma', 'Welcome', 'Hostesses'),

  ('Leo', 'Polish', 'Busers'),
  ('Sofia', 'Reset', 'Busers'),
  ('Henry', 'Clears', 'Busers');

MERGE INTO ScheduleEmployees AS tgt
USING (
  SELECT s.Id AS ScheduleId, e.Id AS EmployeeId
  FROM @ScheduleRoster r
  JOIN Schedules s ON s.Name = r.ScheduleName
  JOIN Employees e ON e.FirstName = r.FirstName AND e.LastName = r.LastName
) AS src
  ON tgt.ScheduleId = src.ScheduleId
 AND tgt.EmployeeId = src.EmployeeId
WHEN NOT MATCHED BY TARGET THEN
  INSERT (ScheduleId, EmployeeId)
  VALUES (src.ScheduleId, src.EmployeeId)
WHEN NOT MATCHED BY SOURCE
  AND tgt.ScheduleId IN (
    SELECT s.Id
    FROM Schedules s
    JOIN @Schedules wanted ON wanted.Name = s.Name
    WHERE s.Name <> 'Managers'
  )
THEN DELETE;

/* User upserts for seeded employees */
IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL
BEGIN
  DECLARE @Users TABLE (
    Username NVARCHAR(100) PRIMARY KEY,
    [Password] NVARCHAR(255),
    [Role] INT,
    FirstName NVARCHAR(50),
    LastName NVARCHAR(50)
  );

  INSERT INTO @Users (Username, [Password], [Role], FirstName, LastName)
  VALUES
    ('Boss', 'Password', @SupervisorRoleId, 'Boss', 'Man'),

    ('Kai', 'Kai', @EmployeeRoleId, 'Kai', 'Grill'),
    ('Mia', 'Mia', @EmployeeRoleId, 'Mia', 'Prep'),
    ('Noah', 'Noah', @EmployeeRoleId, 'Noah', 'Saute'),

    ('Luca', 'Luca', @EmployeeRoleId, 'Luca', 'Shaker'),
    ('Ava', 'Ava', @EmployeeRoleId, 'Ava', 'Collins'),
    ('Ethan', 'Ethan', @EmployeeRoleId, 'Ethan', 'Rocks'),

    ('Olivia', 'Olivia', @EmployeeRoleId, 'Olivia', 'Tray'),
    ('Mason', 'Mason', @EmployeeRoleId, 'Mason', 'Table'),
    ('Isla', 'Isla', @EmployeeRoleId, 'Isla', 'Service'),

    ('Harper', 'Harper', @EmployeeRoleId, 'Harper', 'Door'),
    ('James', 'James', @EmployeeRoleId, 'James', 'Seating'),
    ('Emma', 'Emma', @EmployeeRoleId, 'Emma', 'Welcome'),

    ('Leo', 'Leo', @EmployeeRoleId, 'Leo', 'Polish'),
    ('Sofia', 'Sofia', @EmployeeRoleId, 'Sofia', 'Reset'),
    ('Henry', 'Henry', @EmployeeRoleId, 'Henry', 'Clears');

  MERGE INTO Users AS tgt
  USING (
    SELECT u.Username, u.[Password], u.[Role], e.Id AS EmployeeId
    FROM @Users u
    JOIN Employees e
      ON e.FirstName = u.FirstName
     AND e.LastName = u.LastName
  ) AS src
    ON tgt.Username = src.Username
  WHEN MATCHED THEN
    UPDATE SET
      tgt.[Password] = src.[Password],
      tgt.[Role] = src.[Role],
      tgt.EmployeeId = src.EmployeeId
  WHEN NOT MATCHED BY TARGET THEN
    INSERT (Username, [Password], [Role], EmployeeId)
    VALUES (src.Username, src.[Password], src.[Role], src.EmployeeId)
  WHEN NOT MATCHED BY SOURCE
    AND tgt.Username IN (SELECT Username FROM @Users)
  THEN DELETE;
END

PRINT 'Restaurant scenario pre-deploy seed complete.';
