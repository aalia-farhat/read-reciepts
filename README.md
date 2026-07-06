# ReadReceipts

**ReadReceipts** is a Flask web app inspired by Receiptify, but for books. Upload a Goodreads or StoryGraph CSV export and get a printable, thermal-receipt-style summary of your reading habits — fully customizable and exportable as an image.

## Features

- **Upload** a Goodreads or StoryGraph CSV export (auto-detected).
- **One live workspace page** — no multi-step wizard. Every control updates the receipt immediately:
  - **Metric**: Top Books, Top Authors, or Top Genres
  - **Time Period**: Last Month, Last 6 Months, Last Year, or All Time (rolling windows from today)
  - **Length**: Top 3, 5, or 10
  - **Font**: Classic (monospace) or Internationally Compatible (system sans-serif)
  - **Reorder**: pick any item's rank from a dropdown to move it to that position — instantly, client-side
- **Export**: Download the receipt as a PNG, open it in a new tab, or print it.
- Bookstore-inspired visual design with a real "thermal receipt" reproduction (order number, QTY/ITEM/AMT columns, barcode, card footer).

## Getting started

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000**.

## Usage

1. On the upload page, choose a CSV exported from Goodreads or StoryGraph (see below), optionally enter your name (it's used to personalize the receipt), and submit.
2. You land directly on the receipt workspace. Adjust Metric / Time Period / Length / Font on the right — the ticket on the left updates immediately.
3. Use the rank dropdowns to move any item to a different position in the list.
4. Download the receipt as an image, view it full-size in a new tab, or print it.

A ready-to-use `sample_library.csv` is included if you want to try the app without exporting your own data.

### CSV requirements

**Goodreads** exports (My Books → Tools → Import and Export) need: `Title`, `Author`, `My Rating`, `Number of Pages`, `Date Started`, `Date Read`, `Exclusive Shelf`, and `Genre` or `Bookshelves`.

**StoryGraph** exports (Profile → Manage Profile → Export StoryGraph Data) need: `Title`, `Authors`, `Star Rating`, `Read Status`, `Last Date Read` (or `Date Added`), and `Tags` or `Moods`. StoryGraph exports don't include page counts or a start date, so pages and reading duration will show as 0 for that platform.

Only rows marked as read (`Exclusive Shelf` / `Read Status` = "read") are included.

## Project structure

```
ReadReceipts/
├── app.py                  # Flask app: CSV parsing, filtering/sorting, the /workspace route
├── requirements.txt
├── sample_library.csv       # Sample Goodreads-format data for trying the app
├── static/
│   ├── style.css            # All styling, including the receipt/ticket reproduction
│   ├── workspace.js         # Client-side reorder, font toggle, download/view actions
│   └── images/bg.jpg
├── templates/
│   ├── upload.html           # Upload page
│   └── workspace.html        # Live receipt + customization controls
└── uploads/                  # Uploaded CSVs land here temporarily (gitignored)
```

## Tech stack

- **Backend**: Flask, Pandas
- **Frontend**: Jinja2 templates, vanilla CSS/JS (no build step, no frontend framework)
- **Image export**: [html2canvas](https://html2canvas.hertzen.com/) (loaded from a CDN)

## Notes / limitations

- Uploaded CSVs and reading data are held in the Flask session and a temporary file on disk — there's no database or user accounts, so nothing persists between browsers/devices.
- The dev server (`python app.py`) is for local use only; put a real WSGI server (gunicorn, waitress, etc.) in front of it for anything beyond local testing.
- StoryGraph exports don't carry page counts or a reading-start date, so the "pages" and "days to read" figures will be 0 for books sourced from StoryGraph.
