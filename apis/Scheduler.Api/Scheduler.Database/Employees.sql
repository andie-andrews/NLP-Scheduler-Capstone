CREATE TABLE [dbo].[Employees]
(
    [Id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [FirstName] NVARCHAR(100) NOT NULL,
    [LastName] NVARCHAR(100) NOT NULL,
    [RoleId] TINYINT NOT NULL,

    CONSTRAINT [FK_Employees_Roles]
        FOREIGN KEY (RoleId) REFERENCES Roles(Id)
);