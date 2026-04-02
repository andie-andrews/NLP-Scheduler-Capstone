CREATE TABLE [dbo].[ScheduleEmployees]
(
    [ScheduleId] INT NOT NULL,
    [EmployeeId] INT NOT NULL,

    CONSTRAINT [PK_ScheduleEmployees]
        PRIMARY KEY (ScheduleId, EmployeeId),

    CONSTRAINT [FK_ScheduleEmployees_Schedules]
        FOREIGN KEY (ScheduleId) REFERENCES Schedules(Id),

    CONSTRAINT [FK_ScheduleEmployees_Employees]
        FOREIGN KEY (EmployeeId) REFERENCES Employees(Id)
);