CREATE TABLE [dbo].[Shifts]
(
    [Id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [ScheduleGroupId] INT NOT NULL,
    [EmployeeId] INT NOT NULL,
    [Start] DATETIME2 NOT NULL,
    [DurationHours] INT NOT NULL,

    CONSTRAINT [FK_Shifts_ScheduleGroups]
        FOREIGN KEY (ScheduleGroupId) REFERENCES ScheduleGroups(Id),

    CONSTRAINT [FK_Shifts_Employees]
        FOREIGN KEY (EmployeeId) REFERENCES Employees(Id)
);