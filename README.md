# ReadReceipts

**Turn your reading history into a receipt.** Upload a Goodreads or StoryGraph export and get back a genuinely receipt-like ticket of your top books, authors, or genres — crinkled paper texture, barcode, and all — fully customizable and exportable as an image.

<!-- Add a screenshot before sharing this README: save one as docs/screenshot.png,
     then uncomment the line below.
![ReadReceipts screenshot](docs/screenshot.png)
-->


## What it is

[Receiptify](https://receiptify.herokuapp.com/) turned Spotify listening history into a nostalgic paper receipt. ReadReceipts does the same for readers: point it at your Goodreads or StoryGraph library export and it renders your reading habits — top-rated books, most-read authors, favorite genres — as a printable, shareable ticket, with the reading period, ranking, and order all in your control.

## Features

- **Upload** a Goodreads or StoryGraph CSV export — the format is auto-detected.
- **One live workspace**, no multi-step wizard. Every control updates the receipt instantly:
  - **Metric** — Top Books, Top Authors, or Top Genres
  - **Time period** — Last Month, Last 6 Months, Last Year, or All Time
  - **Length** — Top 3, 5, or 10
  - **Font** — Classic (monospace ticket font) or Internationally Compatible (system sans-serif)
  - **Reorder** — pick any item's rank from a dropdown to move it to that position, instantly, client-side
- **Export** — download the receipt as a PNG, open it full-size in a new tab, or print it
- A receipt that actually looks like a receipt: procedurally generated crumpled-paper texture, dashed tear lines, order number, QTY/ITEM/AMT columns, barcode, and a card-slip footer

## Quick start (local)

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000**. A ready-to-use `sample_library.csv` is included if you want to try it without exporting your own data.

## Usage

1. On the upload page, choose your CSV export, optionally enter your name (it personalizes the receipt), and submit.
2. You land directly on the receipt workspace. Adjust Metric / Time Period / Length / Font on the right — the ticket on the left updates immediately.
3. Use the rank dropdowns to move any item to a different position in the list.
4. Download the receipt as an image, view it full-size in a new tab, or print it.

### CSV requirements

**Goodreads** exports (My Books → Tools → Import and Export) need: `Title`, `Author`, `My Rating`, `Number of Pages`, `Date Started`, `Date Read`, `Exclusive Shelf`, and `Genre` or `Bookshelves`.

**StoryGraph** exports (Profile → Manage Profile → Export StoryGraph Data) need: `Title`, `Authors`, `Star Rating`, `Read Status`, `Last Date Read` (or `Date Added`), and `Tags` or `Moods`. StoryGraph exports don't include page counts or a start date, so pages and reading duration show as 0 for that platform.

Only rows marked as read (`Exclusive Shelf` / `Read Status` = "read") are included.

## Tech stack

- **Backend**: Flask, Pandas
- **Frontend**: Jinja2 templates, vanilla CSS/JS — no build step, no frontend framework
- **Image export**: [html2canvas](https://html2canvas.hertzen.com/) (loaded from a CDN)

## Project structure

```
ReadReceipts/
├── app.py               # Flask app: CSV parsing, filtering/sorting, the /workspace route
├── requirements.txt
├── sample_library.csv    # Sample Goodreads-format data for trying the app
├── static/
│   ├── style.css          # All styling, including the receipt/ticket reproduction
│   ├── workspace.js       # Client-side reorder, font toggle, download/view actions
│   └── images/bg.jpg
├── templates/
│   ├── upload.html         # Upload page
│   └── workspace.html      # Live receipt + customization controls
└── uploads/                # Uploaded CSVs land here temporarily (gitignored)
```

## Notes / limitations

- Uploaded CSVs and reading data are held in the Flask session and a temporary file on disk — there's no database or user accounts, so nothing persists between browsers/devices or restarts.
- StoryGraph exports don't carry page counts or a reading-start date, so "pages" and "days to read" show as 0 for books sourced from StoryGraph.
- The bundled dev server (`python app.py`) is for local/development use only — it's not meant to be exposed on the public internet as-is.
