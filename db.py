from datetime import datetime
from app.api.file.object_storage import ObjectStorage
from app.config.db import db_session, db
from sqlalchemy import func 
from werkzeug.utils import secure_filename
import uuid
import os

MAX_FILE_SIZE = 1000 * 1024 * 1024
class ApndMstrInfo(db.Model):
    __tablename__ = 'apnd_mstr_info'
    
    apnd_uuid = db.Column(db.BigInteger, primary_key=True)
    reg_dttm = db.Column(db.DateTime, default=datetime.utcnow)
    upd_dttm = db.Column(db.DateTime, onupdate=datetime.utcnow)


class ApndDtlInfo(db.Model):
    __tablename__ = 'apnd_detl_info'
    
    apnd_uuid = db.Column(db.BigInteger, db.ForeignKey('apnd_mstr_info.apnd_uuid'), primary_key=True)
    apnd_sno = db.Column(db.Integer, primary_key=True)
    file_nm = db.Column(db.String, nullable=True)
    phys_file_nm = db.Column(db.String, nullable=True)
    file_path_nm = db.Column(db.String, nullable=True)
    file_capa = db.Column(db.Numeric, nullable=True)
    file_kd_nm = db.Column(db.String, nullable=True)
    reg_dttm = db.Column(db.DateTime, default=datetime.utcnow)
    upd_dttm = db.Column(db.DateTime, onupdate=datetime.utcnow)

    master_info = db.relationship('ApndMstrInfo')
    

"""
Insert and Update
return file_uuid
"""
def upload_file(files, file_uuid):
    
    try:
        # 데이터베이스에서 현재 가장 큰 apnd_uuid 가져오기 
        if file_uuid:
            apnd_uuid = file_uuid
        else:
            apnd_uuid = db_session.query(func.max(ApndMstrInfo.apnd_uuid)+1).scalar()
            
        
        if apnd_uuid is None:
            apnd_uuid = 0
        
        for index, file in enumerate(files, start=1):
            if file:
                filename = file.filename
                print(f"파일명: {filename}")
                
                if file.tell() > MAX_FILE_SIZE:
                    raise ValueError(f"File '{filename}' exceeds the maximum allowed size.")

                doc_type = get_type(filename)
                if not doc_type:
                    raise ValueError(f"File '{filename}' not allowd file type.")
                
                
                # 데이터베이스 기록 추가
                current_time = db_session.query(func.now()).scalar()
                master_record = ApndMstrInfo(apnd_uuid=apnd_uuid, reg_dttm=current_time, upd_dttm=current_time)
                db_session.add(master_record)
                phys_file_name = generate_uuid() + "." + doc_type
                dtl_record = ApndDtlInfo(
                    apnd_uuid=apnd_uuid,
                    apnd_sno=index,
                    file_nm=filename,
                    phys_file_nm=phys_file_name,
                    file_path_nm = os.path.join(os.environ['UPLOAD_FOLDER'], phys_file_name),
                    file_capa=file.tell(),
                    file_kd_nm=doc_type,
                    reg_dttm=current_time,
                    upd_dttm=current_time
                )
                db_session.add(dtl_record)
                file.save(dtl_record.file_path_nm)
                obs = ObjectStorage()
                obs.file_upload(bucket_name=os.environ["OS_FILE_BUCKET"], path_forder="/", object_name=phys_file_name, local_file_path=dtl_record.file_path_nm)
                
            db_session.commit()
            return apnd_uuid
    except Exception as e:
        print(f"[ERROR file upload] {e}")
        db_session.rollback()

        # Cleanup files in case of an exception
        for index, file in enumerate(files, start=1):
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(os.environ['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
        return apnd_uuid


# 파일 이름이 유효한지 확인하는 함수
def get_type(filename):
    if '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf':
        return 'pdf'
    elif '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv':
        return 'csv'
    else:
        return ''

def generate_uuid():
        # UUID 생성 및 '-' 제거
        return str(uuid.uuid4()).replace('-', '')