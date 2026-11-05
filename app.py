from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Length
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.secret_key = 'aegis_enterprise_secure_master_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aegis_enterprise.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 1. Model Database Persisten (SQLite)
class InventoryModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_data = db.Column(db.String(150), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default='Aktif')
    dibuat_pada = db.Column(db.String(50), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# 3. Form Validasi Keamanan (Anti-XSS & Type Casting Protection)
class DeployStreamForm(FlaskForm):
    nama_data = StringField('Nama Identifikasi', validators=[DataRequired(), Length(min=3, max=140)])
    kategori = SelectField('Kategori', choices=[('COMPUTE', 'COMPUTE'), ('STORAGE', 'STORAGE'), ('SECURITY', 'SECURITY'), ('NETWORK', 'NETWORK')], validators=[DataRequired()])
    jumlah = IntegerField('Volume Unit', validators=[DataRequired(), NumberRange(min=1, max=10000)])

with app.app_context():
    db.create_all()
    # Seed data awal jika database kosong
    if InventoryModel.query.count() == 0:
        initial_data = [
            InventoryModel(nama_data='Global Telemetry Node Alpha', kategori='COMPUTE', jumlah=48, status='Aktif'),
            InventoryModel(nama_data='Orbital Storage Vault Beta', kategori='STORAGE', jumlah=12, status='Pending'),
            InventoryModel(nama_data='Quantum Encryption Stream', kategori='SECURITY', jumlah=8, status='Aktif'),
            InventoryModel(nama_data='Deep Space Relay Array', kategori='NETWORK', jumlah=3, status='Arsip')
        ]
        db.session.add_all(initial_data)
        db.session.commit()

# 2. Skalabilitas & Paginasi Data Backend
@app.route('/')
def dashboard():
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Batasi per halaman untuk performa optimal
    
    pagination = InventoryModel.query.order_by(InventoryModel.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items
    
    total_data = InventoryModel.query.count()
    total_aktif = InventoryModel.query.filter_by(status='Aktif').count()
    
    form = DeployStreamForm()
    return render_template('index.html', pagination=pagination, items=items, total_data=total_data, total_aktif=total_aktif, form=form)

@app.route('/deploy', methods=['POST'])
def deploy_stream():
    form = DeployStreamForm()
    if form.validate_on_submit():
        # Sanitasi input dasar menangkis XSS
        clean_nama = form.nama_data.data.strip().replace('<', '&lt;').replace('>', '&gt;')
        new_entry = InventoryModel(
            nama_data=clean_nama,
            kategori=form.kategori.data,
            jumlah=form.jumlah.data,
            status='Aktif'
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('Stream inventaris berhasil dideploy dan diamankan ke database persisten!', 'success')
    else:
        flash('Validasi gagal! Periksa kembali parameter input Anda.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_stream(item_id):
    item = InventoryModel.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Dataset berhasil dihapus secara permanen dari sistem.', 'danger')
    return redirect(url_for('dashboard'))

# 4. Fitur Killer: Ekspor Laporan Data ke Format CSV
@app.route('/export/csv')
def export_csv():
    items = InventoryModel.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header CSV Korporat
    writer.writerow(['Index ID', 'Nama Identifikasi', 'Subsystem / Kategori', 'Volume Akumulasi', 'Status Telemetry', 'Timestamp UTC'])
    for item in items:
        writer.writerow([f"IDX-{item.id:04d}", item.nama_data, item.kategori, item.jumlah, item.status, item.dibuat_pada])
        
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=aegis_telemetry_report.csv"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)