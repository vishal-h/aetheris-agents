# Exporting Payroll Sheet to Shared Drive (Google Apps Script)

Automates the CSV export from Google Sheets to the shared Drive folder
`payroll/payslips/` without downloading to a local machine. HR triggers it
from a menu inside the sheet.

---

## Naming convention

| Thing | Convention | Example |
|-------|-----------|---------|
| Sheet file | `YYYY-payroll` | `2627-payroll` |
| Tab name | `YYYY-MM` | `2026-04` |
| Drive folder (under `payslips/`) | `YYYY-MM` (same as tab name) | `2026-04` |
| CSV filename | `payroll.csv` | `payroll.csv` |
| Full path in Drive | `payroll/payslips/YYYY-MM/payroll.csv` | `payroll/payslips/2026-04/payroll.csv` |

The tab name is the single source of truth — the script reads it directly
and uses it as both the subfolder name and the basis for the CSV path.
No parsing or translation needed.

> **Existing folders:** the folder `202604-april` was created manually during
> initial testing and predates this convention. Going forward all month folders
> follow `YYYY-MM`.

---

## Prerequisites

- Edit access to the Google Sheet (`2627-payroll` or equivalent)
- The shared Drive named **payroll** already exists and contains a `payslips/`
  folder
- You know the folder ID of `payslips/` (see step 1 below)

---

## Step 1 — Get the `payslips/` folder ID

Open the `payslips/` folder inside the **payroll** shared Drive. The URL
looks like:

```
https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0J
```

The folder ID is the last segment: `1A2B3C4D5E6F7G8H9I0J`. Copy it — you'll
need it in step 4.

---

## Step 2 — Open the Apps Script editor

1. Open the payroll Google Sheet (`2627-payroll`).
2. Click **Extensions → Apps Script** in the top menu.
3. A new browser tab opens with the script editor. The default file is `Code.gs`.
4. Delete any placeholder code already in the editor.

---

## Step 3 — Paste the script

Copy the full script below and paste it into `Code.gs`:

```javascript
// ID of the payroll/payslips/ folder in the shared Drive.
// Find it in the folder's URL: drive.google.com/drive/folders/<ID>
var PAYSLIPS_FOLDER_ID = "PASTE_YOUR_FOLDER_ID_HERE";

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("Payroll")
    .addItem("Export CSV to Drive", "exportAsCSV")
    .addToUi();
}

function exportAsCSV() {
  var ss    = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getActiveSheet();
  var tabName = sheet.getName();   // e.g. "2026-04"

  // Validate tab name looks like YYYY-MM
  if (!/^\d{4}-\d{2}$/.test(tabName)) {
    SpreadsheetApp.getUi().alert(
      'Unexpected tab name "' + tabName + '".\n' +
      'Rename the tab to YYYY-MM (e.g. 2026-04) before exporting.'
    );
    return;
  }

  // Locate or create payslips/<tab-name>/ folder
  var payslipsFolder = DriveApp.getFolderById(PAYSLIPS_FOLDER_ID);
  var monthFolder;
  var existing = payslipsFolder.getFoldersByName(tabName);
  if (existing.hasNext()) {
    monthFolder = existing.next();
  } else {
    monthFolder = payslipsFolder.createFolder(tabName);
  }

  // Build CSV from the active tab
  var data = sheet.getDataRange().getValues();
  var csv  = data.map(function(row) {
    return row.map(function(cell) {
      var s = (cell instanceof Date)
        ? Utilities.formatDate(cell, Session.getScriptTimeZone(), "yyyy-MM-dd")
        : String(cell);
      if (s.indexOf(",") !== -1 || s.indexOf('"') !== -1 || s.indexOf("\n") !== -1) {
        s = '"' + s.replace(/"/g, '""') + '"';
      }
      return s;
    }).join(",");
  }).join("\n");

  // Write payroll.csv — overwrite if it already exists
  var existingFiles = monthFolder.getFilesByName("payroll.csv");
  if (existingFiles.hasNext()) {
    existingFiles.next().setContent(csv);
    SpreadsheetApp.getUi().alert("Updated: payslips/" + tabName + "/payroll.csv");
  } else {
    monthFolder.createFile("payroll.csv", csv, MimeType.PLAIN_TEXT);
    SpreadsheetApp.getUi().alert("Created: payslips/" + tabName + "/payroll.csv");
  }
}
```

---

## Step 4 — Set the folder ID

At the top of the script, replace:

```javascript
var PAYSLIPS_FOLDER_ID = "PASTE_YOUR_FOLDER_ID_HERE";
```

with the ID you copied in step 1:

```javascript
var PAYSLIPS_FOLDER_ID = "1A2B3C4D5E6F7G8H9I0J";
```

---

## Step 5 — Save and authorise

1. Click the **Save** icon (or `Ctrl+S` / `Cmd+S`).
2. In the function dropdown, select `onOpen` and click **▶ Run**.
3. Google will ask you to authorise the script. Click **Review permissions**,
   choose your account, then click **Allow**.

   The permissions requested are:
   - **See and edit spreadsheets** — to read the payroll data.
   - **See, edit, create and delete files in Google Drive** — to create the
     month subfolder and write `payroll.csv`.

4. You only need to authorise once.

---

## Step 6 — Run the export

1. Go back to the Google Sheet tab and **reload the page**.
2. Make sure the tab you want to export is the **active tab**
   (e.g. click the `2026-05` tab).
3. Click **Payroll → Export CSV to Drive**.
4. A confirmation dialog shows the path that was created or updated.
5. The file is now at `payroll/payslips/2026-05/payroll.csv` in the shared
   Drive.

---

## Behaviour notes

| Situation | What happens |
|-----------|-------------|
| Month folder doesn't exist yet | Created automatically under `payslips/` |
| Month folder already exists | Used as-is, no duplicate created |
| `payroll.csv` already exists in the folder | Overwritten in place |
| Tab name is not `YYYY-MM` | Script aborts with a clear error message |
| Cell contains a comma or quote | Correctly quoted per CSV convention |
| Cell is a date value | Formatted as `yyyy-MM-dd`, not locale-dependent |

---

## Optional — run on a time trigger (no manual click)

If you want the export to happen automatically (e.g. on the 1st of every
month):

1. In the Apps Script editor, click **Triggers** (clock icon on the left
   sidebar).
2. Click **+ Add Trigger** (bottom right).
3. Set:
   - **Function:** `exportAsCSV`
   - **Event source:** Time-driven
   - **Type:** Month timer
   - **Day:** 1
   - **Time:** 8am–9am (or whatever suits your payroll cycle)
4. Click **Save**.

Note: when run on a trigger, `getActiveSheet()` returns the first tab in the
sheet, not a user-selected one. If you use a trigger, set the active tab
programmatically or switch to `getSheetByName()` with a fixed tab name.

---

## Feeding the CSV into the payslip pipeline

Once the CSV is in Drive the Python scripts still need a local path. Two
options:

- **Manual:** HR downloads `payroll.csv` from `payslips/YYYY-MM/` and places
  it at `data/sample_payroll.csv` before running the agent.
- **Automated:** Use the `drive` use-case agent (see `drive/` in this repo)
  to fetch `payroll.csv` from the month folder by ID and write it to `data/`
  before the payslip agent runs.
