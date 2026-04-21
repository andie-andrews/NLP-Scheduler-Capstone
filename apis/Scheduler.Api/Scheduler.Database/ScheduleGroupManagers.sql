CREATE TABLE [dbo].[ScheduleGroupManagers]
(
    [ScheduleGroupId] INT NOT NULL,
    [ManagerId] INT NOT NULL,

    CONSTRAINT [PK_ScheduleGroupManagers]
        PRIMARY KEY (ScheduleGroupId, ManagerId),

    CONSTRAINT [FK_ScheduleGroupManagers_ScheduleGroups]
        FOREIGN KEY (ScheduleGroupId) REFERENCES ScheduleGroups(Id),

    CONSTRAINT [FK_ScheduleGroupManagers_Employees]
        FOREIGN KEY (ManagerId) REFERENCES Employees(Id)
);