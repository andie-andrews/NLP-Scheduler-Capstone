CREATE TABLE [dbo].[Users]
(
    [Id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [Username] NVARCHAR(100) NOT NULL UNIQUE,
    [Password] NVARCHAR(100) NOT NULL,
    [Role] TINYINT NOT NULL,
    [EmployeeId] INT NOT NULL,

    CONSTRAINT [FK_Users_Employees]
        FOREIGN KEY (EmployeeId) REFERENCES Employees(Id)
);