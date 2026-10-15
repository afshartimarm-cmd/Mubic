# -*- coding: utf-8 -*-
"""Mubic - local prototype. Configure secure secrets and email verification before public deployment."""
import os, re, sqlite3, secrets
from functools import wraps
from datetime import datetime
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# فضای ذخیره‌سازی دائمی Deplexo
DATA_DIR = os.environ.get("MUBIC_DATA_DIR", "/data")

os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "mubic.db")

UPLOAD_DIR = os.path.join(DATA_DIR, "mubic_uploads")
MUSIC_DIR = os.path.join(UPLOAD_DIR, "music")
COVER_DIR = os.path.join(UPLOAD_DIR, "covers")

os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(COVER_DIR, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
ADMIN_USERNAME = "JJoo"
ADMIN_PASSWORD = "Abolfazl"  # Change before any public deployment.
ADMIN_EMAIL = "jjoo@mubic.local"  # Local prototype login identifier; not a real mailbox.
ALLOWED_AUDIO = {".mp3", ".wav", ".ogg", ".m4a"}
ALLOWED_COVERS = {".jpg", ".jpeg", ".png", ".webp"}

STYLE = r'''
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap');
:root{--ink:#f4f4ff;--muted:#aaa8c8;--line:#292341;--paper:rgba(20,16,39,.88);--bg:#080611;--cyan:#00eaff;--purple:#9b5cff}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;min-height:100vh;background:#080611;color:#f4f4ff;font-family:'Vazirmatn',Tahoma,sans-serif;direction:rtl;overflow-x:hidden;position:relative}
body:before{content:"";position:fixed;inset:-25%;z-index:-2;pointer-events:none;background:radial-gradient(ellipse at 15% 20%,#00eaff22,transparent 32%),radial-gradient(ellipse at 82% 28%,#9b5cff2b,transparent 34%),radial-gradient(ellipse at 55% 90%,#38108c26,transparent 38%);animation:ambient 20s ease-in-out infinite alternate}
body:after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:.13;background-image:radial-gradient(#8a7cc5 .7px,transparent .7px);background-size:29px 29px}
a{text-decoration:none;color:inherit}button,input,textarea,select{font:inherit}button,.btn{display:inline-block;border:1px solid #ffffff18;border-radius:12px;padding:11px 17px;cursor:pointer;background:linear-gradient(110deg,#00bcd4,#7150dc);color:#fff;box-shadow:0 0 20px #00eaff12;transition:transform .2s,filter .2s,box-shadow .2s}button:hover,.btn:hover{filter:brightness(1.12);transform:translateY(-2px);box-shadow:0 0 25px #00eaff28}
input,textarea,select{width:100%;padding:12px;margin:7px 0 15px;border:1px solid #342b50;border-radius:12px;background:#100c20;color:#fff;outline:none;transition:border-color .2s,box-shadow .2s}input::placeholder,textarea::placeholder{color:#77718f}input:focus,textarea:focus,select:focus{border-color:var(--cyan);box-shadow:0 0 0 3px #00eaff12}
header{position:sticky;top:0;z-index:50;background:#0a0715df;backdrop-filter:blur(18px);border-bottom:1px solid #ffffff12;box-shadow:0 4px 30px #0004;padding:15px 5%;display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap}.logo{font-family:Arial,sans-serif;font-size:32px;font-weight:800;letter-spacing:-1.5px;color:#fff;transition:transform .2s;text-shadow:0 0 20px #00eaff22}.logo:hover{transform:scale(1.035)}nav{display:flex;gap:17px;align-items:center;flex-wrap:wrap;font-size:14px}nav a:not(.btn):hover{color:var(--cyan)}
.container{max-width:1120px;margin:34px auto;padding:0 18px;min-height:55vh}.hero{position:relative;isolation:isolate;overflow:hidden;background:linear-gradient(125deg,#0b0818ed,#17102bea 65%,#090714ed);color:#fff;border:1px solid #8c63ff30;border-radius:27px;padding:45px 30px;margin-bottom:36px;box-shadow:0 20px 60px #0004,0 0 35px #00eaff08;animation:fadeUp .6s ease both}.hero:before{content:"";position:absolute;width:300px;height:300px;border-radius:50%;background:#00eaff30;filter:blur(75px);top:-120px;left:-80px;animation:glow 9s ease-in-out infinite alternate;pointer-events:none;z-index:-1}.hero:after{content:"";position:absolute;width:260px;height:260px;border-radius:50%;background:#9b5cff30;filter:blur(80px);bottom:-160px;right:20%;animation:glow 12s ease-in-out infinite alternate-reverse;pointer-events:none;z-index:-1}.hero h1{position:relative;font-size:clamp(32px,6vw,49px);margin:0 0 14px;letter-spacing:-1px}.hero p{position:relative;color:#c6c1df;line-height:2.1;max-width:720px}.hero .btn{position:relative;margin-top:10px}
.section-title{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:18px}.section-title h2{letter-spacing:-.5px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:18px;margin-top:20px}.card{background:linear-gradient(145deg,#171229ef,#0f0b1df0);border:1px solid #ffffff12;border-radius:19px;padding:13px;overflow:hidden;box-shadow:0 5px 24px #0003;transition:transform .25s,border-color .25s,box-shadow .25s;animation:fadeUp .45s ease both}.card:hover{transform:translateY(-4px);border-color:#00eaff45;box-shadow:0 15px 35px #0004,0 0 22px #00eaff0b}.cover{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:14px;background:linear-gradient(135deg,#1e1733,#29203f)}.card h3{margin:11px 0 4px;font-size:17px}.muted{color:var(--muted);font-size:13px;line-height:1.9}
.form-card{max-width:560px;margin:30px auto;background:linear-gradient(145deg,#171229f2,#0f0b1df5);padding:27px;border-radius:22px;border:1px solid #ffffff15;box-shadow:0 15px 50px #0004,0 0 25px #9b5cff09;animation:fadeUp .45s ease both}.form-card h1{margin-top:0}.notice{padding:13px 16px;border-radius:13px;background:#171229;border:1px solid #ffffff10;margin:15px 0;line-height:1.9}.notice.success{background:#0b2828;border-color:#00eaff33;color:#b9fbff}.notice.error{background:#2c111f;border-color:#ff668855;color:#ffd0dc}.player{width:100%;margin-top:12px;accent-color:var(--cyan)}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.actions form{display:inline}footer{text-align:center;color:#aaa6c7;padding:32px 15px;margin-top:48px;border-top:1px solid #ffffff12;background:#0a0715a8;line-height:2}footer a{color:var(--cyan)}table{width:100%;border-collapse:collapse;background:#100c20;min-width:560px;color:#f4f4ff}th,td{padding:12px;border-bottom:1px solid #ffffff12;text-align:right;vertical-align:top}.badge{display:inline-block;background:#25203a;color:#d8d0ff;padding:5px 10px;border-radius:9px;font-size:12px}.table-wrap{overflow-x:auto;border-radius:14px;border:1px solid #ffffff15}
.search-panel{display:flex;gap:10px;align-items:center;margin:0 0 30px;padding:12px;background:#100c20d9;border:1px solid #ffffff14;border-radius:17px;box-shadow:0 8px 28px #0003}.search-panel input{margin:0;min-width:0;background:#0b0816;border-color:#302545}.search-panel button{white-space:nowrap}.music-rain{position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:0;opacity:.3}.music-note{position:absolute;top:-12vh;color:#8a79ff;text-shadow:0 0 12px #8a5cff66;animation:noteFall linear infinite;user-select:none}.container,header,footer{position:relative;z-index:1}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}@keyframes glow{from{transform:translate(0,0) scale(1)}to{transform:translate(45px,25px) scale(1.2)}}@keyframes ambient{0%{transform:translate3d(-2%,0,0) scale(1)}50%{transform:translate3d(2%,2%,0) scale(1.08)}100%{transform:translate3d(-1%,3%,0) scale(1.02)}}@keyframes noteFall{0%{transform:translate3d(0,-10vh,0) rotate(0);opacity:0}12%{opacity:.75}85%{opacity:.55}100%{transform:translate3d(35px,115vh,0) rotate(160deg);opacity:0}}@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important}}@media(max-width:600px){header{padding:13px 15px}.logo{font-size:29px}nav{gap:11px;font-size:13px}.container{margin-top:22px}.hero{padding:32px 21px}.form-card{padding:20px}.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.card{padding:10px}.section-title h2{font-size:20px}.search-panel{gap:7px}.search-panel button{padding:11px 12px}}
'''


def connect_db():
    db = sqlite3.connect(DB_PATH, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db():
    with connect_db() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE,
          email TEXT NOT NULL UNIQUE, password TEXT NOT NULL, bio TEXT DEFAULT '',
          is_admin INTEGER DEFAULT 0, banned INTEGER DEFAULT 0, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tracks(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          title TEXT NOT NULL, artist TEXT NOT NULL, mixer TEXT DEFAULT '',
          mastering TEXT DEFAULT '', producer TEXT DEFAULT '', genre TEXT DEFAULT '',
          description TEXT DEFAULT '', audio_file TEXT NOT NULL, cover_file TEXT NOT NULL,
          status TEXT DEFAULT 'pending', views INTEGER DEFAULT 0, created_at TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS votes(
          user_id INTEGER NOT NULL, track_id INTEGER NOT NULL, vote INTEGER NOT NULL,
          PRIMARY KEY(user_id,track_id), FOREIGN KEY(user_id) REFERENCES users(id),
          FOREIGN KEY(track_id) REFERENCES tracks(id));
        CREATE TABLE IF NOT EXISTS comments(
          id INTEGER PRIMARY KEY AUTOINCREMENT, track_id INTEGER NOT NULL,
          user_id INTEGER NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL,
          FOREIGN KEY(track_id) REFERENCES tracks(id), FOREIGN KEY(user_id) REFERENCES users(id));
        ''')
        # Create or repair the requested administrator account.
        admin = db.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,)).fetchone()
        email_owner = db.execute("SELECT id,username FROM users WHERE email=?", (ADMIN_EMAIL,)).fetchone()
        if admin:
            db.execute("UPDATE users SET email=?,password=?,is_admin=1,banned=0 WHERE id=?",
                       (ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), admin['id']))
        elif not email_owner:
            db.execute('''INSERT INTO users(username,email,password,is_admin,banned,created_at)
                          VALUES(?,?,?,1,0,?)''',
                       (ADMIN_USERNAME, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), datetime.now().isoformat()))
        else:
            # Avoid changing another user's account if the reserved local email was already used.
            raise RuntimeError("ایمیل رزروشده مدیریت در پایگاه داده متعلق به حساب دیگری است. فایل mubic.db را بررسی کنید.")


def current_user():
    uid = session.get('user_id')
    if not uid: return None
    with connect_db() as db:
        user = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if user and user['banned']:
        session.clear(); return None
    return user


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash('برای ادامه وارد حساب خودت شو.', 'error')
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapped


def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            flash('ابتدا وارد حساب مدیریت شو.', 'error')
            return redirect(url_for('login'))
        if not user['is_admin']:
            return page('''<section class="form-card" style="text-align:center"><h1>دسترسی محدود است</h1><p>این بخش فقط برای مدیریت Mubic است.</p><a class="btn" href="{{ url_for('home') }}">بازگشت به صفحه اصلی</a></section>''', title='دسترسی محدود'), 403
        return fn(*args, **kwargs)
    return wrapped


def page(content, **kwargs):
    user = current_user()
    title = kwargs.pop('title', 'موسیقی رایگان')
    return render_template_string('''<!doctype html><html lang="fa" dir="rtl"><head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="theme-color" content="#f7f7f7"><title>{{ title }} | Mubic</title><style>''' + STYLE + '''</style></head><body>
    <header><a class="logo" href="{{ url_for('home') }}">Mubic</a><nav>
    <a href="{{ url_for('home') }}">صفحه اصلی</a>
    {% if user %}<a href="{{ url_for('upload') }}">آپلود موزیک</a><a href="{{ url_for('my_tracks') }}">موزیک‌های من</a>
    <a href="{{ url_for('profile', username=user['username']) }}">پروفایل من</a>
    {% if user['is_admin'] %}<a href="{{ url_for('admin_panel') }}">مدیریت</a>{% endif %}<a href="{{ url_for('logout') }}">خروج</a>
    {% else %}<a href="{{ url_for('login') }}">ورود</a><a class="btn" href="{{ url_for('register') }}">ثبت‌نام</a>{% endif %}</nav></header>
    <div class="music-rain" aria-hidden="true">{% for note in music_notes %}<span class="music-note" style="left:{{ note.left }}%;animation-delay:-{{ note.delay }}s;animation-duration:{{ note.duration }}s;font-size:{{ note.size }}px">{{ note.symbol }}</span>{% endfor %}</div><main class="container">{% for category,message in get_flashed_messages(with_categories=true) %}<div class="notice {{ category }}">{{ message }}</div>{% endfor %}''' + content + '''</main>
    <footer><b>Mubic</b> — موسیقی برای همه، رایگان.<br>پشتیبانی: <a href="https://t.me/Tucusi" target="_blank" rel="noopener">Telegram : @Tucusi</a></footer></body></html>''', title=title, user=user, music_notes=[{'left':4,'delay':2,'duration':22,'size':19,'symbol':'♪'},{'left':13,'delay':8,'duration':27,'size':15,'symbol':'♫'},{'left':24,'delay':4,'duration':24,'size':22,'symbol':'♬'},{'left':37,'delay':11,'duration':29,'size':17,'symbol':'♪'},{'left':49,'delay':6,'duration':25,'size':20,'symbol':'♫'},{'left':61,'delay':14,'duration':30,'size':16,'symbol':'♪'},{'left':73,'delay':3,'duration':26,'size':22,'symbol':'♬'},{'left':84,'delay':10,'duration':28,'size':17,'symbol':'♫'},{'left':94,'delay':5,'duration':23,'size':19,'symbol':'♪'}], **kwargs)


@app.route('/')
def home():
    query = request.args.get('q', '').strip()[:100]
    with connect_db() as db:
        if query:
            pattern = '%' + query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
            tracks = db.execute('''SELECT t.*,u.username,
                (SELECT COUNT(*) FROM votes v WHERE v.track_id=t.id AND v.vote=1) likes,
                (SELECT COUNT(*) FROM votes v WHERE v.track_id=t.id AND v.vote=-1) dislikes
                FROM tracks t JOIN users u ON u.id=t.user_id
                WHERE t.status='approved' AND u.banned=0
                AND (t.title LIKE ? ESCAPE '\\' OR t.artist LIKE ? ESCAPE '\\' OR t.genre LIKE ? ESCAPE '\\' OR u.username LIKE ? ESCAPE '\\')
                ORDER BY t.id DESC LIMIT 100''', (pattern, pattern, pattern, pattern)).fetchall()
        else:
            tracks = db.execute('''SELECT t.*,u.username,
                (SELECT COUNT(*) FROM votes v WHERE v.track_id=t.id AND v.vote=1) likes,
                (SELECT COUNT(*) FROM votes v WHERE v.track_id=t.id AND v.vote=-1) dislikes
                FROM tracks t JOIN users u ON u.id=t.user_id WHERE t.status='approved' AND u.banned=0
                ORDER BY t.id DESC LIMIT 40''').fetchall()
    return page('''<section class="hero"><h1>موسیقی، بدون مرز.</h1><p>آهنگ‌های تازه را کشف کن، به هنرمندان گوش بده و موسیقی خودت را برای انتشار رایگان در Mubic بفرست.</p><a class="btn" href="{{ url_for('register') }}">شروع کن</a></section>
    <form class="search-panel" action="{{ url_for('home') }}" method="get">
      <input type="search" name="q" value="{{ query }}" maxlength="100" placeholder="جست‌وجوی نام موزیک، خواننده یا سبک..." aria-label="جست‌وجوی موسیقی">
      <button type="submit">جست‌وجو</button>
      {% if query %}<a class="btn" href="{{ url_for('home') }}">پاک‌کردن</a>{% endif %}
    </form>
    <div class="section-title"><h2>{% if query %}نتایج جست‌وجو{% else %}جدیدترین موزیک‌ها{% endif %}</h2><span class="muted">{{ tracks|length }} آهنگ</span></div><div class="grid">
    {% for t in tracks %}<article class="card"><a href="{{ url_for('track_page',track_id=t['id']) }}"><img class="cover" src="{{ url_for('cover',filename=t['cover_file']) }}" alt="کاور"><h3>{{ t['title'] }}</h3></a><div class="muted">{{ t['artist'] }}</div><div class="muted">▶ {{ t['views'] }} بازدید · ♥ {{ t['likes'] }}</div></article>
    {% else %}<div class="notice">{% if query %}نتیجه‌ای برای «{{ query }}» پیدا نشد.{% else %}هنوز موزیکی منتشر نشده است.{% endif %}</div>{% endfor %}</div>''', title='جست‌وجوی موسیقی' if query else 'صفحه اصلی', tracks=tracks, query=query)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username=request.form.get('username','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        if not re.fullmatch(r'[A-Za-z0-9_.-]{3,30}', username): flash('نام کاربری باید ۳ تا ۳۰ حرف انگلیسی، عدد یا . _ - باشد.','error')
        elif username.casefold() == ADMIN_USERNAME.casefold(): flash('این نام کاربری رزرو مدیریت است.','error')
        elif not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email): flash('ایمیل معتبر وارد کن.','error')
        elif len(password)<10: flash('رمز عبور باید حداقل ۱۰ کاراکتر باشد.','error')
        else:
            try:
                with connect_db() as db: db.execute('INSERT INTO users(username,email,password,created_at) VALUES(?,?,?,?)',(username,email,generate_password_hash(password),datetime.now().isoformat()))
                flash('حساب ساخته شد. توجه: تأیید ایمیل هنوز در این نسخه فعال نشده است.','success'); return redirect(url_for('login'))
            except sqlite3.IntegrityError: flash('نام کاربری یا ایمیل قبلاً ثبت شده است.','error')
    return page('''<section class="form-card"><h1>ساخت حساب</h1><p class="muted">به خانواده Mubic بپیوند.</p><form method="post"><label>نام کاربری</label><input name="username" minlength="3" maxlength="30" required><label>ایمیل</label><input name="email" type="email" maxlength="254" required><label>رمز عبور</label><input name="password" type="password" minlength="10" required><button>ثبت‌نام</button></form></section>''',title='ثبت‌نام')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        identifier=request.form.get('identifier','').strip(); password=request.form.get('password','')
        with connect_db() as db: user=db.execute('SELECT * FROM users WHERE lower(email)=lower(?) OR lower(username)=lower(?)',(identifier,identifier)).fetchone()
        if user and check_password_hash(user['password'],password):
            if user['banned']: flash('حساب شما مسدود شده است.','error')
            else:
                session.clear(); session['user_id']=user['id']; session.permanent=False
                return redirect(url_for('admin_panel' if user['is_admin'] else 'home'))
        else: flash('نام کاربری/ایمیل یا رمز عبور اشتباه است.','error')
    return page('''<section class="form-card"><h1>ورود به Mubic</h1><form method="post"><label>نام کاربری یا ایمیل</label><input name="identifier" autocomplete="username" required><label>رمز عبور</label><input name="password" type="password" autocomplete="current-password" required><button>ورود</button></form><p>حساب نداری؟ <a href="{{ url_for('register') }}">ثبت‌نام کن</a></p></section>''',title='ورود')


@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))


@app.route('/upload', methods=['GET','POST'])
@login_required
def upload():
    if request.method=='POST':
        user=current_user(); title=request.form.get('title','').strip(); artist=request.form.get('artist','').strip(); audio=request.files.get('audio'); cover_file=request.files.get('cover')
        if not title or not artist or not audio or not cover_file or not audio.filename or not cover_file.filename: flash('نام آهنگ، خواننده، فایل صوتی و کاور الزامی است.','error')
        else:
            ae=os.path.splitext(secure_filename(audio.filename))[1].lower(); ce=os.path.splitext(secure_filename(cover_file.filename))[1].lower()
            if ae not in ALLOWED_AUDIO: flash('فرمت صوتی مجاز: MP3، WAV، OGG یا M4A.','error')
            elif ce not in ALLOWED_COVERS: flash('فرمت کاور مجاز: JPG، PNG یا WEBP.','error')
            else:
                an=secrets.token_hex(16)+ae; cn=secrets.token_hex(16)+ce
                try:
                    audio.save(os.path.join(MUSIC_DIR,an)); cover_file.save(os.path.join(COVER_DIR,cn))
                    with connect_db() as db: db.execute('''INSERT INTO tracks(user_id,title,artist,mixer,mastering,producer,genre,description,audio_file,cover_file,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(user['id'],title,artist,request.form.get('mixer','').strip(),request.form.get('mastering','').strip(),request.form.get('producer','').strip(),request.form.get('genre','').strip(),request.form.get('description','').strip(),an,cn,'pending',datetime.now().isoformat()))
                    flash('موزیک ارسال شد و منتظر بررسی مدیریت است.','success'); return redirect(url_for('my_tracks'))
                except Exception:
                    for folder,name in ((MUSIC_DIR,an),(COVER_DIR,cn)):
                        try: os.remove(os.path.join(folder,name))
                        except OSError: pass
                    raise
    return page('''<section class="form-card"><h1>آپلود موزیک</h1><div class="notice">۱ الی ۴ روز طول می‌کشد تا موزیک شما بررسی و پخش شود. انتشار فقط پس از تأیید مدیریت انجام می‌شود.</div><form method="post" enctype="multipart/form-data"><label>نام موزیک *</label><input name="title" maxlength="150" required><label>نام خواننده *</label><input name="artist" maxlength="150" required><label>کاور آهنگ *</label><input name="cover" type="file" accept=".jpg,.jpeg,.png,.webp" required><label>فایل موسیقی *</label><input name="audio" type="file" accept=".mp3,.wav,.ogg,.m4a" required><label>میکس‌کننده</label><input name="mixer" maxlength="150"><label>مسترینگ</label><input name="mastering" maxlength="150"><label>تنظیم‌کننده</label><input name="producer" maxlength="150"><label>سبک موسیقی</label><input name="genre" maxlength="80"><label>توضیحات</label><textarea name="description" maxlength="2000" rows="4"></textarea><button>ارسال برای بررسی</button></form></section>''',title='آپلود موزیک')


@app.route('/my-tracks')
@login_required
def my_tracks():
    user=current_user()
    with connect_db() as db: tracks=db.execute('SELECT * FROM tracks WHERE user_id=? ORDER BY id DESC',(user['id'],)).fetchall()
    return page('''<h1>موزیک‌های من</h1><div class="grid">{% for t in tracks %}<article class="card"><img class="cover" src="{{ url_for('cover',filename=t['cover_file']) }}"><h3>{{ t['title'] }}</h3><span class="badge">{% if t['status']=='pending' %}در انتظار بررسی{% elif t['status']=='approved' %}منتشرشده{% elif t['status']=='rejected' %}ردشده{% else %}حذف‌شده{% endif %}</span></article>{% else %}<p>هنوز آهنگی ارسال نکرده‌ای.</p>{% endfor %}</div>''',title='موزیک‌های من',tracks=tracks)


@app.route('/artist/<username>')
def profile(username):
    with connect_db() as db:
        artist=db.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
        if not artist or artist['banned']: abort(404)
        tracks=db.execute("SELECT * FROM tracks WHERE user_id=? AND status='approved' ORDER BY id DESC",(artist['id'],)).fetchall()
    return page('''<section class="hero"><h1>{{ artist['username'] }}</h1><p>{{ artist['bio'] or 'هنرمند Mubic' }}</p><p>{{ tracks|length }} موزیک منتشرشده</p>{% if user and user['id']==artist['id'] %}<a class="btn" href="{{ url_for('edit_profile') }}">ویرایش بیوگرافی</a>{% endif %}</section><h2>آهنگ‌های این هنرمند</h2><div class="grid">{% for t in tracks %}<article class="card"><a href="{{ url_for('track_page',track_id=t['id']) }}"><img class="cover" src="{{ url_for('cover',filename=t['cover_file']) }}"><h3>{{ t['title'] }}</h3></a></article>{% else %}<p>هنوز موزیکی منتشر نشده است.</p>{% endfor %}</div>''',title=artist['username'],artist=artist,tracks=tracks)


@app.route('/edit-profile',methods=['GET','POST'])
@login_required
def edit_profile():
    user=current_user()
    if request.method=='POST':
        with connect_db() as db: db.execute('UPDATE users SET bio=? WHERE id=?',(request.form.get('bio','').strip()[:1000],user['id']))
        flash('بیوگرافی ذخیره شد.','success'); return redirect(url_for('profile',username=user['username']))
    return page('''<section class="form-card"><h1>ویرایش پروفایل</h1><form method="post"><label>بیوگرافی</label><textarea name="bio" rows="5" maxlength="1000">{{ user['bio'] }}</textarea><button>ذخیره</button></form></section>''',title='ویرایش پروفایل',user=user)


@app.route('/track/<int:track_id>')
def track_page(track_id):
    with connect_db() as db:
        track=db.execute('''SELECT t.*,u.username,(SELECT COUNT(*) FROM votes v WHERE v.track_id=t.id AND v.vote=1) likes,(SELECT COUNT(*) FROM votes v WHERE v.track_id=t.id AND v.vote=-1) dislikes FROM tracks t JOIN users u ON u.id=t.user_id WHERE t.id=? AND t.status='approved' AND u.banned=0''',(track_id,)).fetchone()
        if not track: abort(404)
        db.execute('UPDATE tracks SET views=views+1 WHERE id=?',(track_id,))
        comments=db.execute('''SELECT c.*,u.username FROM comments c JOIN users u ON u.id=c.user_id WHERE c.track_id=? AND u.banned=0 ORDER BY c.id DESC LIMIT 100''',(track_id,)).fetchall()
    return page('''<section class="form-card"><img class="cover" src="{{ url_for('cover',filename=track['cover_file']) }}"><h1>{{ track['title'] }}</h1><p>خواننده: <a href="{{ url_for('profile',username=track['username']) }}">{{ track['artist'] }}</a></p><p class="muted">میکس: {{ track['mixer'] or '—' }} | مسترینگ: {{ track['mastering'] or '—' }}</p><audio class="player" controls preload="none" src="{{ url_for('audio',filename=track['audio_file']) }}"></audio><p>بازدید: {{ track['views']+1 }} | ♥ {{ track['likes'] }} | 👎 {{ track['dislikes'] }}</p>{% if user %}<div class="actions"><form action="{{ url_for('vote',track_id=track['id']) }}" method="post"><input type="hidden" name="vote" value="1"><button>♥ لایک</button></form><form action="{{ url_for('vote',track_id=track['id']) }}" method="post"><input type="hidden" name="vote" value="-1"><button>👎 دیسلایک</button></form></div>{% else %}<p><a href="{{ url_for('login') }}">برای رأی‌دادن وارد شو.</a></p>{% endif %}<p>{{ track['description'] }}</p></section><section class="form-card"><h2>نظرات</h2>{% if user %}<form method="post" action="{{ url_for('add_comment',track_id=track['id']) }}"><textarea name="body" maxlength="1000" rows="3" placeholder="نظر خودت را بنویس..." required></textarea><button>ثبت نظر</button></form>{% else %}<p>برای ثبت نظر باید وارد حساب کاربری شوی.</p>{% endif %}{% for c in comments %}<div class="notice"><b>{{ c['username'] }}</b><p>{{ c['body'] }}</p></div>{% else %}<p class="muted">هنوز نظری ثبت نشده است.</p>{% endfor %}</section>''',title=track['title'],track=track,comments=comments)


@app.route('/vote/<int:track_id>',methods=['POST'])
@login_required
def vote(track_id):
    user=current_user()
    try: value=int(request.form.get('vote','0'))
    except ValueError: value=0
    if value not in (1,-1): abort(400)
    with connect_db() as db:
        if not db.execute("SELECT id FROM tracks WHERE id=? AND status='approved'",(track_id,)).fetchone(): abort(404)
        db.execute('''INSERT INTO votes(user_id,track_id,vote) VALUES(?,?,?) ON CONFLICT(user_id,track_id) DO UPDATE SET vote=excluded.vote''',(user['id'],track_id,value))
    return redirect(url_for('track_page',track_id=track_id))


@app.route('/comment/<int:track_id>',methods=['POST'])
@login_required
def add_comment(track_id):
    user=current_user(); body=request.form.get('body','').strip()
    if not body or len(body)>1000: flash('متن نظر معتبر نیست.','error')
    else:
        with connect_db() as db:
            if db.execute("SELECT id FROM tracks WHERE id=? AND status='approved'",(track_id,)).fetchone():
                db.execute('INSERT INTO comments(track_id,user_id,body,created_at) VALUES(?,?,?,?)',(track_id,user['id'],body,datetime.now().isoformat()))
    return redirect(url_for('track_page',track_id=track_id))


@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    with connect_db() as db:
        pending=db.execute("SELECT t.*,u.username FROM tracks t JOIN users u ON u.id=t.user_id WHERE t.status='pending' ORDER BY t.id ASC").fetchall()
        users=db.execute('SELECT id,username,email,banned FROM users WHERE is_admin=0 ORDER BY id DESC').fetchall()
        stats={'users':db.execute('SELECT COUNT(*) FROM users').fetchone()[0],'tracks':db.execute("SELECT COUNT(*) FROM tracks WHERE status='approved'").fetchone()[0],'pending':len(pending)}
    return page('''<section class="hero"><h1>پنل مدیریت</h1><p>بررسی و انتشار موسیقی‌های ارسالی در Mubic.</p></section><div class="grid"><div class="card"><h2>{{ stats.users }}</h2><p>کاربران</p></div><div class="card"><h2>{{ stats.tracks }}</h2><p>آهنگ منتشرشده</p></div><div class="card"><h2>{{ stats.pending }}</h2><p>در انتظار بررسی</p></div></div><h2>آهنگ‌های در انتظار بررسی</h2>{% for t in pending %}<article class="card" style="margin:15px 0"><h3>{{ t['title'] }} — {{ t['artist'] }}</h3><p>ارسال‌کننده: {{ t['username'] }}</p><img class="cover" style="max-width:200px" src="{{ url_for('cover',filename=t['cover_file']) }}"><audio controls class="player" src="{{ url_for('audio',filename=t['audio_file']) }}"></audio><p>میکس: {{ t['mixer'] or '—' }} | مسترینگ: {{ t['mastering'] or '—' }}</p><div class="actions"><form method="post" action="{{ url_for('review_track',track_id=t['id']) }}"><input type="hidden" name="decision" value="approved"><button>تأیید و انتشار</button></form><form method="post" action="{{ url_for('review_track',track_id=t['id']) }}"><input type="hidden" name="decision" value="rejected"><button>رد آهنگ</button></form></div></article>{% else %}<div class="notice">آهنگی در انتظار بررسی نیست.</div>{% endfor %}<h2>مدیریت کاربران</h2><div class="table-wrap"><table><tr><th>نام کاربری</th><th>ایمیل</th><th>وضعیت</th><th>عملیات</th></tr>{% for u in users %}<tr><td>{{ u['username'] }}</td><td>{{ u['email'] }}</td><td>{{ 'مسدود' if u['banned'] else 'فعال' }}</td><td><form method="post" action="{{ url_for('ban_user',user_id=u['id']) }}"><input type="hidden" name="banned" value="{{ 0 if u['banned'] else 1 }}"><button>{{ 'رفع مسدودیت' if u['banned'] else 'مسدودکردن' }}</button></form></td></tr>{% endfor %}</table></div>''',title='مدیریت',pending=pending,users=users,stats=stats)


@app.route('/admin/review/<int:track_id>',methods=['POST'])
@login_required
@admin_required
def review_track(track_id):
    decision=request.form.get('decision')
    if decision not in ('approved','rejected'): abort(400)
    with connect_db() as db: db.execute("UPDATE tracks SET status=? WHERE id=? AND status='pending'",(decision,track_id))
    flash('وضعیت آهنگ ثبت شد.','success'); return redirect(url_for('admin_panel'))


@app.route('/admin/ban/<int:user_id>',methods=['POST'])
@login_required
@admin_required
def ban_user(user_id):
    if user_id==current_user()['id']: abort(400)
    banned=1 if request.form.get('banned')=='1' else 0
    with connect_db() as db: db.execute('UPDATE users SET banned=? WHERE id=? AND is_admin=0',(banned,user_id))
    return redirect(url_for('admin_panel'))


def serve_media(folder, filename, kind):
    # Never allow path traversal; serve pending tracks only to the administrator or their owner.
    if secure_filename(filename) != filename: abort(404)
    column = 'audio_file' if kind == 'audio' else 'cover_file'
    with connect_db() as db:
        track=db.execute(f'SELECT t.status,t.user_id FROM tracks t WHERE t.{column}=?',(filename,)).fetchone()
    if not track: abort(404)
    user=current_user()
    if track['status']!='approved' and not (user and (user['is_admin'] or user['id']==track['user_id'])): abort(404)
    return send_from_directory(folder,filename,conditional=True)

@app.route('/uploads/music/<filename>')
def audio(filename): return serve_media(MUSIC_DIR,filename,'audio')
@app.route('/uploads/covers/<filename>')
def cover(filename): return serve_media(COVER_DIR,filename,'cover')

@app.errorhandler(413)
def too_large(error): return 'حجم فایل‌ها در این نسخه حداکثر ۵۰ مگابایت است.',413

init_db()
if __name__ == '__main__':
    print('='*38)
    print('Mubic is running!')
    print('Open: http://127.0.0.1:5000')
    print('Admin username:', ADMIN_USERNAME)
    print('Admin password:', ADMIN_PASSWORD)
    print('Local prototype only: email verification and production security still need setup.')
    print('='*38)
    app.run(host='127.0.0.1',port=5000,debug=False)
