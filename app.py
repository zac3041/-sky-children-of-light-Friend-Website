from flask import Flask, render_template, send_from_directory, request, redirect, url_for
import os,jsonify
from flask import jsonify  # 正确！直接导入函数
from werkzeug.utils import secure_filename
import datetime
app = Flask(__name__)

# 配置上传
UPLOAD_FOLDER = 'static/image'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# 检查文件扩展名
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 获取相册图片列表
def get_photos():
    photos = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if allowed_file(filename):
                photos.append({
                    'url': f"/static/image/{filename}",
                    'name': filename
                })
    # 按修改时间倒序排列
    photos.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x['name'])), reverse=True)
    return photos

START_DATE = "2025-01-06 7:21:25"
@app.route('/')
def index():
    return render_template('index.html', start_date=START_DATE)


@app.route('/photos', methods=['GET', 'POST'])
def photos():
    if request.method == 'POST':
        # 检查是否有文件上传
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # 如果用户没有选择文件
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('photos'))

    return render_template('photos.html', photos=get_photos())
def get_text_files():
    text_dir = os.path.join(app.static_folder, 'text')
    files = []
    if os.path.exists(text_dir):
        for filename in os.listdir(text_dir):
            if filename.endswith('.txt'):
                files.append({
                    'name': filename.replace('.txt', ''),
                    'path': f'/static/text/{filename}'
                })
    return sorted(files, key=lambda x: x['name'])

@app.route('/notebook')
def notebook():
    return render_template('notebook.html', files=get_text_files())

@app.route('/get_note_content')
def get_note_content():
    try:
        filename = request.args.get('file')
        if not filename:
            return jsonify({'error': '缺少文件名参数'}), 400

        # 安全验证文件名
        if not filename.endswith('.txt'):
            return jsonify({'error': '仅支持.txt文件'}), 400

        # 构建文件路径
        text_dir = os.path.join(app.static_folder, 'text')
        filepath = os.path.join(text_dir, filename)

        # 路径安全性检查
        if not os.path.abspath(filepath).startswith(os.path.abspath(text_dir)):
            return jsonify({'error': '非法文件路径'}), 403

        # 检查文件是否存在
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        # 读取文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return jsonify({'content': content})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
# 静态文件路由
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


@app.route('/save_note', methods=['POST'])
def save_note():
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()

    if not title:
        return jsonify({'error': '标题不能为空'}), 400

    # 确保text目录存在
    text_dir = os.path.join(app.static_folder, 'text')
    os.makedirs(text_dir, exist_ok=True)

    # 安全处理文件名
    filename = f"{secure_filename(title)}.txt"
    filepath = os.path.join(text_dir, filename)

    # 防止文件名冲突
    counter = 1
    while os.path.exists(filepath):
        filename = f"{secure_filename(title)}_{counter}.txt"
        filepath = os.path.join(text_dir, filename)
        counter += 1

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/videos')
def videos_page():
    return render_template('videos.html')

@app.route('/api/videos')
def get_videos():
    import os
    video_dir = os.path.join(app.static_folder, 'video')
    videos = [f for f in os.listdir(video_dir) if f.endswith(('.mp4', '.webm', '.ogg'))]
    return jsonify(videos)


import os
from flask import request, jsonify
from werkzeug.utils import secure_filename

# 确保这些配置正确
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/video')
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov'}

# 创建上传目录（如果不存在）
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/upload-video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)

        try:
            file.save(save_path)
            print(f"文件保存到: {save_path}")  # 调试日志
            return jsonify({'message': '上传成功', 'filename': filename}), 200
        except Exception as e:
            print(f"保存文件出错: {str(e)}")  # 调试日志
            return jsonify({'error': '文件保存失败'}), 500

    return jsonify({'error': '不允许的文件类型'}), 400

if __name__ == '__main__':
    # 确保上传目录存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)