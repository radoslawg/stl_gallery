from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired, Optional

class UploadForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    creator = StringField('Creator', validators=[DataRequired()])
    description = TextAreaField('Description')
    tags = StringField('Tags', validators=[DataRequired()])
    submit_button = SubmitField('Upload')

class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

class EditForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    creator = StringField('Creator', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    tags = StringField('Tags', validators=[DataRequired()])
    file = FileField('STL File')
    stl_model = FileField('STL Model')
    submit_button = SubmitField('Save Changes')

class BulkUploadForm(FlaskForm):
    directory = StringField('Directory', validators=[DataRequired()])
    creator = StringField('Creator', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    tags = StringField('Tags', validators=[DataRequired()])
    submit = SubmitField('Upload')    
    