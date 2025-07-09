import streamlit as st
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
    parse_description = st.text_area("Mô tả những gì bạn muốn phân tích từ nội dung:")

    if st.button("Phân tích nội dung"):
        if parse_description:
            st.write("Đang phân tích nội dung...")

            try:
                # Parse the content with Ollama
                dom_chunks = split_dom_content(st.session_state.dom_content)
                parsed_result = parse_with_ollama(dom_chunks, parse_description)
                st.write(parsed_result)
            except Exception as e:
                st.error(f"Lỗi khi phân tích: {str(e)}")
