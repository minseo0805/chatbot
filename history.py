from app.api.user.user import UserModel
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.config.db import db_session, db
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from . import history_api 

   
    
# 모델 정의
class ChatHistMstrInfo(db.Model):
    __tablename__ = 'chat_hist_mstr_info'
    
    history_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey(UserModel.user_id),nullable=False)
    reg_dttm = db.Column(db.DateTime, default=datetime.utcnow)
    upd_dttm = db.Column(db.DateTime, onupdate=datetime.utcnow)



class ChatHistDetlInfo(db.Model):
    __tablename__ = 'chat_hist_detl_info'
    
    message_id = db.Column(db.Integer, primary_key=True)
    history_id = db.Column(db.Integer, db.ForeignKey(ChatHistMstrInfo.history_id), nullable=False)
    chat_role = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    reg_dttm = db.Column(db.DateTime, default=datetime.utcnow)
    upd_dttm = db.Column(db.DateTime, onupdate=datetime.utcnow)
    top_p = db.Column(db.Numeric(3, 2), nullable = True)
    top_k = db.Column(db.Integer, nullable = True)
    max_tokens = db.Column(db.Integer, nullable = True)
    temperature = db.Column(db.Numeric(3, 2), nullable = True)
    repeat_penalty = db.Column(db.Numeric(3, 2), nullable = True)
    
    
def save_chat_history(chat_data):
    current_time = db_session.query(func.now()).scalar()
    try:
        user_id = chat_data["user_id"]
        print("chat_data", chat_data)
        # 채팅 기록의 마스터 레코드 생성 및 저장 
        chat_hist_master = ChatHistMstrInfo(
            user_id=user_id,
            reg_dttm=current_time,
            upd_dttm=current_time,
        )
        db_session.add(chat_hist_master)
        db_session.flush()

        # 세부 정보 저장
        for message in chat_data['messages']:
            chat_hist_detail = ChatHistDetlInfo(
                history_id=chat_hist_master.history_id,
                chat_role=message['role'],
                content=message['content'],
                reg_dttm=current_time,
                upd_dttm=current_time,
                top_p=chat_data.get('top_p'),
                top_k=chat_data.get('top_k'),
                max_tokens=chat_data.get('max_tokens'),
                temperature=chat_data.get('temperature'),
                repeat_penalty=chat_data.get('repeat_penalty')

            )
            db_session.add(chat_hist_detail)
            
        # 시스템 메시지 저장
        system_message = chat_data.get('system_message')
        if system_message:
            chat_hist_detail = ChatHistDetlInfo(
                history_id=chat_hist_master.history_id,
                chat_role='system', # 시스템 메시지로 'role' 설정
                content=system_message,
                reg_dttm=current_time,
                upd_dttm=current_time,
                top_p=chat_data.get('top_p'),
                top_k=chat_data.get('top_k'),
                max_tokens=chat_data.get('max_tokens'),
                temperature=chat_data.get('temperature'),
                repeat_penalty=chat_data.get('repeat_penalty')
            )
            db_session.add(chat_hist_detail)
        
        db_session.commit()

    except SQLAlchemyError as e:
        db_session.rollback()
        print(f"Database error occurred: {e}")    