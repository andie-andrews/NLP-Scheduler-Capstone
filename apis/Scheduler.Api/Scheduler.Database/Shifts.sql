CREATE TABLE [dbo].[Shifts]
(
    [Id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [ScheduleId] INT NOT NULL,
    [EmployeeId] INT NOT NULL,
    [Start] DATETIME2 NOT NULL,
    [DurationHours] INT NOT NULL,

    CONSTRAINT [FK_Shifts_Schedules]
        FOREIGN KEY (ScheduleId) REFERENCES Schedules(Id),

    CONSTRAINT [FK_Shifts_Employees]
        FOREIGN KEY (EmployeeId) REFERENCES Employees(Id)
);