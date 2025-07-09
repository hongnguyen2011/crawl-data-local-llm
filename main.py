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
    clean_body_content_with_links_and_images,
    split_dom_content,
    analyze_content_for_missing_data,
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

# Tùy chọn crawl links và images
include_links_images = st.checkbox(
    "Crawl links và địa chỉ ảnh", 
    value=False,
    help="Khi bật, sẽ thu thập thông tin về links và URLs của hình ảnh"
)

# Tùy chọn nâng cao
with st.expander("⚙️ Cài đặt nâng cao"):
    col1, col2 = st.columns(2)
    with col1:
        chunk_size = st.selectbox(
            "Kích thước chunk xử lý:",
            [4000, 8000, 12000, 16000, 20000],
            index=1,  # Default 6000
            help="Chunk nhỏ hơn = xử lý chính xác hơn nhưng chậm hơn"
        )
    with col2:
        max_chunks = st.selectbox(
            "Số chunks tối đa:",
            [30, 50, 70, 100],
            index=1,  # Default 50
            help="Tăng để xử lý nhiều dữ liệu hơn"
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
            
            # Sử dụng hàm cleaning phù hợp dựa trên lựa chọn của người dùng
            if include_links_images:
                cleaned_content = clean_body_content_with_links_and_images(body_content, base_url=url)
            else:
                cleaned_content = clean_body_content(body_content)

            # Store the DOM content in Streamlit session state
            st.session_state.dom_content = cleaned_content

            # Display the DOM content in an expandable text box
            with st.expander("Xem nội dung DOM"):
                st.text_area("Nội dung DOM", cleaned_content, height=300)
                
            # Hiển thị thông báo về mode crawling
            if include_links_images:
                st.success("Scraping thành công! ✅ Đã bao gồm links và địa chỉ ảnh")
            else:
                st.success("Scraping thành công! ℹ️ Chỉ text content (không bao gồm links/ảnh)")
            
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
        
        **Khi bật "Crawl links và địa chỉ ảnh":**
        - Links sẽ hiển thị dạng: "Text link [LINK: url]"
        - Hình ảnh sẽ hiển thị dạng: "[IMAGE: Alt: mô tả | URL: địa chỉ]"
        - Video/Audio sẽ hiển thị dạng: "[VIDEO: url]" hoặc "[AUDIO: url]"
        - Bạn có thể yêu cầu AI trích xuất: "URLs của hình ảnh, Links trang web, Địa chỉ video"
        """)
    
    # Thay đổi placeholder dựa trên việc có bật crawl links/images hay không
    if include_links_images:
        placeholder_text = "Ví dụ: Họ và tên, Năm sinh, URLs hình ảnh, Links trang web, Địa chỉ video"
        help_text = "Nhập các thông tin bạn muốn trích xuất, bao gồm links và URLs media, cách nhau bằng dấu phẩy"
    else:
        placeholder_text = "Ví dụ: Họ và tên, Năm sinh, Quê quán, Trình độ chuyên môn, Chức vụ, Đoàn ĐBQH, Đạt % số phiếu"
        help_text = "Nhập các thông tin bạn muốn trích xuất, cách nhau bằng dấu phẩy"
    
    parse_description = st.text_area(
        "Mô tả những gì bạn muốn phân tích từ nội dung:",
        placeholder=placeholder_text,
        help=help_text
    )

    if st.button("Phân tích nội dung"):
        if parse_description:
            st.write("Đang phân tích nội dung...")

            try:
                # Parse the content with Ollama
                dom_chunks = split_dom_content(
                    st.session_state.dom_content, 
                    max_length=chunk_size, 
                    max_batches=max_chunks
                )
                parsed_result = parse_with_ollama(dom_chunks, parse_description)
                
                # Lưu kết quả vào session state
                st.session_state.parsed_data = parsed_result
                
                # Hiển thị thống kê xử lý
                if 'stats' in parsed_result:
                    stats = parsed_result['stats']
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Tổng chunks", stats['total_chunks'])
                    with col2:
                        st.metric("Chunks thành công", stats['successful_chunks'])
                    with col3:
                        st.metric("Tổng records", stats['total_records'])
                
                # Hiển thị kết quả dưới dạng bảng nếu có dữ liệu structured
                if parsed_result['structured_data']:
                    st.success(f"🎉 Đã phân tích được {len(parsed_result['structured_data'])} mục dữ liệu có cấu trúc!")
                    
                    # Tạo DataFrame để hiển thị
                    df = pd.DataFrame(parsed_result['structured_data'])
                    st.subheader("Dữ liệu đã phân tích:")
                    st.dataframe(df, use_container_width=True)
                    
                    # Hiển thị thông tin về các cột
                    st.info(f"Các cột dữ liệu: {', '.join(df.columns.tolist())}")
                    
                    # Hiển thị cảnh báo nếu có vẻ như thiếu dữ liệu
                    if 'stats' in parsed_result and parsed_result['stats']['total_records'] < 50:
                        st.warning("⚠️ Số lượng records có vẻ thấp. Đang phân tích nguyên nhân...")
                        
                        # Phân tích content để tìm nguyên nhân
                        analysis = analyze_content_for_missing_data(st.session_state.dom_content)
                        
                        if analysis['potential_issues']:
                            st.write("**Các vấn đề phát hiện:**")
                            for issue in analysis['potential_issues']:
                                st.write(f"- {issue}")
                        
                        if analysis['suggestions']:
                            st.write("**Gợi ý khắc phục:**")
                            for suggestion in analysis['suggestions']:
                                st.write(f"- {suggestion}")
                        
                        st.write("**Các bước kiểm tra khác:**")
                        st.write("- Kiểm tra mô tả phân tích có chính xác không")
                        st.write("- Thử scrape lại website với thời gian chờ lâu hơn")
                        st.write("- Thử tăng kích thước chunk hoặc số chunks tối đa")
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
