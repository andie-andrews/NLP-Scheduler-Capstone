# Restaurant Seed Scenario + AI Assistant Demo Workflow

## Seed script location

`apis\Scheduler.Api\Scheduler.Database/Seed.RestaurantScenario.sql`

---

## Manual run options

### Option 1: SQL Server Management Studio (SSMS)

For manual execution, you can run either:
- `Seed.RestaurantScenario.sql` directly.

Steps:
1. Open the script you want to run.
2. Connect to your SQL Server instance.
3. Select the `SchedulerDb` database.
4. Execute the script.

### Option 2: sqlcmd
```bash
sqlcmd -S .\\SQLSERVER -d SchedulerDb -E -i apis/Scheduler.Api/Scheduler.Api/Database/Seed.RestaurantScenario.sql
```

If your SQL Server instance name is different, replace `.\\SQLSERVER` with your instance.

---

## AI Assistant Demo Workflow

Use the prompts below during demos to illustrate core scheduling workflows.

### 1) Create a single shift (one employee)

**Goal:** Show one-off shift creation for one person.

Example prompt:

```text
Create a shift for Kai Grill on Tuesday from 9:00 AM to 5:00 PM on the Kitchen schedule.
```

Alternative prompt:

```text
Schedule Emma Welcome for Hostesses tomorrow 4 PM to 10 PM.
```

---

### 2) Create shifts for this week and next week (Monday–Friday range)

**Goal:** Show batch/range scheduling for coverage across weekdays.

Example prompt:

```text
Create shifts Monday through Friday for this week and next week for Olivia Tray, 11:00 AM to 7:00 PM on Servers.
```

Alternative prompt with multiple employees:

```text
Schedule Mia Prep, Noah Saute, and Kai Grill on Kitchen for Monday-Friday this week and next week, 8 AM to 4 PM.
```

---

### 3) Create recurring shifts: Every {dayOfWeek} for next X weeks

**Goal:** Show recurring pattern creation.

Example prompt:

```text
Create shifts for Luca Shaker every Thursday for the next 6 weeks from 5:00 PM to 11:00 PM on Bartenders.
```

Template prompt:

```text
Create shifts for {EmployeeName} every {dayOfWeek} for the next {X} weeks from {startTime} to {endTime} on {ScheduleName}.
```

(If you typed `dayOfweed`, use `dayOfWeek` in the actual prompt.)

---

### 4) Ensure every employee gets scheduled

**Goal:** Show coverage validation and fill-gaps workflow.

Step 1 prompt:

```text
Show me which seeded employees do not have shifts scheduled for this week.
```

Step 2 prompt (fill missing):

```text
Create weekday shifts for all employees with no shifts this week, matching their schedule, 9:00 AM to 5:00 PM.
```

---

### 5) Manager asks to see employee schedules

**Goal:** Show manager reporting and lookup.

Example manager prompts:

```text
Show me all schedules for employee Olivia Tray.
```

```text
As manager, list this week's shifts for Kitchen employees.
```

```text
Show next week's shifts for each employee in Bartenders.
```

---

## Suggested end-to-end demo order

1. Run seed script.
2. Create one single shift.
3. Create Monday-Friday shifts for this + next week.
4. Create recurring "every dayOfWeek for next X weeks" shifts.
5. Ask who is unscheduled and auto-fill missing shifts.
6. Ask manager-view queries to inspect employee/schedule coverage.
