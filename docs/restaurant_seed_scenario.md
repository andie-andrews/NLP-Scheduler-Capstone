# Restaurant Seed Scenario + AI Assistant Demo Workflow

This document explains how to seed `SchedulerDb` with a restaurant staffing scenario and how to demo AI assistant scheduling workflows.

## What gets seeded

### Schedules
- Kitchen
- Bartenders
- Servers
- Hostesses
- Managers
- Busers

### Employees and manager rules
- **Boss Man** is enforced as the **only Supervisor** in the seeded set.
- Boss Man is assigned as manager for **all schedules**.
- **3 employees are seeded for each non-manager schedule**:
  - Kitchen
  - Bartenders
  - Servers
  - Hostesses
  - Busers

### Users
- A user is upserted for each seeded employee.
- Username = employee first name.
- Password = employee first name.
- Role = Employee for all seeded users except Boss.
- Boss user is upserted as:
  - Username: `Boss`
  - Password: `Password`
  - Role: Supervisor

> The seed script uses `MERGE`-based upserts and delete-sync logic for seeded records, so it can be re-run safely and will update/replace seeded rows.

---

## Seed script location

`apis/Scheduler.Api/Scheduler.Api/Database/Seed.RestaurantScenario.sql`

---

## DACPAC pre-deploy usage

This script is intended to run during pre-deploy in a SQL project/DACPAC pipeline.

Example in a SQL project pre-deploy script:

```sql
:r .\Database\Seed.RestaurantScenario.sql
```

If this repository later adds a `.sqlproj`, include the script in the pre-deployment step so seeded data is kept in sync on deploy.

---

## Manual run options

### Option 1: SQL Server Management Studio (SSMS)
1. Open `Seed.RestaurantScenario.sql`.
2. Connect to your SQL Server instance.
3. Select the `SchedulerDb` database.
4. Execute the script.

### Option 2: sqlcmd
```bash
sqlcmd -S .\\SQLSERVER2014 -d SchedulerDb -E -i apis/Scheduler.Api/Scheduler.Api/Database/Seed.RestaurantScenario.sql
```

If your SQL Server instance name is different, replace `.\\SQLSERVER2014` with your instance.

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
