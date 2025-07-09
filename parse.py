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
    
    "CRITICAL EXTRACTION REQUIREMENTS: "
    "- Extract ALL matching records from the content, not just a few examples "
    "- If there are 50 people mentioned, extract ALL 50 people "
    "- If there are 100 products listed, extract ALL 100 products "
    "- DO NOT limit yourself to only a few items - extract EVERYTHING that matches "
    
    "IMPORTANT FIELD NAMING RULES: "
    "- Use Vietnamese field names without spaces or special characters "
    "- Convert Vietnamese field names to camelCase format "
    "- Examples: 'Họ và tên' → 'HoVaTen', 'Năm sinh' → 'NamSinh', 'Quê quán' → 'QueQuan', "
    "'Trình độ chuyên môn' → 'TrinhDoChuyenMon', 'Chức vụ' → 'ChucVu', 'Đoàn ĐBQH' → 'DoanDBQH', "
    "'Đạt % số phiếu' → 'SoPhieu', 'Số phiếu' → 'SoPhieu', 'Địa chỉ ảnh' → 'DiaChiAnh', "
    "'URLs hình ảnh' → 'URLsHinhAnh', 'Links' → 'Links', 'Liên kết' → 'LienKet' "
    
    "SPECIAL HANDLING FOR LINKS AND MEDIA: "
    "- Links appear as: 'text [LINK: url]' - extract both text and URL if requested "
    "- Images appear as: '[IMAGE: Alt: description | URL: image_url]' - extract URLs if requested "
    "- Videos appear as: '[VIDEO: video_url]' - extract URLs if requested "
    "- Audio appears as: '[AUDIO: audio_url]' - extract URLs if requested "
    
    "OUTPUT FORMAT: "
    "- If you find multiple items (like multiple people), return them as a list of JSON objects with the same field structure "
    "- Each JSON object should represent one complete record (e.g., one person's information) "
    "- Extract ALL records found in this content chunk, not just the first few "
    "- Only return valid JSON, no additional text or explanations "
    "- If no matching data found, return an empty list: []"
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
        'vote_percentage': 'SoPhieu',
        
        # Links và Images
        'links': 'Links',
        'link': 'Links',
        'url': 'URL',
        'urls': 'URLs',
        'image': 'HinhAnh',
        'images': 'HinhAnh',
        'hình ảnh': 'HinhAnh',
        'ảnh': 'HinhAnh',
        'img': 'HinhAnh',
        'video': 'Video',
        'audio': 'Audio',
        'media': 'Media',
        'địa chỉ ảnh': 'DiaChiAnh',
        'đường dẫn': 'DuongDan',
        'liên kết': 'LienKet'
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
    successful_chunks = 0
    total_records_extracted = 0

    print(f"Bắt đầu xử lý {len(dom_chunks)} chunks...")
    
    for i, chunk in enumerate(dom_chunks, start=1):
        print(f"Đang xử lý chunk {i}/{len(dom_chunks)} (kích thước: {len(chunk)} ký tự)...")
        
        response = chain.invoke(
            {"dom_content": chunk, "parse_description": parse_description}
        )
        parsed_results.append(response)
        
        # Thử parse JSON từ response
        try:
            # Làm sạch response để lấy JSON
            cleaned_response = clean_json_response(response)
            json_data = json.loads(cleaned_response)
            
            # Chuẩn hóa tên field
            json_data = normalize_field_names(json_data)
            
            # Đếm số records từ chunk này
            chunk_records = 0
            
            # Nếu là list, extend vào all_data
            if isinstance(json_data, list):
                chunk_records = len(json_data)
                all_data.extend(json_data)
            # Nếu là dict, append vào all_data
            elif isinstance(json_data, dict) and json_data:
                chunk_records = 1
                all_data.append(json_data)
            
            if chunk_records > 0:
                successful_chunks += 1
                total_records_extracted += chunk_records
                print(f"✅ Chunk {i}: Trích xuất được {chunk_records} records")
            else:
                print(f"⚠️ Chunk {i}: Không tìm thấy dữ liệu phù hợp")
                
        except (json.JSONDecodeError, Exception) as e:
            print(f"❌ Chunk {i}: Không thể parse JSON - {e}")
            # In ra một phần response để debug
            print(f"Response preview: {response[:200]}...")
            continue

    print(f"\n📊 Kết quả tổng hợp:")
    print(f"- Tổng chunks: {len(dom_chunks)}")
    print(f"- Chunks thành công: {successful_chunks}")
    print(f"- Tổng records trích xuất: {total_records_extracted}")
    
    # Lưu dữ liệu vào session state để có thể tải xuống
    return {
        'text_results': parsed_results,
        'structured_data': all_data,
        'combined_text': "\n".join(parsed_results),
        'stats': {
            'total_chunks': len(dom_chunks),
            'successful_chunks': successful_chunks,
            'total_records': total_records_extracted
        }
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
