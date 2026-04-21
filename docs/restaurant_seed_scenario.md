# AI Assistant Demo Workflow

## Seed script location

`apis/Scheduler.Api/Scheduler.Database/Seed.RestaurantScenario.sql`

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
sqlcmd -S .\\SQLSERVER -d SchedulerDb -E -i apis/Scheduler.Api/Scheduler.Database/Seed.RestaurantScenario.sql
```

If your SQL Server instance name is different, replace `.\\SQLSERVER` with your instance.

### Seeded demo users

All seeded users have password `password`:

- `boss1` (Supervisor)
- `olivia.tray`
- `emma.welcome`
- `mia.prep`
- `noah.saute`
- `kai.grill`
- `luca.shaker`

---

## AI Assistant Demo Workflow

Use the prompts below during demos to illustrate core scheduling workflows.

### 1) Create a single shift (one employee)

**Goal:** Show one-off shift creation for one person.

Example prompt:

```text
Create a shift for Olivia Tray tomorrow from 9:00 AM to 5:00 PM on the Server schedule.
```

Alternative prompt:

```text
Schedule Emma Welcome for Hostesses on Tuesday 4 PM to 10 PM.
```

---

### 2) Create shifts for this week and next week (Monday–Friday range)

**Goal:** Show batch/range scheduling for coverage across weekdays.

Example prompt:

```text
Create shifts Monday through Friday for next week for Olivia Tray, 11:00 AM to 7:00 PM on Servers.
```

Alternative prompt with multiple employees:

TODO: THIS IS NOT SUPPORTED YET

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

### 4) Manager asks to see employee schedules

**Goal:** Show manager reporting and lookup.

Example manager prompts:

```text
Show me Olivia Tray's schedule this week.
```

```text
Show next week's shifts for each Luca Shaker.
```

---

### 5) Employee login + self-service schedule and hours

**Goal:** Show employee-facing access where a staff member signs in and checks their own schedule and total hours.

Step B - Ask "what is my next shift?":

```text
When is my next shift?
```

Step C - Ask for this week's total hours:

```text
How many hours am I scheduled for this week?
```

Step D - Ask for next week's total hours:

```text
How many hours am I scheduled for next week?
```

Optional follow-up:

```text
List all of my shifts for this week.
```

```text
List all of my shifts for next week.
```

---

### 6) Reassign shift from one employee to another

**Goal:** Show reassign works for employees on the same schedule.

Assuming the following:
- you have a shift assigned to Lance Dall on a Tuesday
- you want to reassign the shift to Andie Andrews
- and they are both on the same schedule
then:

```text
reassign Lance Dall's tuesday shift to Andie Andrews
```

should result in the shift being reassigned to Andie.
---

## Suggested end-to-end demo order

1. Run seed script.
2. Create one single shift.
3. Create Monday-Friday shifts for this + next week.
4. Create recurring "every dayOfWeek for next X weeks" shifts.
5. Ask manager-view queries to inspect employee/schedule coverage.
6. Log in as an employee and run self-service queries:
   - next shift
   - total hours this week
   - total hours next week
