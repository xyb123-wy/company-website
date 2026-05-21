import os
import uuid
from datetime import timedelta
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   jsonify, session, send_from_directory)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, UserMixin, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image

from models import get_db, init_db

# ===== 配置 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, template_folder=BASE_DIR,
            static_folder=BASE_DIR, static_url_path='')
app.secret_key = 'zhicheng-cms-secret-key-2026'

# ===== Flask-Login 设置 =====
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.session_protection = 'strong'


class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    conn.close()
    if row:
        return User(row['id'], row['username'])
    return None


# 会话超时 30 分钟
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': '请先登录'}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ===== 辅助函数 =====
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_content(section, key, default=''):
    conn = get_db()
    row = conn.execute(
        'SELECT content FROM site_content WHERE section=? AND field_key=?',
        (section, key)).fetchone()
    conn.close()
    return row['content'] if row else default


def get_all_content(section):
    conn = get_db()
    rows = conn.execute(
        'SELECT field_key, content FROM site_content WHERE section=?', (section,)).fetchall()
    conn.close()
    return {r['field_key']: r['content'] for r in rows}


# ===== 前台页面 =====
@app.route('/')
def index():
    conn = get_db()
    services = conn.execute('SELECT * FROM services ORDER BY sort_order').fetchall()
    cases = conn.execute('SELECT * FROM cases ORDER BY sort_order').fetchall()
    news = conn.execute('SELECT * FROM news ORDER BY date DESC').fetchall()
    contact = conn.execute('SELECT * FROM contact_info ORDER BY sort_order').fetchall()
    content = {}
    for row in conn.execute('SELECT section, field_key, content FROM site_content').fetchall():
        content[f'{row["section"]}_{row["field_key"]}'] = row['content']
    conn.close()
    return render_template('index.html', services=services, cases=cases,
                           news=news, contact=contact, content=content)


# ===== 后台 - 登录 =====
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        conn = get_db()
        row = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        conn.close()
        if row and check_password_hash(row['password_hash'], password):
            login_user(User(row['id'], row['username']), remember=True,
                       duration=timedelta(minutes=30))
            next_page = request.args.get('next', url_for('admin_dashboard'))
            return redirect(next_page)
        return render_template('admin/login.html', error='用户名或密码错误')
    return render_template('admin/login.html', error='')


# ===== 后台 - 退出 =====
@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))


# ===== 后台 - 仪表盘 =====
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    conn = get_db()
    stats = {
        'services': conn.execute('SELECT COUNT(*) as n FROM services').fetchone()['n'],
        'cases': conn.execute('SELECT COUNT(*) as n FROM cases').fetchone()['n'],
        'news': conn.execute('SELECT COUNT(*) as n FROM news').fetchone()['n'],
        'messages': conn.execute('SELECT COUNT(*) as n FROM messages').fetchone()['n'],
    }
    conn.close()
    return render_template('admin/dashboard.html', stats=stats)


# ===== 后台 - 内容编辑页面 =====
@app.route('/admin/edit/<section>')
@login_required
def admin_edit(section):
    conn = get_db()
    if section == 'hero':
        content = get_all_content('hero')
        data = {'content': content}
    elif section == 'about':
        content = get_all_content('about')
        data = {'content': content}
    elif section == 'footer':
        content = get_all_content('footer')
        data = {'content': content}
    elif section == 'services':
        data = {'services': conn.execute(
            'SELECT * FROM services ORDER BY sort_order').fetchall()}
    elif section == 'cases':
        data = {'cases': conn.execute(
            'SELECT * FROM cases ORDER BY sort_order').fetchall()}
    elif section == 'news':
        data = {'news': conn.execute(
            'SELECT * FROM news ORDER BY date DESC').fetchall()}
    elif section == 'contact':
        data = {'contact': conn.execute(
            'SELECT * FROM contact_info ORDER BY sort_order').fetchall()}
    elif section == 'messages':
        data = {'messages': conn.execute(
            'SELECT * FROM messages ORDER BY created_at DESC').fetchall()}
    elif section == 'settings':
        content = get_all_content('settings')
        data = {'content': content}
    else:
        return redirect(url_for('admin_dashboard'))
    conn.close()
    return render_template('admin/editor.html', section=section, data=data)


# ===== API - 保存单项内容 =====
@app.route('/api/save-content', methods=['POST'])
@admin_required
def api_save_content():
    data = request.get_json()
    section = data.get('section')
    updates = data.get('updates', {})
    if not section or not updates:
        return jsonify({'error': '参数错误'}), 400
    conn = get_db()
    for key, value in updates.items():
        conn.execute(
            'INSERT INTO site_content (section, field_key, content) VALUES (?, ?, ?) '
            'ON CONFLICT(section, field_key) DO UPDATE SET content=excluded.content',
            (section, key, str(value)))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


# ===== API - 服务 CRUD =====
@app.route('/api/services', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def api_services():
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('SELECT * FROM services ORDER BY sort_order').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])

    if request.method == 'POST':
        data = request.get_json()
        conn.execute('INSERT INTO services (icon, title, description, sort_order) VALUES (?, ?, ?, ?)',
                     (data.get('icon', '📌'), data['title'], data.get('description', ''), data.get('sort_order', 99)))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    if request.method == 'PUT':
        data = request.get_json()
        item_id = data.pop('id', None)
        if not item_id:
            conn.close()
            return jsonify({'error': '缺少ID'}), 400
        fields = ', '.join(f'{k}=?' for k in data)
        conn.execute(f'UPDATE services SET {fields} WHERE id=?', (*data.values(), item_id))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    if request.method == 'DELETE':
        item_id = request.args.get('id')
        conn.execute('DELETE FROM services WHERE id=?', (item_id,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})


# ===== API - 案例 CRUD =====
@app.route('/api/cases', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def api_cases():
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('SELECT * FROM cases ORDER BY sort_order').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])

    if request.method == 'POST':
        data = request.get_json()
        conn.execute(
            'INSERT INTO cases (category, title, description, image_path, sort_order) VALUES (?, ?, ?, ?, ?)',
            (data.get('category', 'building'), data['title'], data.get('description', ''),
             data.get('image_path', ''), data.get('sort_order', 99)))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    if request.method == 'PUT':
        data = request.get_json()
        item_id = data.pop('id', None)
        if not item_id:
            conn.close()
            return jsonify({'error': '缺少ID'}), 400
        fields = ', '.join(f'{k}=?' for k in data)
        conn.execute(f'UPDATE cases SET {fields} WHERE id=?', (*data.values(), item_id))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    if request.method == 'DELETE':
        item_id = request.args.get('id')
        # 删除关联图片
        row = conn.execute('SELECT image_path FROM cases WHERE id=?', (item_id,)).fetchone()
        if row and row['image_path']:
            path = os.path.join(UPLOAD_DIR, row['image_path'])
            if os.path.exists(path):
                os.remove(path)
        conn.execute('DELETE FROM cases WHERE id=?', (item_id,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})


# ===== API - 新闻 CRUD =====
@app.route('/api/news', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def api_news():
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('SELECT * FROM news ORDER BY date DESC').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])

    if request.method == 'POST':
        data = request.get_json()
        conn.execute(
            'INSERT INTO news (date, title, summary, image_path, sort_order) VALUES (?, ?, ?, ?, ?)',
            (data.get('date', ''), data['title'], data.get('summary', ''),
             data.get('image_path', ''), data.get('sort_order', 0)))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    if request.method == 'PUT':
        data = request.get_json()
        item_id = data.pop('id', None)
        if not item_id:
            conn.close()
            return jsonify({'error': '缺少ID'}), 400
        fields = ', '.join(f'{k}=?' for k in data)
        conn.execute(f'UPDATE news SET {fields} WHERE id=?', (*data.values(), item_id))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    if request.method == 'DELETE':
        item_id = request.args.get('id')
        row = conn.execute('SELECT image_path FROM news WHERE id=?', (item_id,)).fetchone()
        if row and row['image_path']:
            path = os.path.join(UPLOAD_DIR, row['image_path'])
            if os.path.exists(path):
                os.remove(path)
        conn.execute('DELETE FROM news WHERE id=?', (item_id,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})


# ===== API - 联系信息 =====
@app.route('/api/contact', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def api_contact():
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('SELECT * FROM contact_info ORDER BY sort_order').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])

    if request.method == 'POST':
        data = request.get_json()
        conn.execute(
            'INSERT INTO contact_info (icon, label, value, sort_order) VALUES (?, ?, ?, ?)',
            (data.get('icon', '📌'), data['label'], data['value'], data.get('sort_order', 99)))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    if request.method == 'PUT':
        data = request.get_json()
        item_id = data.pop('id', None)
        if not item_id:
            conn.close()
            return jsonify({'error': '缺少ID'}), 400
        fields = ', '.join(f'{k}=?' for k in data)
        conn.execute(f'UPDATE contact_info SET {fields} WHERE id=?', (*data.values(), item_id))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    if request.method == 'DELETE':
        item_id = request.args.get('id')
        conn.execute('DELETE FROM contact_info WHERE id=?', (item_id,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})


# ===== API - 图片上传 =====
@app.route('/api/upload', methods=['POST'])
@admin_required
def api_upload():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式，请上传 jpg/png/gif/webp'}), 400

    # 检查大小
    file.seek(0, 2)
    if file.tell() > MAX_UPLOAD_SIZE:
        return jsonify({'error': '文件太大，最大10MB'}), 400
    file.seek(0)

    ext = file.filename.rsplit('.', 1)[1].lower()
    name = uuid.uuid4().hex
    filename = f'{name}.{ext}'
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    # 生成缩略图（保持宽高比，最大宽度 800px）
    try:
        img = Image.open(filepath)
        if img.width > 800:
            ratio = 800 / img.width
            new_size = (800, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            img.save(filepath, quality=85, optimize=True)
    except Exception:
        pass

    section = request.form.get('section', 'general')
    conn = get_db()
    conn.execute('INSERT INTO images (filename, original_name, section) VALUES (?, ?, ?)',
                 (filename, file.filename, section))
    conn.commit()
    conn.close()

    return jsonify({'ok': True, 'filename': filename, 'url': f'/uploads/{filename}'})


# ===== API - 图片列表 =====
@app.route('/api/images')
@admin_required
def api_images():
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM images ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ===== API - 删除图片 =====
@app.route('/api/images/<filename>', methods=['DELETE'])
@admin_required
def api_delete_image(filename):
    filepath = os.path.join(UPLOAD_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
    conn = get_db()
    conn.execute('DELETE FROM images WHERE filename=?', (filename,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


# ===== API - 留言 =====
@app.route('/api/messages', methods=['GET', 'DELETE'])
@admin_required
def api_messages():
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute(
            'SELECT * FROM messages ORDER BY created_at DESC').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    if request.method == 'DELETE':
        msg_id = request.args.get('id')
        conn.execute('DELETE FROM messages WHERE id=?', (msg_id,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})


# ===== 前台表单提交 =====
@app.route('/api/submit-message', methods=['POST'])
def submit_message():
    data = request.get_json()
    conn = get_db()
    conn.execute(
        'INSERT INTO messages (name, phone, email, service_type, content) VALUES (?, ?, ?, ?, ?)',
        (data.get('name', ''), data.get('phone', ''), data.get('email', ''),
         data.get('service', ''), data.get('message', '')))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'message': '感谢您的留言，我们会尽快与您联系！'})


# ===== 上传文件访问 =====
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ===== 错误处理 =====
@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('index'))


if __name__ == '__main__':
    import sys
    init_db()
    # 本地开发用 127.0.0.1:5000，部署时平台会设置 PORT 环境变量
    if '--public' in sys.argv:
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
    else:
        app.run(host='127.0.0.1', port=5000, debug=False)
