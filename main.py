import streamlit as st
import json
import pandas as pd
from scrape_utils import (
    scrape_website_brightdata,
    scrape_website_nobright,
    scrape_website_combined,
    scrape_website_nobright_only,
    extract_body_content,
    clean_body_content,
    split_dom_content,
)
from parse import parse_with_ollama

# Streamlit UI
st.title("AI Web Scraper")
url = st.text_input("Enter Website URL")

# Chọn phương thức scraping
scrape_method = st.selectbox(
    "Chọn phương thức scraping:",
    ("Tự động (Combined)", "Chỉ Chrome (No BrightData)", "BrightData")
)

# Step 1: Scrape the Website
if st.button("Scrape Website"):
    if url:
        st.write("Đang scraping website...")

        try:
            # Chọn phương thức scraping dựa trên lựa chọn của người dùng
            if scrape_method == "Chỉ Chrome (No BrightData)":
                dom_content = scrape_website_nobright_only(url)
            elif scrape_method == "BrightData":
                dom_content = scrape_website_brightdata(url)
            else:  # Tự động (Combined)
                dom_content = scrape_website_combined(url)
                
            body_content = extract_body_content(dom_content)
            cleaned_content = clean_body_content(body_content)

            # Store the DOM content in Streamlit session state
            st.session_state.dom_content = cleaned_content

            # Display the DOM content in an expandable text box
            with st.expander("Xem nội dung DOM"):
                st.text_area("Nội dung DOM", cleaned_content, height=300)
                
            st.success("Scraping thành công!")
            
        except Exception as e:
            st.error(f"Lỗi khi scraping: {str(e)}")
            st.info("Hãy thử sử dụng phương thức 'Chỉ Chrome (No BrightData)' nếu bạn không có cấu hình BrightData.")


# Step 2: Ask Questions About the DOM Content
if "dom_content" in st.session_state:
    st.subheader("Bước 2: Phân tích nội dung")
    
    # Thêm hướng dẫn
    with st.expander("💡 Hướng dẫn sử dụng"):
        st.write("""
        **Cách mô tả thông tin cần trích xuất:**
        - Liệt kê các thông tin cần lấy, cách nhau bằng dấu phẩy
        - Ví dụ: "Họ và tên, Năm sinh, Quê quán, Trình độ chuyên môn, Chức vụ, Đoàn ĐBQH, Đạt % số phiếu"
        
        **File Excel sẽ có các cột tương ứng:**
        - Họ và tên → HoVaTen
        - Năm sinh → NamSinh  
        - Quê quán → QueQuan
        - Trình độ chuyên môn → TrinhDoChuyenMon
        - Chức vụ → ChucVu
        - Đoàn ĐBQH → DoanDBQH
        - Đạt % số phiếu → SoPhieu
        """)
    
    parse_description = st.text_area(
        "Mô tả những gì bạn muốn phân tích từ nội dung:",
        placeholder="Ví dụ: Họ và tên, Năm sinh, Quê quán, Trình độ chuyên môn, Chức vụ, Đoàn ĐBQH, Đạt % số phiếu",
        help="Nhập các thông tin bạn muốn trích xuất, cách nhau bằng dấu phẩy"
    )

    if st.button("Phân tích nội dung"):
        if parse_description:
            st.write("Đang phân tích nội dung...")

            try:
                # Parse the content with Ollama
                dom_chunks = split_dom_content(st.session_state.dom_content)
                parsed_result = parse_with_ollama(dom_chunks, parse_description)
                
                # Lưu kết quả vào session state
                st.session_state.parsed_data = parsed_result
                
                # Hiển thị kết quả dưới dạng bảng nếu có dữ liệu structured
                if parsed_result['structured_data']:
                    st.success(f"Đã phân tích được {len(parsed_result['structured_data'])} mục dữ liệu có cấu trúc!")
                    
                    # Tạo DataFrame để hiển thị
                    df = pd.DataFrame(parsed_result['structured_data'])
                    st.subheader("Dữ liệu đã phân tích:")
                    st.dataframe(df, use_container_width=True)
                    
                    # Hiển thị thông tin về các cột
                    st.info(f"Các cột dữ liệu: {', '.join(df.columns.tolist())}")
                else:
                    # Hiển thị text nếu không có structured data
                    st.write(parsed_result['combined_text'])
                
            except Exception as e:
                st.error(f"Lỗi khi phân tích: {str(e)}")

# Step 3: Download buttons
if "parsed_data" in st.session_state:
    st.subheader("Tải xuống dữ liệu đã phân tích")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Nút tải JSON
        if st.session_state.parsed_data['structured_data']:
            json_data = json.dumps(st.session_state.parsed_data['structured_data'], 
                                 ensure_ascii=False, indent=2)
            st.download_button(
                label="📁 Tải dữ liệu JSON",
                data=json_data,
                file_name=f"parsed_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            # Nếu không có dữ liệu structured, tải text results
            json_data = json.dumps(st.session_state.parsed_data['text_results'], 
                                 ensure_ascii=False, indent=2)
            st.download_button(
                label="📁 Tải dữ liệu JSON (Text)",
                data=json_data,
                file_name=f"parsed_text_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        # Nút tải Excel
        if st.session_state.parsed_data['structured_data']:
            try:
                import pandas as pd
                import io
                
                df = pd.DataFrame(st.session_state.parsed_data['structured_data'])
                
                # Tạo buffer để lưu file Excel
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Parsed Data')
                    
                    # Lấy worksheet để format
                    worksheet = writer.sheets['Parsed Data']
                    
                    # Auto-adjust column width
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)  # Giới hạn độ rộng tối đa
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                st.download_button(
                    label="📊 Tải dữ liệu Excel",
                    data=buffer.getvalue(),
                    file_name=f"parsed_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Hiển thị preview của Excel
                st.write("**Preview dữ liệu Excel:**")
                st.dataframe(df.head(), use_container_width=True)
                
            except ImportError:
                st.error("Cần cài đặt pandas và openpyxl để xuất Excel. Chạy: pip install pandas openpyxl")
            except Exception as e:
                st.error(f"Lỗi khi tạo file Excel: {str(e)}")
        else:
            # Nếu không có dữ liệu structured, tạo Excel từ text
            try:
                import pandas as pd
                import io
                
                # Tạo DataFrame từ text results
                df = pd.DataFrame({
                    'Batch': [f"Batch {i+1}" for i in range(len(st.session_state.parsed_data['text_results']))],
                    'Content': st.session_state.parsed_data['text_results']
                })
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Parsed Text')
                    
                    # Format worksheet
                    worksheet = writer.sheets['Parsed Text']
                    worksheet.column_dimensions['A'].width = 15
                    worksheet.column_dimensions['B'].width = 80
                
                st.download_button(
                    label="📊 Tải dữ liệu Excel (Text)",
                    data=buffer.getvalue(),
                    file_name=f"parsed_text_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except ImportError:
                st.error("Cần cài đặt pandas và openpyxl để xuất Excel. Chạy: pip install pandas openpyxl")
            except Exception as e:
                st.error(f"Lỗi khi tạo file Excel: {str(e)}")
