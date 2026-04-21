CREATE TABLE [dbo].[ScheduleGroupEmployees]
(
    [ScheduleGroupId] INT NOT NULL,
    [EmployeeId] INT NOT NULL,

    CONSTRAINT [PK_ScheduleGroupEmployees]
        PRIMARY KEY (ScheduleGroupId, EmployeeId),

    CONSTRAINT [FK_ScheduleGroupEmployees_ScheduleGroups]
        FOREIGN KEY (ScheduleGroupId) REFERENCES ScheduleGroups(Id),

    CONSTRAINT [FK_ScheduleGroupEmployees_Employees]
        FOREIGN KEY (EmployeeId) REFERENCES Employees(Id)
);