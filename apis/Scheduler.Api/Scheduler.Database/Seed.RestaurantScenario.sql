/*
  Demo seed for restaurant scenario.
  Uses ScheduleGroup naming introduced by the Schedule -> ScheduleGroup refactor.
*/

SET NOCOUNT ON;

-- Ensure roles exist.
IF NOT EXISTS (SELECT 1 FROM Roles WHERE Id = 1)
  INSERT INTO Roles (Id, Name) VALUES (1, 'Employee');

IF NOT EXISTS (SELECT 1 FROM Roles WHERE Id = 2)
  INSERT INTO Roles (Id, Name) VALUES (2, 'Supervisor');

-- Manager account used in demos.
IF NOT EXISTS (SELECT 1 FROM Employees WHERE Email = 'boss.man@scheduler.local')
BEGIN
  INSERT INTO Employees (FirstName, LastName, Email, RoleId)
  VALUES ('Boss', 'Man', 'boss.man@scheduler.local', 2);
END

DECLARE @ManagerId INT = (SELECT TOP 1 Id FROM Employees WHERE Email = 'boss.man@scheduler.local');

-- Schedule groups.
IF NOT EXISTS (SELECT 1 FROM ScheduleGroups WHERE Name = 'Servers')
  INSERT INTO ScheduleGroups (Name) VALUES ('Servers');

IF NOT EXISTS (SELECT 1 FROM ScheduleGroups WHERE Name = 'Hostesses')
  INSERT INTO ScheduleGroups (Name) VALUES ('Hostesses');

IF NOT EXISTS (SELECT 1 FROM ScheduleGroups WHERE Name = 'Kitchen')
  INSERT INTO ScheduleGroups (Name) VALUES ('Kitchen');

IF NOT EXISTS (SELECT 1 FROM ScheduleGroups WHERE Name = 'Bartenders')
  INSERT INTO ScheduleGroups (Name) VALUES ('Bartenders');

DECLARE @ServersGroupId INT = (SELECT TOP 1 Id FROM ScheduleGroups WHERE Name = 'Servers');
DECLARE @HostessesGroupId INT = (SELECT TOP 1 Id FROM ScheduleGroups WHERE Name = 'Hostesses');
DECLARE @KitchenGroupId INT = (SELECT TOP 1 Id FROM ScheduleGroups WHERE Name = 'Kitchen');
DECLARE @BartendersGroupId INT = (SELECT TOP 1 Id FROM ScheduleGroups WHERE Name = 'Bartenders');

-- Employees referenced in demo prompts.
IF NOT EXISTS (SELECT 1 FROM Employees WHERE Email = 'olivia.tray@scheduler.local')
  INSERT INTO Employees (FirstName, LastName, Email, RoleId) VALUES ('Olivia', 'Tray', 'olivia.tray@scheduler.local', 1);

IF NOT EXISTS (SELECT 1 FROM Employees WHERE Email = 'emma.welcome@scheduler.local')
  INSERT INTO Employees (FirstName, LastName, Email, RoleId) VALUES ('Emma', 'Welcome', 'emma.welcome@scheduler.local', 1);

IF NOT EXISTS (SELECT 1 FROM Employees WHERE Email = 'mia.prep@scheduler.local')
  INSERT INTO Employees (FirstName, LastName, Email, RoleId) VALUES ('Mia', 'Prep', 'mia.prep@scheduler.local', 1);

IF NOT EXISTS (SELECT 1 FROM Employees WHERE Email = 'noah.saute@scheduler.local')
  INSERT INTO Employees (FirstName, LastName, Email, RoleId) VALUES ('Noah', 'Saute', 'noah.saute@scheduler.local', 1);

IF NOT EXISTS (SELECT 1 FROM Employees WHERE Email = 'kai.grill@scheduler.local')
  INSERT INTO Employees (FirstName, LastName, Email, RoleId) VALUES ('Kai', 'Grill', 'kai.grill@scheduler.local', 1);

IF NOT EXISTS (SELECT 1 FROM Employees WHERE Email = 'luca.shaker@scheduler.local')
  INSERT INTO Employees (FirstName, LastName, Email, RoleId) VALUES ('Luca', 'Shaker', 'luca.shaker@scheduler.local', 1);

-- Manager -> schedule-group relationships.
IF @ManagerId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ScheduleGroupManagers WHERE ScheduleGroupId = @ServersGroupId AND ManagerId = @ManagerId)
  INSERT INTO ScheduleGroupManagers (ScheduleGroupId, ManagerId) VALUES (@ServersGroupId, @ManagerId);

IF @ManagerId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ScheduleGroupManagers WHERE ScheduleGroupId = @HostessesGroupId AND ManagerId = @ManagerId)
  INSERT INTO ScheduleGroupManagers (ScheduleGroupId, ManagerId) VALUES (@HostessesGroupId, @ManagerId);

IF @ManagerId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ScheduleGroupManagers WHERE ScheduleGroupId = @KitchenGroupId AND ManagerId = @ManagerId)
  INSERT INTO ScheduleGroupManagers (ScheduleGroupId, ManagerId) VALUES (@KitchenGroupId, @ManagerId);

IF @ManagerId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ScheduleGroupManagers WHERE ScheduleGroupId = @BartendersGroupId AND ManagerId = @ManagerId)
  INSERT INTO ScheduleGroupManagers (ScheduleGroupId, ManagerId) VALUES (@BartendersGroupId, @ManagerId);

-- Employee -> schedule-group assignments.
DECLARE @OliviaId INT = (SELECT TOP 1 Id FROM Employees WHERE Email = 'olivia.tray@scheduler.local');
DECLARE @EmmaId INT = (SELECT TOP 1 Id FROM Employees WHERE Email = 'emma.welcome@scheduler.local');
DECLARE @MiaId INT = (SELECT TOP 1 Id FROM Employees WHERE Email = 'mia.prep@scheduler.local');
DECLARE @NoahId INT = (SELECT TOP 1 Id FROM Employees WHERE Email = 'noah.saute@scheduler.local');
DECLARE @KaiId INT = (SELECT TOP 1 Id FROM Employees WHERE Email = 'kai.grill@scheduler.local');
DECLARE @LucaId INT = (SELECT TOP 1 Id FROM Employees WHERE Email = 'luca.shaker@scheduler.local');

IF @OliviaId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ScheduleGroupEmployees WHERE ScheduleGroupId = @ServersGroupId AND EmployeeId = @OliviaId)
  INSERT INTO ScheduleGroupEmployees (ScheduleGroupId, EmployeeId) VALUES (@ServersGroupId, @OliviaId);

IF @EmmaId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ScheduleGroupEmployees WHERE ScheduleGroupId = @HostessesGroupId AND EmployeeId = @EmmaId)
  INSERT INTO ScheduleGroupEmployees (ScheduleGroupId, EmployeeId) VALUES (@HostessesGroupId, @EmmaId);

IF @MiaId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ScheduleGroupEmployees WHERE ScheduleGroupId = @KitchenGroupId AND EmployeeId = @MiaId)
  INSERT INTO ScheduleGroupEmployees (ScheduleGroupId, EmployeeId) VALUES (@KitchenGroupId, @MiaId);

IF @NoahId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ScheduleGroupEmployees WHERE ScheduleGroupId = @KitchenGroupId AND EmployeeId = @NoahId)
  INSERT INTO ScheduleGroupEmployees (ScheduleGroupId, EmployeeId) VALUES (@KitchenGroupId, @NoahId);

IF @KaiId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ScheduleGroupEmployees WHERE ScheduleGroupId = @KitchenGroupId AND EmployeeId = @KaiId)
  INSERT INTO ScheduleGroupEmployees (ScheduleGroupId, EmployeeId) VALUES (@KitchenGroupId, @KaiId);

IF @LucaId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM ScheduleGroupEmployees WHERE ScheduleGroupId = @BartendersGroupId AND EmployeeId = @LucaId)
  INSERT INTO ScheduleGroupEmployees (ScheduleGroupId, EmployeeId) VALUES (@BartendersGroupId, @LucaId);

PRINT 'Restaurant scenario seed applied successfully using ScheduleGroup tables.';
