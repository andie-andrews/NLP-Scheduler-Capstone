-- Insert initial data into the database

-- Backfill schema for environments created before Email was added.
IF COL_LENGTH('Employees', 'Email') IS NULL
BEGIN
    ALTER TABLE Employees ADD Email NVARCHAR(255) NULL;

    UPDATE Employees
    SET Email = LOWER(CONCAT(FirstName, '.', LastName, '@scheduler.local'))
    WHERE Email IS NULL;

    ALTER TABLE Employees ALTER COLUMN Email NVARCHAR(255) NOT NULL;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'UQ_Employees_Email'
          AND object_id = OBJECT_ID('dbo.Employees')
    )
    BEGIN
        ALTER TABLE Employees ADD CONSTRAINT [UQ_Employees_Email] UNIQUE ([Email]);
    END
END

-- Roles
IF NOT EXISTS (SELECT 1 FROM Roles)
BEGIN
    INSERT INTO Roles (Id, Name)
    VALUES
        (1, 'Employee'),
        (2, 'Supervisor');
END

-- Schedules
IF NOT EXISTS (SELECT 1 FROM Schedules WHERE Name = 'Week 1')
BEGIN
    INSERT INTO Schedules (Name)
    VALUES ('Week 1');
END

-- Employees
IF NOT EXISTS (SELECT 1 FROM Employees WHERE Email = 'john.doe@scheduler.local')
BEGIN
    INSERT INTO Employees (FirstName, LastName, Email, RoleId)
    VALUES ('John', 'Doe', 'john.doe@scheduler.local', 1);
END

IF NOT EXISTS (SELECT 1 FROM Employees WHERE Email = 'jane.smith@scheduler.local')
BEGIN
    INSERT INTO Employees (FirstName, LastName, Email, RoleId)
    VALUES ('Jane', 'Smith', 'jane.smith@scheduler.local', 1);
END

IF NOT EXISTS (SELECT 1 FROM Employees WHERE Email = 'boss.man@scheduler.local')
BEGIN
    INSERT INTO Employees (FirstName, LastName, Email, RoleId)
    VALUES ('Boss', 'Man', 'boss.man@scheduler.local', 2);
END

DECLARE @ScheduleId INT = (SELECT TOP 1 Id FROM Schedules WHERE Name = 'Week 1' ORDER BY Id);
DECLARE @JohnEmployeeId INT = (SELECT TOP 1 Id FROM Employees WHERE Email = 'john.doe@scheduler.local' ORDER BY Id);
DECLARE @JaneEmployeeId INT = (SELECT TOP 1 Id FROM Employees WHERE Email = 'jane.smith@scheduler.local' ORDER BY Id);
DECLARE @BossEmployeeId INT = (SELECT TOP 1 Id FROM Employees WHERE Email = 'boss.man@scheduler.local' ORDER BY Id);

-- Assign employees to schedule
IF @ScheduleId IS NOT NULL AND @JohnEmployeeId IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM ScheduleEmployees WHERE ScheduleId = @ScheduleId AND EmployeeId = @JohnEmployeeId)
BEGIN
    INSERT INTO ScheduleEmployees (ScheduleId, EmployeeId) VALUES (@ScheduleId, @JohnEmployeeId);
END

IF @ScheduleId IS NOT NULL AND @JaneEmployeeId IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM ScheduleEmployees WHERE ScheduleId = @ScheduleId AND EmployeeId = @JaneEmployeeId)
BEGIN
    INSERT INTO ScheduleEmployees (ScheduleId, EmployeeId) VALUES (@ScheduleId, @JaneEmployeeId);
END

-- Assign manager
IF @ScheduleId IS NOT NULL AND @BossEmployeeId IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM ScheduleManagers WHERE ScheduleId = @ScheduleId AND ManagerId = @BossEmployeeId)
BEGIN
    INSERT INTO ScheduleManagers (ScheduleId, ManagerId) VALUES (@ScheduleId, @BossEmployeeId);
END

-- Shifts
IF @ScheduleId IS NOT NULL AND @JohnEmployeeId IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM Shifts WHERE ScheduleId = @ScheduleId AND EmployeeId = @JohnEmployeeId)
BEGIN
    INSERT INTO Shifts (ScheduleId, EmployeeId, Start, DurationHours)
    VALUES
    (@ScheduleId, @JohnEmployeeId, DATEADD(HOUR, 8, GETDATE()), 8);
END

IF @JohnEmployeeId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM Users WHERE Username = 'john')
BEGIN
    INSERT INTO Users (Username, Password, Role, EmployeeId) VALUES ('john', 'password', 1, @JohnEmployeeId);
END

IF @JaneEmployeeId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM Users WHERE Username = 'jane')
BEGIN
    INSERT INTO Users (Username, Password, Role, EmployeeId) VALUES ('jane', 'password', 1, @JaneEmployeeId);
END

IF @BossEmployeeId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM Users WHERE Username = 'boss')
BEGIN
    INSERT INTO Users (Username, Password, Role, EmployeeId) VALUES ('boss', 'password', 2, @BossEmployeeId);
END
