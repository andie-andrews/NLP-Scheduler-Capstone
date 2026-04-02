-- Insert initial data into the database

-- Roles
IF NOT EXISTS (SELECT 1 FROM Roles)
BEGIN
    INSERT INTO Roles (Id, Name)
    VALUES
        (1, 'Employee'),
        (2, 'Supervisor');
END

-- Schedules
INSERT INTO Schedules (Name, StartDate, EndDate)
VALUES ('Week 1', GETDATE(), DATEADD(DAY, 7, GETDATE()));

-- Employees
INSERT INTO Employees (FirstName, LastName, RoleId)
VALUES
('John', 'Doe', 1),
('Jane', 'Smith', 1),
('Boss', 'Man', 2);

-- Assign employees to schedule
INSERT INTO ScheduleEmployees (ScheduleId, EmployeeId)
VALUES
(1, 1),
(1, 2);

-- Assign manager
INSERT INTO ScheduleManagers (ScheduleId, ManagerId)
VALUES
(1, 3);

-- Shifts
INSERT INTO Shifts (ScheduleId, EmployeeId, Start, DurationHours)
VALUES
(1, 1, DATEADD(HOUR, 8, GETDATE()), 8);