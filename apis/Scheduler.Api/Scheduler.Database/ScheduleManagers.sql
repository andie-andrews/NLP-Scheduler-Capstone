CREATE TABLE [dbo].[ScheduleManagers]
(
    [ScheduleId] INT NOT NULL,
    [ManagerId] INT NOT NULL,

    CONSTRAINT [PK_ScheduleManagers]
        PRIMARY KEY (ScheduleId, ManagerId),

    CONSTRAINT [FK_ScheduleManagers_Schedules]
        FOREIGN KEY (ScheduleId) REFERENCES Schedules(Id),

    CONSTRAINT [FK_ScheduleManagers_Employees]
        FOREIGN KEY (ManagerId) REFERENCES Employees(Id)
);