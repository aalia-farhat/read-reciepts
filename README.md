# ReadReceipts

Web application inspired by [Receiptify](https://receiptify.herokuapp.com/). Generates receipts that list out a user's top books, authors, or genres from their Goodreads or StoryGraph reading history — for the last month, 6 months, year, or all time.

<!-- Add a screenshot before sharing this README: save one as docs/screenshot.png,
     then uncomment the line below.
![ReadReceipts screenshot](docs/screenshot.png)
-->

## Running the App Locally

This app runs on Python (Flask). Clone the repository and install its dependencies:

```
$ pip install -r requirements.txt
```

Once installed, run its `app.py` file:

```
$ python app.py
```

Then open `http://localhost:5000` in a browser. A sample library (`sample_library.csv`) is included in the repo if you want to try it out right away, without exporting your own reading history first.

## Using your own reading history

Export your library as a CSV and upload it on the home page — the format is detected automatically:

- **Goodreads**: My Books → Tools → Import and Export → download your library.
- **StoryGraph**: Profile icon → Manage Profile → Export StoryGraph Data → Export.

Only books marked "read" are included.

## Features

- Upload a Goodreads or StoryGraph CSV export, no account or API keys needed
- One live page — Metric (Top Books / Authors / Genres), Time Period, Length, and Font all update the receipt instantly, no page reloads
- Reorder any item to any position with a dropdown, right on the receipt
- Download the receipt as a PNG, open it full-size in a new tab, or print it
- A receipt that actually looks like a receipt: procedurally generated crumpled-paper texture, dashed tear lines, order number, QTY/ITEM/AMT columns, and a barcode

## Tech stack

Flask + Pandas on the backend; Jinja2 templates with vanilla CSS/JS on the frontend (no build step, no frontend framework). Image export via [html2canvas](https://html2canvas.hertzen.com/).

## Notes

- Uploaded CSVs and reading data are held in the Flask session and a temporary file on disk — there's no database or user accounts, so nothing persists between browsers/devices or restarts.
- StoryGraph exports don't carry page counts or a reading-start date, so "pages" and "days to read" show as 0 for books sourced from StoryGraph.
