import os

class Config:
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    THUMBNAIL_FOLDER = os.environ.get('THUMBNAIL_FOLDER', os.path.join(os.getcwd(), 'app', 'static', 'thumbnails'))
    MODEL_FOLDER = os.environ.get('MODEL_FOLDER', os.path.join(os.getcwd(), 'models'))
    #MODEL_FOLDER = os.path.join('F:', os.sep, 'stl_gallery', 'models')
    ITEMS_PER_PAGE = 8
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
