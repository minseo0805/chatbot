import csv
import datetime
import io
import os
import unicodedata
import ast
import pandas as pd
from app.api.file.db import upload_file, db_session
from app.api.file.object_storage import ObjectStorage
import boto3
from app.api.hyperclovax_api.collection.model import CollectionModel
from app.api.hist.history import ChatHistMstrInfo, ChatHistDetlInfo
from app.api.hist.history import save_chat_history
from app.utils.helper_functions import csv_to_vector, get_texts_from_pdf, pdf_to_vector, get_largest_font_text_with_previous, find_href_links_in_first_page
from app.utils.utils import create_collection
from . import hyperclovax_api
from .hyperclovax_controller import HyperClovaXController
from flask_jwt_extended import get_jwt_identity
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required
from pymilvus import connections, utility
from datetime import datetime
from app.utils.scraping_service import menu_find, item_finder, paging_finder, scrape_and_chunk

@hyperclovax_api.route('/simple_chat', methods=['POST'])
@jwt_required()
def simple_chat():
    input_data = request.json.get("data")
    input_data["user_id"] = get_jwt_identity()
    hyperclovax_controller = HyperClovaXController()
    response = hyperclovax_controller.simple_process_user_input(input_data)
   
    if 'error' in response:
        return jsonify({'error': response['error']}), 40

    return jsonify(response)

@hyperclovax_api.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    input_data = request.json.get("data")
    input_data["user_id"] = get_jwt_identity() 

    hyperclovax_controller = HyperClovaXController()
    response = hyperclovax_controller.process_user_input(input_data)
    # print("input data: ", input_data)
    # 채팅 기록 저장
    # save_chat_history(input_data)
   
    if 'error' in response:
        return jsonify({'error': response['error']}), 400

    return jsonify(response)


@hyperclovax_api.route('/bucket_create', methods=['GET'])
def bucket_create():
    try:
        os = ObjectStorage()
        os.create_bucket("claion-bucket")
    except Exception as e:
        print(f"[ERROR occured] bucket_create {e}")

    return jsonify("s")

@hyperclovax_api.route('/get_bucket', methods=['GET'])
def get_bucket():
    try:
        s3 = boto3.client(service_name=os.environ["OS_SERVICE_NAME"], endpoint_url=os.environ["OS_ENDPOINT_URL"], aws_access_key_id=os.environ["OS_ACCESS_KEY"],
                      aws_secret_access_key=os.environ["OS_SECRET_KEY"])
        response = s3.list_buckets()

        for bucket in response.get('Buckets', []):
            print (bucket.get('Name'))
    except Exception as e:
        print(f"[ERROR occured] get_bucket {e}")

    return jsonify("s")

# 보완 필요
# @hyperclovax_api.route('/cr', methods=['GET'])
# def cr():
#     url_list = menu_find("https://korean.visitseoul.net")
#     pg_list = paging_finder(url_list)
#     new_list = item_finder(url_list+pg_list)
    
#     # Get the length of url_list
#     url_list_length = len(new_list)
#     print("url_list_length :" , url_list_length)
#     # Define the batch size
#     batch_size = 50

#     # Process url_list in batches
   
#     for i in range(0, url_list_length, batch_size):
#         start_index = i
#         end_index = min(i + batch_size, url_list_length)
        
#         # Extract the current batch
#         current_batch = new_list[start_index:end_index]
#         print("end idx :", end_index)
#         # Process the current batch
#         try:
#             scrape_and_chunk(current_batch)
#         except Exception as e:
#             print(str(e))
#             continue
        
    
#     return jsonify("https://korean.visitseoul.net/")

@hyperclovax_api.route('/register_data', methods=['POST'])
@jwt_required()
def register_data():
    connections.connect("default", host="milvus.claion.io", port="19530")
    
    entities_list = []  # Accumulate entities for bulk insertion
    try:
        form_data = request.form.to_dict()
        form_data["user_id"] = get_jwt_identity()
        collection_model = CollectionModel(form_data)
        
        if collection_model.has_collection_id() or utility.has_collection(collection_model.collection_id):
            raise ValueError("이미 존재하는 데이터명 입니다.")
        
        cur_collection = create_collection(collection_name=collection_model.collection_id)
        df = pd.read_csv("file_info.csv", encoding="utf-8")
        files = request.files.getlist("files")

        for file in files:
            
            print("collection_model.loader_type::", collection_model.loader_type)
            if collection_model.loader_type == "pdf":
                # title, menu = get_largest_font_text_with_previous(file)
                
                # find_href_links_in_first_page(file)
                title = file.filename[:-4]
                title = unicodedata.normalize('NFC', title)
                # PDF로 부터 text 추출
                menu = df[df["제목"] == title]["메뉴"].values[0]
                url = df[df["제목"] == title]["url"].values[0]
                print("title ::", title)
                print("menu ::", menu)
                entity = {
                    "title" : title,
                    "menu"  : menu,
                    "url"   : url
                }
                texts: list[str] = get_texts_from_pdf(file)
                strip_texts = [
                    text.strip() for text in texts if text.strip()
                ]
                text = "\n".join(strip_texts)
                pdf_to_vector(entities_list, text, collection_model, entity)
            else:
                csv_file = io.TextIOWrapper(file.stream, encoding='cp949')
                csv_reader = csv.DictReader(csv_file)

                for row in csv_reader:
                    entity = {
                        "title": row["title"],
                        "menu": row["menu"],
                        "url": row["url"],
                        "text": row["text"]
                        # "embedding": ast.literal_eval(row["embedding"])
                    }
                    csv_to_vector(entities_list, collection_model, entity)
            
        ### LOAD
        # upload -> get uuid
        ### SPLIT
        # split data
        ### EMBED
        # embed data
        ### STORE
        
        # Bulk insert all entities after processing all URLs
        cur_collection.insert(entities_list)
        cur_collection.flush()
        
        uuid = upload_file(files, None)
        print("file upload success ::", uuid)
        collection_model.file_id = uuid
        collection_model.save_to_db()
        return jsonify({"message": "데이터가 등록되었습니다."}), 200
    except ValueError as ve:
        # 오류 로깅 및 오류 메시지 반환
        print(f"An ValueError occurred: {ve}")
        return jsonify({'message': str(ve)}), 202
    except Exception as e:
        # 오류 로깅 및 오류 메시지 반환
        print(f"An error occurred: {e}")
        return jsonify({'message': "알 수 없는 오류가 발생했습니다."}), 500
