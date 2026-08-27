from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

PERIOD_LABELS = {
    'month': 'LAST MONTH',
    'six_months': 'LAST 6 MONTHS',
    'year': 'LAST YEAR',
    'all': 'ALL TIME',
}

METRIC_LABELS = {
    'books': 'Top Books',
    'authors': 'Top Authors',
    'genres': 'Top Genres',
}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_path(filename):
    """Get safe upload path"""
    return os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))


def detect_platform(df):
    """Detect whether CSV is from Goodreads or StoryGraph"""
    columns = set(df.columns)

    goodreads_indicators = {'Title', 'Author', 'My Rating', 'Exclusive Shelf', 'Date Read'}
    storygraph_indicators = {'Title', 'Authors', 'Star Rating', 'Read Status', 'Last Date Read'}

    if goodreads_indicators.issubset(columns):
        return 'goodreads'
    elif storygraph_indicators.issubset(columns):
        return 'storygraph'
    else:
        return 'unknown'


def normalize_csv(df, platform):
    """
    Normalize CSV from either Goodreads or StoryGraph to internal schema
    Returns normalized DataFrame with columns:
    - title, author, rating, pages, date_started, date_read, read_status, genre_or_tags
    """
    normalized = pd.DataFrame()

    try:
        if platform == 'goodreads':
            normalized['title'] = df.get('Title', '').astype(str)
            normalized['author'] = df.get('Author', 'Unknown').astype(str)

            if 'My Rating' in df.columns:
                normalized['rating'] = pd.to_numeric(df['My Rating'], errors='coerce').fillna(0)
            else:
                normalized['rating'] = 0

            if 'Number of Pages' in df.columns:
                normalized['pages'] = pd.to_numeric(df['Number of Pages'], errors='coerce').fillna(0).astype(int)
            else:
                normalized['pages'] = 0

            if 'Date Started' in df.columns:
                normalized['date_started'] = pd.to_datetime(df['Date Started'], errors='coerce')
            else:
                normalized['date_started'] = pd.NaT

            if 'Date Read' in df.columns:
                normalized['date_read'] = pd.to_datetime(df['Date Read'], errors='coerce')
            else:
                normalized['date_read'] = pd.NaT

            if 'Exclusive Shelf' in df.columns:
                normalized['read_status'] = df['Exclusive Shelf'].astype(str).str.lower().str.strip()
            else:
                normalized['read_status'] = 'unknown'

            if 'Bookshelves' in df.columns:
                normalized['genre_or_tags'] = df['Bookshelves'].astype(str)
            elif 'Genre' in df.columns:
                normalized['genre_or_tags'] = df['Genre'].astype(str)
            else:
                normalized['genre_or_tags'] = 'Unknown'

        elif platform == 'storygraph':
            normalized['title'] = df.get('Title', '').astype(str)
            normalized['author'] = df.get('Authors', 'Unknown').astype(str)

            if 'Star Rating' in df.columns:
                normalized['rating'] = pd.to_numeric(df['Star Rating'], errors='coerce').fillna(0)
            else:
                normalized['rating'] = 0

            # StoryGraph exports don't expose page counts or a start date
            normalized['pages'] = 0
            normalized['date_started'] = pd.NaT

            if 'Last Date Read' in df.columns:
                normalized['date_read'] = pd.to_datetime(df['Last Date Read'], errors='coerce')
            elif 'Date Added' in df.columns:
                normalized['date_read'] = pd.to_datetime(df['Date Added'], errors='coerce')
            else:
                normalized['date_read'] = pd.NaT

            if 'Read Status' in df.columns:
                normalized['read_status'] = df['Read Status'].astype(str).str.lower().str.strip()
            else:
                normalized['read_status'] = 'unknown'

            if 'Tags' in df.columns:
                normalized['genre_or_tags'] = df['Tags'].astype(str)
            elif 'Moods' in df.columns:
                normalized['genre_or_tags'] = df['Moods'].astype(str)
            else:
                normalized['genre_or_tags'] = 'Unknown'

        else:
            normalized['title'] = df.get('Title', df.get('title', '')).astype(str) if 'Title' in df.columns or 'title' in df.columns else ''
            normalized['author'] = df.get('Author', df.get('author', 'Unknown')).astype(str) if 'Author' in df.columns or 'author' in df.columns else 'Unknown'
            normalized['rating'] = 0
            normalized['pages'] = 0
            normalized['date_started'] = pd.NaT
            normalized['date_read'] = pd.NaT
            normalized['read_status'] = 'read'
            normalized['genre_or_tags'] = 'Unknown'

        return normalized

    except Exception as e:
        print(f"Error normalizing CSV: {str(e)}")
        raise


def get_read_books(filepath, platform):
    """Read the uploaded CSV and return only the read books, normalized and reindexed"""
    df = pd.read_csv(filepath)
    normalized = normalize_csv(df, platform)
    return normalized[normalized['read_status'] == 'read'].reset_index(drop=True)


def aggregate_authors(books, top_count):
    """Rank authors by number of books read"""
    counts = books['author'].value_counts()
    return [
        {'name': str(name), 'count': int(count)}
        for name, count in counts.head(top_count).items()
    ]


def aggregate_genres(books, top_count):
    """Split comma-separated genre/tag strings and rank by frequency"""
    exploded = (
        books['genre_or_tags']
        .astype(str)
        .str.split(',')
        .explode()
        .str.strip()
    )
    exploded = exploded[(exploded != '') & (exploded.str.lower() != 'unknown')]
    counts = exploded.value_counts()
    return [
        {'name': str(name), 'count': int(count)}
        for name, count in counts.head(top_count).items()
    ]


def compute_receipt(filepath, platform, metric, period, top_count, display_name):
    """Read, filter and shape the uploaded library into ticket-ready data"""
    df = pd.read_csv(filepath)
    normalized = normalize_csv(df, platform)

    books = normalized[normalized['read_status'] == 'read'].copy()
    if books.empty:
        return None

    now = pd.Timestamp.now()
    if period == 'month':
        cutoff = now - pd.DateOffset(months=1)
        books = books[books['date_read'] >= cutoff]
    elif period == 'six_months':
        cutoff = now - pd.DateOffset(months=6)
        books = books[books['date_read'] >= cutoff]
    elif period == 'year':
        cutoff = now - pd.DateOffset(years=1)
        books = books[books['date_read'] >= cutoff]
    # period == 'all': no filter

    if books.empty:
        return {
            'entries': [],
            'metric': metric,
            'metric_label': METRIC_LABELS.get(metric, 'Top Books'),
            'period': period,
            'period_label': PERIOD_LABELS.get(period, 'ALL TIME'),
            'item_count': 0,
            'total': 0,
            'display_name': display_name,
        }

    duration = (books['date_read'] - books['date_started']).dt.days
    books['reading_duration'] = duration.where(duration.notna() & (duration >= 0), 0).fillna(0).astype(int)

    if metric == 'authors':
        rows = aggregate_authors(books, top_count)
        items = [{'kind': 'count', 'name': r['name'], 'amount': r['count']} for r in rows]
        total = sum(r['count'] for r in rows)
    elif metric == 'genres':
        rows = aggregate_genres(books, top_count)
        items = [{'kind': 'count', 'name': r['name'], 'amount': r['count']} for r in rows]
        total = sum(r['count'] for r in rows)
    else:
        metric = 'books'
        sorted_books = books.sort_values(
            by=['rating', 'date_read'],
            ascending=[False, False],
            na_position='last'
        )
        top_books = sorted_books.head(top_count)
        items = []
        for _, row in top_books.iterrows():
            items.append({
                'kind': 'book',
                'title': str(row['title']),
                'author': str(row['author']),
                'rating': float(row['rating']) if pd.notna(row['rating']) else 0,
                'pages': int(row['pages']) if pd.notna(row['pages']) else 0,
                'duration': int(row['reading_duration']) if pd.notna(row['reading_duration']) else 0,
            })
        total = sum(item['pages'] for item in items)

    return {
        'entries': items,
        'metric': metric,
        'metric_label': METRIC_LABELS.get(metric, 'Top Books'),
        'period': period,
        'period_label': PERIOD_LABELS.get(period, 'ALL TIME'),
        'item_count': len(items),
        'total': total,
        'display_name': display_name,
    }


@app.route('/')
def index():
    """Upload Page"""
    if 'uploaded_file' in session:
        try:
            old_path = get_upload_path(session['uploaded_file'])
            if os.path.exists(old_path):
                os.remove(old_path)
        except OSError:
            pass

    session.clear()
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload - Support both Goodreads and StoryGraph"""
    if 'csv_file' not in request.files:
        return render_template('upload.html', error="No file selected. Please upload a CSV file.")

    file = request.files['csv_file']

    if file.filename == '':
        return render_template('upload.html', error="No file selected. Please upload a CSV file.")

    if not allowed_file(file.filename):
        return render_template('upload.html', error="Invalid file type. Please upload a CSV file.")

    try:
        filename = f"upload_{secrets.token_hex(8)}.csv"
        filepath = get_upload_path(filename)
        file.save(filepath)

        try:
            df = pd.read_csv(filepath)
            platform = detect_platform(df)

            if platform == 'unknown':
                os.remove(filepath)
                return render_template('upload.html',
                    error="CSV format not recognized. Please upload a valid Goodreads or StoryGraph export.")

            normalized_df = normalize_csv(df, platform)
            read_books = normalized_df[normalized_df['read_status'] == 'read']

            if read_books.empty:
                os.remove(filepath)
                return render_template('upload.html',
                    error="No completed books found in your library. Please make sure your CSV contains books marked as 'read'.")

            display_name = request.form.get('display_name', '').strip() or 'Reader'

            session['uploaded_file'] = filename
            session['platform'] = platform
            session['display_name'] = display_name
            session['card_last4'] = f"{secrets.randbelow(10000):04d}"
            session['auth_code'] = f"{secrets.randbelow(1000000):06d}"
            session.permanent = True

            return redirect(url_for('workspace'))

        except pd.errors.ParserError:
            os.remove(filepath)
            return render_template('upload.html', error="Invalid CSV format. Please check your file and try again.")
        except Exception as e:
            os.remove(filepath)
            return render_template('upload.html', error=f"Error processing CSV: {str(e)}")

    except Exception as e:
        return render_template('upload.html', error=f"Error uploading file: {str(e)}")


@app.route('/workspace')
def workspace():
    """Single live-preview page: customize controls + receipt ticket"""
    if 'uploaded_file' not in session:
        return redirect(url_for('index'))

    platform = session.get('platform', 'unknown')
    display_name = session.get('display_name', 'Reader')
    filepath = get_upload_path(session['uploaded_file'])

    if not os.path.exists(filepath):
        session.clear()
        return redirect(url_for('index'))

    # "Name Your Receipt" lives in the same GET controlsForm as the other
    # controls, so it's only present in the query string when that form was
    # actually submitted (including via Enter in the text field).
    if 'receipt_name' in request.args:
        session['receipt_name'] = request.args.get('receipt_name', '').strip() or 'READRECEIPTS'
    receipt_name = session.get('receipt_name', 'READRECEIPTS')

    # A hand-picked list from /custom-select takes over the ticket in place
    # of the algorithm's auto-sorted top N, until the reader changes one of
    # the Customize Receipt controls below (which submits back to this same
    # route without ?custom=1 and falls through to the normal path).
    use_custom = request.args.get('custom') == '1' and 'custom_receipt' in session

    if use_custom:
        receipt = session['custom_receipt']
        metric = receipt['metric']
        period = receipt['period']
        top_count = receipt['item_count']
    else:
        metric = request.args.get('metric', 'books')
        if metric not in METRIC_LABELS:
            metric = 'books'

        period = request.args.get('period', 'all')
        if period not in PERIOD_LABELS:
            period = 'all'

        try:
            top_count = int(request.args.get('top_count', 10))
        except ValueError:
            top_count = 10
        if top_count not in (3, 5, 10):
            top_count = 10

        receipt = compute_receipt(filepath, platform, metric, period, top_count, display_name)

        if receipt is None:
            session.clear()
            return redirect(url_for('index'))

    return render_template(
        'workspace.html',
        receipt=receipt,
        metric=metric,
        period=period,
        top_count=top_count,
        today=datetime.now().strftime('%A, %B %-d, %Y') if os.name != 'nt' else datetime.now().strftime('%A, %B %#d, %Y'),
        card_last4=session.get('card_last4', '0000'),
        auth_code=session.get('auth_code', '000000'),
        custom_active=use_custom,
        receipt_name=receipt_name,
    )


@app.route('/custom-select', methods=['GET'])
def custom_select():
    """Let the reader hand-pick which read books appear on the receipt"""
    if 'uploaded_file' not in session or 'platform' not in session:
        return redirect(url_for('index'))

    filepath = get_upload_path(session['uploaded_file'])
    if not os.path.exists(filepath):
        session.clear()
        return redirect(url_for('index'))

    try:
        read_books = get_read_books(filepath, session['platform'])
    except Exception:
        session.clear()
        return redirect(url_for('index'))

    books = [
        {
            'index': idx,
            'title': str(row['title']),
            'author': str(row['author']),
            'rating': float(row['rating']) if pd.notna(row['rating']) else 0,
        }
        for idx, row in read_books.iterrows()
    ]

    return render_template(
        'custom_select.html',
        books=books,
        receipt_name=session.get('receipt_name', 'READRECEIPTS'),
    )


@app.route('/custom-select', methods=['POST'])
def custom_select_submit():
    """Build a receipt from the reader's hand-picked books"""
    if 'uploaded_file' not in session or 'platform' not in session:
        return redirect(url_for('index'))

    filepath = get_upload_path(session['uploaded_file'])
    if not os.path.exists(filepath):
        session.clear()
        return redirect(url_for('index'))

    try:
        read_books = get_read_books(filepath, session['platform'])
    except Exception:
        session.clear()
        return redirect(url_for('index'))

    raw_indices = request.form.getlist('book_index')
    selected_indices = sorted({
        int(i) for i in raw_indices
        if i.isdigit() and 0 <= int(i) < len(read_books)
    })[:10]

    selected = read_books.loc[selected_indices]

    session['receipt_name'] = request.form.get('receipt_name', '').strip() or 'READRECEIPTS'

    entries = [
        {
            'kind': 'book',
            'title': str(row['title']),
            'author': str(row['author']),
            'rating': float(row['rating']) if pd.notna(row['rating']) else 0,
            'pages': int(row['pages']) if pd.notna(row['pages']) else 0,
            'duration': 0,
        }
        for _, row in selected.iterrows()
    ]

    total_pages = sum(item['pages'] for item in entries)
    total_books = len(entries)
    avg_rating = round(float(selected['rating'].mean()), 2) if not selected.empty else 0
    top_authors = aggregate_authors(selected, 5) if not selected.empty else []

    receipt_data = {
        'entries': entries,
        'metric': 'books',
        'metric_label': 'My Selection',
        'period': 'custom',
        'period_label': 'MY SELECTION',
        'item_count': total_books,
        'total': total_pages,
        'total_pages': total_pages,
        'total_books': total_books,
        'avg_rating': avg_rating,
        'top_authors': top_authors,
        'total_days': 0,
        'display_name': session.get('display_name', 'Reader'),
    }

    session['custom_receipt'] = receipt_data

    return redirect(url_for('workspace', custom=1))


@app.route('/start-over')
def start_over():
    """Clear session and return to upload"""
    if 'uploaded_file' in session:
        try:
            filepath = get_upload_path(session['uploaded_file'])
            if os.path.exists(filepath):
                os.remove(filepath)
        except OSError:
            pass

    session.clear()
    return redirect(url_for('index'))


@app.template_filter('pluralize')
def pluralize(count, singular, plural=None):
    """Jinja filter for pluralization"""
    if plural is None:
        plural = singular + 's'
    return singular if count == 1 else plural


if __name__ == '__main__':
    app.run(debug=True)
