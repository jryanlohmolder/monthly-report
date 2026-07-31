# monthly-report

A Python script that runs automatically every first Saturday of the month via GitHub Actions. It emails an HTML report of upcoming birthdays and anniversaries within a 30-day window, renders a calendar view, and creates corresponding tasks in Google Tasks.

---

## How It Works

On the first Saturday of each month, GitHub Actions:
1. Loads dates from a private YAML file (stored as a GitHub Secret)
2. Filters entries falling within the next 30 days
3. Generates an HTML report and calendar
4. Sends the report to a specified email address
5. Creates tasks in Google Tasks for each upcoming date

---

## Example Report

The email arrives with the upcoming dates listed and a calendar view below. Here's what a report for an October window looks like:

---

# Monthly Report

## Upcoming Dates

- **Sunny Baudelaire** (birthday) - 10/04
- **Count Olaf's Theater Performance** (event) - 10/11
- **Uncle Monty** (work anniversary) - 10/19
- **Aunt Josephine's Annual Tea Party** (event) - 11/02

---

**October**

| Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|-----|-----|-----|-----|-----|-----|-----|
|     |  1  |  2  |  3  | **4** 🎂 |  5  |  6  |
|  7  |  8  |  9  | 10  | **11** 🎭 | 12  | 13  |
| 14  | 15  | 16  | 17  | 18  | **19** 🎉 | 20  |
| 21  | 22  | 23  | 24  | 25  | 26  | 27  |
| 28  | 29  | 30  | 31  |     |     |     |

**November** *(partial)*

| Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|-----|-----|-----|-----|-----|-----|-----|
|     |     |     |     |  1  | **2** 🍵 |  3  |

---

## dates.yaml Format

Dates are stored in a YAML file with the following structure. The year in each entry is ignored — the script always looks at the current or upcoming occurrence.

```yaml
# important, annual dates

- name: "Sunny Baudelaire"
  date: "2001-10-04"
  type: "birthday"

- name: "Count Olaf's Theater Performance"
  date: "2001-10-11"
  type: "event"

- name: "Uncle Monty"
  date: "1985-10-19"
  type: "work anniversary"

- name: "Aunt Josephine's Annual Tea Party"
  date: "2001-11-02"
  type: "event"
```

---

## Setup

Requires a Gmail account with an App Password, a Google Cloud project with the Tasks API enabled, and OAuth 2.0 credentials. Secrets are stored in GitHub Actions and never committed to the repository.

```bash
git clone https://github.com/jryanlohmolder/monthly-report.git
cd monthly-report
pip install -r requirements.txt
```

---

## Schedule

The workflow runs every **Saturday at midnight ET**. The script checks whether it is the first Saturday of the month and exits early if not — so it only sends on the first Saturday.
