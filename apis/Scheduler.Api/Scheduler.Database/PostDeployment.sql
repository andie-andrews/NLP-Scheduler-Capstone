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
IF NOT EXISTS (SELECT 1 FROM Schedules)
BEGIN
    INSERT INTO Schedules (Name)
    VALUES ('Week 1');
END

-- Employees
IF NOT EXISTS (SELECT 1 FROM Employees)
BEGIN
    INSERT INTO Employees (FirstName, LastName, Email, RoleId)
    VALUES
    ('John', 'Doe', 'john.doe@scheduler.local', 1),
    ('Jane', 'Smith', 'jane.smith@scheduler.local', 1),
    ('Boss', 'Man', 'boss.man@scheduler.local', 2);
END

-- Assign employees to schedule
IF NOT EXISTS (SELECT 1 FROM ScheduleEmployees)
BEGIN
    INSERT INTO ScheduleEmployees (ScheduleId, EmployeeId)
    VALUES
    (1, 1),
    (1, 2);
END

-- Assign manager
IF NOT EXISTS (SELECT 1 FROM ScheduleManagers)
BEGIN
    INSERT INTO ScheduleManagers (ScheduleId, ManagerId)
    VALUES
    (1, 3);
END

-- Shifts
IF NOT EXISTS (SELECT 1 FROM Shifts)
BEGIN
    INSERT INTO Shifts (ScheduleId, EmployeeId, Start, DurationHours)
    VALUES
    (1, 1, DATEADD(HOUR, 8, GETDATE()), 8);
END

IF NOT EXISTS (SELECT 1 FROM Users)
BEGIN
    INSERT INTO Users (Username, Password, Role, EmployeeId)
    VALUES
    ('john', 'password', 1, 1),
    ('jane', 'password', 1, 2),
    ('boss', 'password', 2, 3);
END
