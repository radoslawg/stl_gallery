from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory, send_file, current_app as app
from app import db
from app.forms import UploadForm, SearchForm, EditForm, BulkUploadForm
from app.models import STLFile
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import random
import string
import shutil
from PIL import Image
from io import BytesIO

UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
THUMBNAIL_FOLDER = app.config['THUMBNAIL_FOLDER']
MODEL_FOLDER = app.config['MODEL_FOLDER']
ITEMS_PER_PAGE = app.config['ITEMS_PER_PAGE']

@app.route('/full_res/<path:filename>')
def full_res_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, "rb") as in_file: # opening for [r]eading as [b]inary
        img_io = BytesIO(in_file.read())
        return send_file(img_io, mimetype='image/jpeg')

@app.route('/thumbnail/<path:filename>')
def thumbnail_file(filename):
    thumbfile_name = os.path.join(THUMBNAIL_FOLDER, os.path.splitext(filename)[0] + '.jpg')
    print(thumbfile_name)
    if not os.path.exists(os.path.dirname(thumbfile_name)):
            os.makedirs(os.path.dirname(thumbfile_name))
    if os.path.exists(thumbfile_name):
        with open(thumbfile_name, "rb") as in_file: # opening for [r]eading as [b]inary
            img_io = BytesIO(in_file.read())
            return send_file(img_io, mimetype='image/jpeg')

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    # Open the image file
    with Image.open(file_path) as img:
        # Resize the image
        img.thumbnail((320, 320))
        img = img.convert('RGB')
        # Save the resized image to a BytesIO object
        img.save(thumbfile_name, 'JPEG', quality=50)
        img_io = BytesIO()
        img.save(img_io, 'JPEG', quality=50)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')

def generate_unique_filename(directory, filename):
    """
    Generate a unique filename by appending a timestamp or random string if the filename already exists.
    """
    base, extension = os.path.splitext(filename)
    while os.path.exists(os.path.join(directory, filename)):
        # Generate a unique string (timestamp + random characters)
        unique_str = datetime.now().strftime("%Y%m%d%H%M%S") + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        filename = f"{base}_{unique_str}{extension}"
    return filename

def filter_files(query, search_term):
    """Filter files based on search term"""
    terms = search_term.split()
    for term in terms:
        term = term.strip()
        query = query.filter(
            (STLFile.name.contains(term)) |
            (STLFile.description.contains(term)) |
            (STLFile.creator.contains(term)) |
            (STLFile.tags.contains(term))
        )
    return query

@app.route('/')
@app.route('/page/<int:page>')
def index(page=1):
    search_term = request.args.get('search', '', type=str)
    if search_term:
        query = STLFile.query
        query = filter_files(query, search_term)
        query = query.order_by(STLFile.upload_date.desc())  # Order by upload date descending
        pagination = query.paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=False)
    else:
        pagination = STLFile.query.order_by(STLFile.upload_date.desc()).paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=False)

    files = pagination.items
    total_pages = pagination.pages

    while len(files) < ITEMS_PER_PAGE and pagination.has_next:
        page += 1
        additional_pagination = STLFile.query.paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=False)
        files.extend(additional_pagination.items)
        total_pages = additional_pagination.pages

    return render_template('index.html', files=files, page=page, total_pages=total_pages, search_term=search_term)


@app.route('/search_more', methods=['GET'])
def search_more():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '', type=str)
    if search_term:
        query = STLFile.query
        query = filter_files(query, search_term)
        query = query.order_by(STLFile.upload_date.desc())  # Order by upload date descending
        pagination = query.paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=False)
    else:
        pagination = STLFile.query.order_by(STLFile.upload_date.desc()).paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=False)

    # Extract the directory and filename
    #directory = os.path.dirname(file.filename)
    #filename = os.path.basename(file.filename)

    files = pagination.items
    return jsonify([{
        'name': file.name,
        'creator': file.creator,
        'description': file.description,
        'tags': file.tags,
        'thumbnail': url_for('thumbnail_file', filename=file.filename),
        'full_res': url_for('full_res_file', filename=file.filename),
        'stl_model': url_for('static', filename='models/' + file.stl_model),
        'id': file.id,
    } for file in files])

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        creator = form.creator.data
        creator_folder = secure_filename(creator)
        # Ensure creator subfolder exists in both UPLOAD_FOLDER and MODEL_FOLDER
        creator_upload_folder = os.path.join(UPLOAD_FOLDER, creator_folder)
        creator_model_folder = os.path.join(MODEL_FOLDER, creator_folder)

        if not os.path.exists(creator_upload_folder):
            os.makedirs(creator_upload_folder)
        
        if not os.path.exists(creator_model_folder):
            os.makedirs(creator_model_folder)

        file = form.file.data
        filename = secure_filename(file.filename)
        filename = generate_unique_filename(creator_upload_folder, filename)
        file_path = os.path.join(creator_upload_folder, filename)
        file.save(file_path)

        # Use the same filename (without extension) for the STL model file
        stl_model_filename = None
        stl_model_file = form.stl_model.data
        if stl_model_file:
            stl_model_filename = os.path.splitext(filename)[0] + '.7z'
            stl_model_filename = secure_filename(stl_model_filename)
            stl_model_file.save(os.path.join(creator_model_folder, stl_model_filename))


        stl_file = STLFile(
            name=form.name.data,
            creator=form.creator.data,
            description=form.description.data if form.description.data else "",  # Handle optional description
            tags=form.tags.data,
            filename=os.path.join(creator_folder, filename),
            stl_model=os.path.join(creator_folder, stl_model_filename) if stl_model_filename else None,
            upload_date=datetime.utcnow()  # Set the upload date
        )
        db.session.add(stl_file)
        db.session.commit()
        flash('File uploaded successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('upload.html', form=form)

@app.route('/edit/<int:file_id>', methods=['GET', 'POST'])
def edit(file_id):
    stl_file = STLFile.query.get_or_404(file_id)
    form = EditForm(obj=stl_file)
    old_creator_folder = secure_filename(stl_file.creator)
    old_file_path = os.path.join(UPLOAD_FOLDER, stl_file.filename)
    old_stl_model_path = os.path.join(MODEL_FOLDER, stl_file.stl_model) if stl_file.stl_model else None
    new_filename = None
    new_stl_model_filename = None

    if form.validate_on_submit():
        new_creator = secure_filename(form.creator.data)
        new_creator_folder = os.path.join(UPLOAD_FOLDER, new_creator)
        new_creator_model_folder = os.path.join(MODEL_FOLDER, new_creator)

        # Ensure new creator subfolder exists
        if not os.path.exists(new_creator_folder):
            os.makedirs(new_creator_folder)
        if not os.path.exists(new_creator_model_folder):
            os.makedirs(new_creator_model_folder)

        file = form.file.data
        stl_model_file = form.stl_model.data if form.stl_model else None

        # Case 1: Both image and STL model are uploaded
        if file and stl_model_file:
            new_filename = secure_filename(file.filename)
            new_filename = generate_unique_filename(new_creator_folder, new_filename)
            new_stl_model_filename = os.path.splitext(new_filename)[0] + '.7z'
            
            # Save the new files
            file.save(os.path.join(new_creator_folder, new_filename))
            stl_model_file.save(os.path.join(new_creator_model_folder, new_stl_model_filename))
            
            # Remove old files if the creator is changed or filenames are different
            if old_creator_folder != new_creator_folder or old_file_path != os.path.join(new_creator_folder, new_filename):
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            print(old_stl_model_path)
            print(os.path.join(new_creator_model_folder, new_stl_model_filename))
            if old_stl_model_path and (old_stl_model_path != os.path.join(new_creator_model_folder, new_stl_model_filename)):
                if os.path.exists(old_stl_model_path):
                    os.remove(old_stl_model_path)

            stl_file.filename = os.path.join(new_creator, new_filename)
            stl_file.stl_model = os.path.join(new_creator, new_stl_model_filename)

        # Case 2: Only STL model is uploaded
        elif not file and stl_model_file:
            new_stl_model_filename = os.path.splitext(stl_file.filename)[0] + '.7z'
            #new_stl_model_filename = secure_filename(new_stl_model_filename)
            
            # Save the new STL model file
            stl_model_file.save(os.path.join(MODEL_FOLDER, new_stl_model_filename))
            
            # Remove old STL model file if the creator is changed or filenames are different
            if old_stl_model_path and (old_creator_folder != new_creator_folder or old_stl_model_path != os.path.join(MODEL_FOLDER, new_stl_model_filename)):
                if os.path.exists(old_stl_model_path):
                    os.remove(old_stl_model_path)
            
            stl_file.stl_model = os.path.join(new_creator, new_stl_model_filename)

        # Case 3: Only image is uploaded
        elif file and not stl_model_file:
            new_filename = secure_filename(file.filename)
            new_filename = generate_unique_filename(new_creator_folder, new_filename)
            
            # Save the new image file
            file.save(os.path.join(new_creator_folder, new_filename))
            
            # Rename the STL model file if it exists and the creator is changed
            if stl_file.stl_model:
                new_stl_model_filename = os.path.splitext(new_filename)[0] + '.7z'
                new_stl_model_path = os.path.join(new_creator_model_folder, new_stl_model_filename)
                print(old_stl_model_path)
                print(new_stl_model_path)
                if old_stl_model_path != new_stl_model_path:
                    if os.path.exists(old_stl_model_path):
                        os.rename(old_stl_model_path, new_stl_model_path)
                stl_file.stl_model = os.path.join(new_creator, new_stl_model_filename)

            # Remove old image file if the creator is changed or filenames are different
            if old_file_path != os.path.join(new_creator_folder, new_filename):
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            stl_file.filename = os.path.join(new_creator, new_filename)

        # Update the remaining fields
        stl_file.name = form.name.data
        stl_file.creator = form.creator.data
        stl_file.description = form.description.data if form.description.data else ""  # Handle optional description
        stl_file.tags = form.tags.data
        
        db.session.commit()
        flash('File updated successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit.html', form=form, stl_file=stl_file)

@app.route('/delete/<int:file_id>', methods=['GET', 'POST'])
def delete(file_id):
    stl_file = STLFile.query.get_or_404(file_id)
    try:
        # Delete the file from the file system
        os.remove(os.path.join(UPLOAD_FOLDER, stl_file.filename))
        if stl_file.stl_model:
            os.remove(os.path.join(MODEL_FOLDER, stl_file.stl_model))
    except OSError as e:
        flash(f"Error deleting file: {e}", 'danger')
    
    db.session.delete(stl_file)
    db.session.commit()
    flash('File deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/download_model/<int:file_id>', methods=['GET'])
def download_model(file_id):
    stl_file = STLFile.query.get_or_404(file_id)
    if not stl_file.stl_model:
        flash('No STL model available for this file.', 'danger')
        return redirect(url_for('index'))
    
    file_path = os.path.join(MODEL_FOLDER, stl_file.stl_model)
    print("File path: ", file_path)
    if not os.path.exists(file_path):
        flash('STL model file not found.', 'danger')
        return redirect(url_for('index'))
    
    # Extract the directory and filename
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)

    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/bulk_upload', methods=['GET', 'POST'])
def bulk_upload():
    form = BulkUploadForm()
    if form.validate_on_submit():
        directory = form.directory.data
        creator = form.creator.data
        description = form.description.data
        description=form.description.data if form.description.data else ""  # Handle optional description
        tags = form.tags.data

        # Create secure folder names based on creator
        creator_folder = secure_filename(creator)
        creator_upload_folder = os.path.join(UPLOAD_FOLDER, creator_folder)
        creator_model_folder = os.path.join(MODEL_FOLDER, creator_folder)

        # Ensure creator subfolder exists in both UPLOAD_FOLDER and MODEL_FOLDER
        if not os.path.exists(creator_upload_folder):
            os.makedirs(creator_upload_folder)
        if not os.path.exists(creator_model_folder):
            os.makedirs(creator_model_folder)

        # Allowed image extensions
        allowed_image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}

        for filename in os.listdir(directory):
            name, ext = os.path.splitext(filename)
            if ext.lower() in allowed_image_extensions:
                # Process image file
                image_path = os.path.join(directory, filename)
                image_filename = secure_filename(filename)
                image_filename = generate_unique_filename(creator_upload_folder, image_filename)
                image_dest_path = os.path.join(creator_upload_folder, image_filename)
                shutil.copy(image_path, image_dest_path)

                # Generate the STL model filename based on the photo filename
                stl_model_filename = None
                stl_model_path = os.path.join(directory, f"{name}.7z")
                if os.path.exists(stl_model_path):
                    stl_model_filename = os.path.splitext(image_filename)[0] + '.7z'
                    stl_model_dest_path = os.path.join(creator_model_folder, stl_model_filename)
                    shutil.copy(stl_model_path, stl_model_dest_path)

                # Create database entry
                stl_file = STLFile(
                    name=name,
                    creator=creator,
                    description=description,
                    tags=tags,
                    filename=os.path.join(creator_folder, image_filename),
                    stl_model=os.path.join(creator_folder, stl_model_filename) if stl_model_filename else None,
                    upload_date=datetime.utcnow()
                )
                db.session.add(stl_file)

        db.session.commit()
        flash('Files uploaded successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('bulk_upload.html', form=form)

