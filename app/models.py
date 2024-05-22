from app import db
from datetime import datetime

class STLFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    creator = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(120), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) 
    stl_model = db.Column(db.String(256), nullable=True) 


    def __repr__(self):
        return f'<STLFile {self.name}>'
