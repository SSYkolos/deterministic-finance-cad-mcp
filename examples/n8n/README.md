# n8n: bank statement email → balance check → Google Sheets

[`bank-statement-to-sheets.json`](bank-statement-to-sheets.json) watches a mailbox for bank statement
attachments (MT940, camt.053, BAI2, CODA, or a ZIP of them), checks each one with the
[Bank Statement Reconciler](https://rapidapi.com/SSYkolos/api/bank-statement-reconciler1)
(opening + credits − debits = closing, to the cent), writes one row per statement to Google Sheets,
and emails you when a statement is not `VERIFIED`.

```
IMAP trigger → keep statement attachments → Reconciler (RapidAPI) → one row per statement ─┬→ Google Sheets
                                                                                            └→ not VERIFIED? → alert email
```

## Set up (about 10 minutes)

1. In n8n: **Workflows → Import from file** and pick `bank-statement-to-sheets.json`.
2. **Statement email (IMAP)**: create an IMAP credential for the mailbox your bank (or your bookkeeping
   inbox) sends statements to. For Gmail use `imap.gmail.com` with an app password.
3. **Reconcile (RapidAPI)**: create a **Header Auth** credential with name `X-RapidAPI-Key` and your
   key as the value. A free key is on the
   [API page](https://rapidapi.com/SSYkolos/api/bank-statement-reconciler1) (Subscribe → Basic).
   The key lives only in the n8n credential, never in the workflow JSON.
4. **Append to Google Sheets**: connect your Google account, paste the sheet's URL and pick the tab.
   The columns are created from the first row the workflow writes.
5. **Alert email**: pick an SMTP credential and put your address in *To*.
6. Send yourself a statement file and activate the workflow.

## What ends up in the sheet

`checked_at, email_subject, file_name, verdict, format, account, currency, statement_ref, opening_balance,
total_credits, total_debits, calculated_closing, bank_closing, discrepancy, transactions, note`

- `VERIFIED`: the numbers add up.
- `DISCREPANCY`: they don't (or a statement is missing between two files); `discrepancy` has the difference.
- `UNVERIFIABLE`: the file has no closing balance to check against.
- `ERROR`: the API could not read the file; `note` says why.

Attachments whose names don't look like statements (`.sta .mt940 .940 .txt .xml .053 .camt .bai .bai2 .cod .coda .zip`)
are skipped. Change the pattern in the *Statement attachments* node if your bank uses another extension.

## Try it without n8n

The free browser demo runs the same check on one file:
[ssykolos.github.io/tools/bank-statement-balance-check](https://ssykolos.github.io/tools/bank-statement-balance-check/?ref=github_n8n).

Tested by importing into n8n 2.44 and running the nodes against the demo endpoint.
