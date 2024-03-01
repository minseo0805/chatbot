import markdown
from app.api.langchain.chathcx import ChatHCX
from .abc_hcx import HyperClovaX
from .chat_adj_param import ChatExecutor
from .detection import LangDetect
from .embedding import EmbeddingExecutor
from .doc_seg import SegmentationExecutor
from .translation import Translation
from app.utils.utils import create_collection
from pymilvus import Collection, connections
from app.api.user.user import UserModel
from app.config.db import db_session, execute_query_with_retry
from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.prompts import MessagesPlaceholder
from langchain.chains import LLMChain

MEMORY_KEY_PREFIX = "chat_history::"
class HyperClovaXController:
    def __init__(self):
        # 각 Executor 클래스의 인스턴스화
        self.lang_detect = LangDetect()
        self.segmentation_executor = SegmentationExecutor()
        self.embedding_executor = EmbeddingExecutor()
        self.translation = Translation()
        self.chat_executor = ChatExecutor()

    ###
    # {
    #  'messages': 'DATA',
    #  'maxTokens': '512',
    #  'temperature': '0.80',
    #  'topK': '0',
    #  'topP': '0.80',
    #  'repeatPenalty': '0.80',
    #  'stopBefore': [],
    #  'includeAiFilters': True
    # }
    def process_user_input(self, input_data):
        try:
            
            if not input_data["user_id"]:
                raise ValueError("get user id failed")
            
            
            # history_message = input_data["messages"]
            # if len(history_message) >= 3:
            #     # 배열 길이가 3 이상이면 앞의 데이터를 제거
            #     history_message = history_message[-3:]

            # temp_messages = history_message[:]

            input_text = input_data["message"]
            collection_name = input_data["collection_name"]
            # 언어 감지
            self.lang_detect.set_request_data(input_text)
            detected_language = self.lang_detect.execute()

            # 허용된 언어 목록
            allowed_languages = [
                "ko",
                "en",
                "ja",
                "zh-CN",
                "zh-TW",
                "vi",
                "th",
                "id",
                "es",
                "ru",
            ]

            # 감지된 언어가 허용된 언어 목록에 없으면 에러 반환
            if detected_language not in allowed_languages:
                return {"error": "This language is not supported"}
            print("detected_language:", detected_language)

            # 문단 분할 실행
            self.segmentation_executor.set_request_data(input_text)
            segments = self.segmentation_executor.execute()

            print("segments:", segments)
            # 임베딩 생성
            self.embedding_executor.set_request_data(input_text)
            embedding = self.embedding_executor.execute()

            # 벡터 db 조회
            # print("embedding:", embedding)
            connections.connect("default", host="milvus.claion.io", port="19530")
            search_params = {
                "metric_type": "L2",
                "offset": 0,
                "ignore_growing": False,
                # "params": {"nprobe": 10}
                "params": {"nlist": 1024},
            }
            collection = Collection(collection_name)
            print("collection", collection)
            # collection = create_collection()
            if collection_name == "visitseoul":
                query_limit_num = 10
                query_result = collection.search(
                    data=[embedding],
                    anns_field="embedding",
                    param=search_params,
                    limit=query_limit_num,
                    expr=None,
                    output_fields=["title", "menu", "url", "text"],
                )
                ##############################################
                from random import sample

                idx_list = []
                idx_list += sample(range(5), k=2)
                idx_list += sample(range(5, 10), k=1)
                ##############################################
                pre_messages = "".join(
                    [
                        f'"""추천할만한 장소\n[제목]: {query_result[0][idx].entity.get("title")}\n'
                        f'[분류]: {query_result[0][idx].entity.get("menu")}\n'
                        f'[내용]: {query_result[0][idx].entity.get("text")}\n'
                        f'[URL]: {query_result[0][idx].entity.get("url")}"""\n'
                        # for idx in range(query_limit_num)
                        for idx in idx_list
                    ]
                )
            elif collection_name == "custom_visitseoul":
                query_limit_num = 3
                query_result = collection.search(
                    data=[embedding],
                    anns_field="embedding",
                    param=search_params,
                    limit=query_limit_num,
                    expr=None,
                    # output_fields=['title', 'menu', 'url', 'text']
                    output_fields=["ref_txt"],
                )

                pre_messages = "".join(
                    [
                        f'"""##{idx+1}번\n{query_result[0][idx].entity.get("ref_txt")}\n'
                        for idx in range(query_limit_num)
                    ]
                )

            # 번역 (한국어가 아닐 경우에만)
            translated_text = input_text
            if detected_language != "ko":
                self.translation.set_request_data(detected_language, "ko", input_text)
                translated_text = self.translation.execute()
                if translated_text is None:
                    raise ValueError("Translation failed")

            # 대화 응답을 포함하여 전체 처리 결과를 반환
            self.chat_executor = ChatExecutor()
            # hapi_key = db.session.query(UserModel).filter_by(user_id=input_data["user_id"]).get("hapi_key")

            user = execute_query_with_retry(
                user_execute_query, user_id=input_data["user_id"]
            )
            hapi_key = user.hapi_key
            if hapi_key is None:
                raise ValueError("ChatExecutor  or hapi_key failed")

            # temp_messages.append(
            #     {
            #         "role": "user",
            #         "content": f"{pre_messages}\n질문: {translated_text}",
            #     }
            # )
            # self.chat_executor.set_api_key(hapi_key)
            # self.chat_executor.set_request_data(
            #     messages=temp_messages,
            #     system_message=input_data["system_message"],
            #     max_tokens=input_data["max_tokens"],
            #     temperature=input_data["temperature"],
            #     top_k=input_data["top_k"],
            #     top_p=input_data["top_p"],
            #     repeat_penalty=input_data["repeat_penalty"],
            # )

            # chat_response = self.chat_executor.execute()
            # if chat_response is None:
            #     raise ValueError("Chat execution failed")
            
            llm = ChatHCX()
            # print("hapi_key ::", hapi_key)
            llm.set_hapi_key(api_key=hapi_key)
            llm.set_request_data(
                max_tokens=input_data["max_tokens"],
                temperature=input_data["temperature"],
                top_k=input_data["top_k"],
                top_p=input_data["top_p"],
                repeat_penalty=input_data["repeat_penalty"],
            )
            memory_key = MEMORY_KEY_PREFIX +  input_data["user_id"] 
            memory = ConversationBufferMemory(memory_key=memory_key, return_messages=True)
            input = f"질문:{input_text}\n참고할 내용 {pre_messages}\n"
            prompt = ChatPromptTemplate.from_messages([
                # SystemMessagePromptTemplate.from_template("당신은 여행 코스를 추천해주는 Assistant입니다."), 
                SystemMessagePromptTemplate.from_template(input_data["system_message"]), 
                MessagesPlaceholder(variable_name=memory_key),
                HumanMessagePromptTemplate.from_template("{input}"),
            ])
            
            llm_chain = LLMChain(llm=llm, 
                     prompt=prompt,
                     verbose=True,
                     memory=memory)
            # chat_response = llm_chain.invoke({"input": pre_messages + '\n Input Data\n' + translated_text})
            chat_response = llm_chain.invoke({"input": input})
            # result = llm_chain.invoke({"input": content})
            print("chat_response ::", chat_response)
            print("chat_response[text]", chat_response["text"])
            chat_response["content"] = markdown.markdown(chat_response["text"])
            # 재번역 (한국어가 아닐 경우에만)
            if detected_language != "ko":
                self.translation.set_request_data(
                    "ko", detected_language, chat_response["content"]
                )
                chat_response["content"] = self.translation.execute()
                if chat_response["content"] is None:
                    raise ValueError("Translation failed")

            # 전체 처리 결과 반환
            return {
                "language": detected_language,
                "segments": segments,
                "embedding": embedding,
                "translated_text": translated_text,
                "chat_response": chat_response["content"],
                # "messages": history_message,
            }

        except Exception as e:
            # 오류 로깅 및 오류 메시지 반환
            print(f"An error occurred: {e}")
            return {"error": str(e)}

        ###

    # {
    #  'messages': 'DATA',
    #  'maxTokens': '512',
    #  'temperature': '0.80',
    #  'topK': '0',
    #  'topP': '0.80',
    #  'repeatPenalty': '0.80',
    #  'stopBefore': [],
    #  'includeAiFilters': True
    # }
    def simple_process_user_input(self, input_data):
        try:
            input_text = input_data["message"]
            # 언어 감지
            self.lang_detect.set_request_data(input_text)
            detected_language = self.lang_detect.execute()

            # 허용된 언어 목록
            allowed_languages = [
                "ko",
                "en",
                "ja",
                "zh-CN",
                "zh-TW",
                "vi",
                "th",
                "id",
                "es",
                "ru",
            ]

            # 감지된 언어가 허용된 언어 목록에 없으면 에러 반환
            if detected_language not in allowed_languages:
                return {"error": "This language is not supported"}
            print("detected_language:", detected_language)

            # 문단 분할 실행
            self.segmentation_executor.set_request_data(input_text)
            segments = self.segmentation_executor.execute()

            print("segments:", segments)

            # 번역 (한국어가 아닐 경우에만)
            translated_text = input_text
            if detected_language != "ko":
                self.translation.set_request_data(detected_language, "ko", input_text)
                translated_text = self.translation.execute()
                if translated_text is None:
                    raise ValueError("Translation failed")

            # 대화 응답을 포함하여 전체 처리 결과를 반환
            self.chat_executor = ChatExecutor()
            # hapi_key = db.session.query(UserModel).filter_by(user_id=input_data["user_id"]).get("hapi_key")

            user = execute_query_with_retry(
                user_execute_query, user_id=input_data["user_id"]
            )
            hapi_key = user.hapi_key
            if hapi_key is None:
                raise ValueError("ChatExecutor  or hapi_key failed")

            self.chat_executor.set_api_key(hapi_key)
            self.chat_executor.set_request_data(
                messages=[
                    {
                        "role": "user",
                        "content": translated_text,
                    }
                ],
                system_message=input_data["system_message"],
                max_tokens=input_data["max_tokens"],
                temperature=input_data["temperature"],
                top_k=input_data["top_k"],
                top_p=input_data["top_p"],
                repeat_penalty=input_data["repeat_penalty"],
            )
            chat_response = self.chat_executor.execute()
            if chat_response is None:
                raise ValueError("Chat execution failed")

            # 재번역 (한국어가 아닐 경우에만)
            if detected_language != "ko":
                self.translation.set_request_data(
                    "ko", detected_language, chat_response["content"]
                )
                chat_response["content"] = self.translation.execute()
                if chat_response["content"] is None:
                    raise ValueError("Translation failed")

            # 전체 처리 결과 반환
            return {
                "language": detected_language,
                "segments": segments,
                "translated_text": translated_text,
                "chat_response": chat_response,
            }

        except Exception as e:
            # 오류 로깅 및 오류 메시지 반환
            print(f"An error occurred: {e}")
            return {"error": str(e)}


def user_execute_query(user_id):
    return db_session.query(UserModel).filter_by(user_id=user_id).first()


