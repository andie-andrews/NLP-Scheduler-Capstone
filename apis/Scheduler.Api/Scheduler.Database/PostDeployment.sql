-- Insert initial data into the database

-- Roles
IF NOT EXISTS (SELECT 1 FROM Roles)
BEGIN
    INSERT INTO Roles (Id, Name)
    VALUES
        (1, 'Employee'),
        (2, 'Supervisor');
END

-- Employees
IF NOT EXISTS (SELECT 1 FROM Employees WHERE Email = 'boss.man@scheduler.local')
BEGIN
    INSERT INTO Employees (FirstName, LastName, Email, RoleId)
    VALUES ('Boss', 'Man', 'boss.man@scheduler.local', 2);
END


