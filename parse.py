"""
#     "4. **Direct Data Only:** Your output should contain only the data that is explicitly requested, with no other text.
#     "1. **Extract Information:** extract the information that directly matches the provided description: {parse_description}. "
# 2. "**No Extra Content:** Do not include any additional text, comments, or explanations in your response. 

"Please follow these instructions carefully: \n\n"
    "1. **Basic setting** you basic setting is to return most of the text content as long as it matches the provided description: {parse_description} "
    "2. We are specifically interested in the text that explain concepts, code explanations, the content of code blocks, and tables related to the topic. "
    "3. Dont return comments about the content or what you are about to do, if the information dont match the provided description, return all the content {dom_content} ."
"""


from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

template = (
    "You are tasked with extracting and structuring information from the following text content: {dom_content}. "
    "Based on the user's description: {parse_description}, extract the relevant data and return it as a JSON object. "
    "IMPORTANT FIELD NAMING RULES: "
    "- Use Vietnamese field names without spaces or special characters "
    "- Convert Vietnamese field names to camelCase format "
    "- Examples: 'Họ và tên' → 'HoVaTen', 'Năm sinh' → 'NamSinh', 'Quê quán' → 'QueQuan', "
    "'Trình độ chuyên môn' → 'TrinhDoChuyenMon', 'Chức vụ' → 'ChucVu', 'Đoàn ĐBQH' → 'DoanDBQH', "
    "'Đạt % số phiếu' → 'SoPhieu', 'Số phiếu' → 'SoPhieu' "
    "If you find multiple items (like multiple people), return them as a list of JSON objects with the same field structure. "
    "Each JSON object should represent one complete record (e.g., one person's information). "
    "Only return valid JSON, no additional text or explanations."
)

# Lấy tên model từ biến môi trường, mặc định là llama3:latest
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")
model = OllamaLLM(model=OLLAMA_MODEL)

def normalize_field_names(data):
    """
    Chuẩn hóa tên field trong dữ liệu JSON để phù hợp với Excel
    """
    field_mapping = {
        # Họ và tên
        'họ và tên': 'HoVaTen',
        'họ tên': 'HoVaTen', 
        'tên': 'HoVaTen',
        'name': 'HoVaTen',
        'fullname': 'HoVaTen',
        'ho_va_ten': 'HoVaTen',
        
        # Năm sinh
        'năm sinh': 'NamSinh',
        'birth_year': 'NamSinh',
        'year_of_birth': 'NamSinh',
        'nam_sinh': 'NamSinh',
        
        # Quê quán
        'quê quán': 'QueQuan',
        'que_quan': 'QueQuan',
        'hometown': 'QueQuan',
        'origin': 'QueQuan',
        
        # Trình độ chuyên môn
        'trình độ chuyên môn': 'TrinhDoChuyenMon',
        'trinh_do_chuyen_mon': 'TrinhDoChuyenMon',
        'education': 'TrinhDoChuyenMon',
        'qualification': 'TrinhDoChuyenMon',
        
        # Chức vụ
        'chức vụ': 'ChucVu',
        'chuc_vu': 'ChucVu',
        'position': 'ChucVu',
        'title': 'ChucVu',
        
        # Đoàn ĐBQH
        'đoàn đbqh': 'DoanDBQH',
        'doan_dbqh': 'DoanDBQH',
        'delegation': 'DoanDBQH',
        
        # Số phiếu
        'đạt % số phiếu': 'SoPhieu',
        'số phiếu': 'SoPhieu',
        'so_phieu': 'SoPhieu',
        'votes': 'SoPhieu',
        'vote_percentage': 'SoPhieu'
    }
    
    def normalize_item(item):
        if isinstance(item, dict):
            normalized = {}
            for key, value in item.items():
                # Tìm key mapping phù hợp
                normalized_key = key
                for original, mapped in field_mapping.items():
                    if original.lower() in key.lower():
                        normalized_key = mapped
                        break
                normalized[normalized_key] = value
            return normalized
        return item
    
    if isinstance(data, list):
        return [normalize_item(item) for item in data]
    elif isinstance(data, dict):
        return normalize_item(data)
    return data

def parse_with_ollama(dom_chunks, parse_description):
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    parsed_results = []
    all_data = []

    for i, chunk in enumerate(dom_chunks, start=1):
        response = chain.invoke(
            {"dom_content": chunk, "parse_description": parse_description}
        )
        print(f"Parsed batch: {i} of {len(dom_chunks)}")
        parsed_results.append(response)
        
        # Thử parse JSON từ response
        try:
            # Làm sạch response để lấy JSON
            cleaned_response = clean_json_response(response)
            json_data = json.loads(cleaned_response)
            
            # Chuẩn hóa tên field
            json_data = normalize_field_names(json_data)
            
            # Nếu là list, extend vào all_data
            if isinstance(json_data, list):
                all_data.extend(json_data)
            # Nếu là dict, append vào all_data
            elif isinstance(json_data, dict):
                all_data.append(json_data)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Không thể parse JSON từ batch {i}: {e}")
            # Giữ response gốc nếu không parse được JSON
            continue

    # Lưu dữ liệu vào session state để có thể tải xuống
    return {
        'text_results': parsed_results,
        'structured_data': all_data,
        'combined_text': "\n".join(parsed_results)
    }

def clean_json_response(response):
    """
    Làm sạch response để lấy JSON hợp lệ
    """
    # Tìm JSON trong response
    json_match = re.search(r'\{.*\}|\[.*\]', response, re.DOTALL)
    if json_match:
        return json_match.group()
    
    # Nếu không tìm thấy JSON pattern, thử làm sạch basic
    cleaned = response.strip()
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    
    return cleaned.strip()
