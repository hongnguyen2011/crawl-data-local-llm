#!/usr/bin/env python3
"""
Script để tự động tải và cập nhật ChromeDriver phiên bản mới nhất
tương thích với Chrome browser hiện tại
"""

import os
import sys
import json
import zipfile
import requests
import subprocess
import platform
from pathlib import Path

def get_chrome_version():
    """Lấy phiên bản Chrome hiện tại"""
    system = platform.system()
    try:
        if system == "Windows":
            # Thử các đường dẫn phổ biến cho Chrome trên Windows
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    # Sử dụng PowerShell để lấy version
                    cmd = f'powershell "(Get-Item \'{chrome_path}\').VersionInfo.FileVersion"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        print(f"Phát hiện Chrome version: {version}")
                        return version
                        
        elif system == "Darwin":  # macOS
            result = subprocess.run([
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"
            ], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split()[-1]
                print(f"Phát hiện Chrome version: {version}")
                return version
                
        elif system == "Linux":
            result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split()[-1]
                print(f"Phát hiện Chrome version: {version}")
                return version
                
    except Exception as e:
        print(f"Lỗi khi lấy phiên bản Chrome: {e}")
    
    return None

def get_chromedriver_version(chrome_version):
    """Lấy phiên bản ChromeDriver tương thích"""
    if not chrome_version:
        return None
        
    major_version = chrome_version.split('.')[0]
    print(f"Chrome major version: {major_version}")
    
    try:
        # Với Chrome 115+, sử dụng Chrome for Testing API
        if int(major_version) >= 115:
            # Thử API mới nhất trước
            url = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone.json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if major_version in data["milestones"]:
                    chromedriver_version = data["milestones"][major_version]["version"]
                    print(f"Phiên bản ChromeDriver tương thích: {chromedriver_version}")
                    return chromedriver_version
            
            # Nếu không tìm thấy, thử fallback với các phiên bản cũ hơn
            print(f"Không tìm thấy phiên bản chính xác cho Chrome {major_version}, thử tìm phiên bản gần nhất...")
            
            # Thử các phiên bản major gần nhất
            for fallback_version in [int(major_version) - 1, int(major_version) - 2]:
                if fallback_version >= 115:
                    if str(fallback_version) in data.get("milestones", {}):
                        chromedriver_version = data["milestones"][str(fallback_version)]["version"]
                        print(f"Sử dụng phiên bản ChromeDriver tương thích gần nhất: {chromedriver_version} (cho Chrome {fallback_version})")
                        return chromedriver_version
        
        # Với Chrome < 115, sử dụng API cũ
        url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            chromedriver_version = response.text.strip()
            print(f"Phiên bản ChromeDriver tương thích: {chromedriver_version}")
            return chromedriver_version
            
    except Exception as e:
        print(f"Lỗi khi lấy phiên bản ChromeDriver: {e}")
    
    # Fallback cuối cùng: thử tải phiên bản stable mới nhất
    try:
        print("Thử lấy phiên bản ChromeDriver stable mới nhất...")
        url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            stable_version = data.get("channels", {}).get("Stable", {}).get("version")
            if stable_version:
                print(f"Sử dụng phiên bản ChromeDriver stable: {stable_version}")
                return stable_version
    except Exception as e:
        print(f"Lỗi khi lấy phiên bản stable: {e}")
    
    return None

def download_chromedriver(version):
    """Tải ChromeDriver"""
    if not version:
        return False
        
    system = platform.system()
    architecture = platform.architecture()[0]
    
    # Xác định platform
    if system == "Windows":
        if architecture == "64bit":
            platform_name = "win64"
        else:
            platform_name = "win32"
        file_extension = ".zip"
        exe_name = "chromedriver.exe"
    elif system == "Darwin":  # macOS
        if platform.processor() == "arm":
            platform_name = "mac-arm64"
        else:
            platform_name = "mac-x64"
        file_extension = ".zip"
        exe_name = "chromedriver"
    elif system == "Linux":
        platform_name = "linux64"
        file_extension = ".zip"
        exe_name = "chromedriver"
    else:
        print(f"Hệ điều hành không được hỗ trợ: {system}")
        return False
    
    try:
        major_version = int(version.split('.')[0])
        
        if major_version >= 115:
            # Sử dụng Chrome for Testing API
            download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/{platform_name}/chromedriver{file_extension}"
        else:
            # Sử dụng API cũ
            download_url = f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_{platform_name}{file_extension}"
        
        print(f"Đang tải ChromeDriver từ: {download_url}")
        
        response = requests.get(download_url, timeout=30)
        if response.status_code == 200:
            # Lưu file zip
            zip_filename = f"chromedriver_{version}.zip"
            with open(zip_filename, 'wb') as f:
                f.write(response.content)
            
            # Giải nén
            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                zip_ref.extractall("./")
            
            # Di chuyển file chromedriver đến thư mục hiện tại
            if major_version >= 115:
                # Với Chrome 115+, file được extract vào thư mục con
                extracted_path = f"chromedriver-{platform_name}/{exe_name}"
                if os.path.exists(extracted_path):
                    # Xóa file cũ nếu có
                    if os.path.exists(exe_name):
                        os.remove(exe_name)
                    # Di chuyển file mới
                    os.rename(extracted_path, exe_name)
                    # Xóa thư mục tạm
                    import shutil
                    shutil.rmtree(f"chromedriver-{platform_name}")
            else:
                # Với Chrome < 115, file được extract trực tiếp
                if os.path.exists(exe_name) and exe_name != "chromedriver.exe":
                    os.rename(exe_name, "chromedriver.exe")
            
            # Xóa file zip
            os.remove(zip_filename)
            
            # Cấp quyền thực thi trên Unix-like systems
            if system != "Windows":
                os.chmod("chromedriver.exe" if exe_name == "chromedriver.exe" else exe_name, 0o755)
            
            print(f"ChromeDriver {version} đã được tải xuống và cập nhật thành công!")
            return True
        else:
            print(f"Không thể tải ChromeDriver. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Lỗi khi tải ChromeDriver: {e}")
        return False

def download_manual_chromedriver():
    """Tải ChromeDriver thủ công với phiên bản gần nhất có sẵn"""
    print("\n=== Tải ChromeDriver thủ công ===")
    
    # Danh sách các phiên bản có thể có
    potential_versions = [
        "137.0.7151.120",  # Chrome 137 stable
        "137.0.7151.104", 
        "136.0.6898.116",  # Chrome 136 stable
        "135.0.6761.94",   # Chrome 135 stable
    ]
    
    system = platform.system()
    if system == "Windows":
        platform_name = "win64"
        exe_name = "chromedriver.exe"
    else:
        print("Chức năng tải thủ công hiện chỉ hỗ trợ Windows.")
        return False
    
    for version in potential_versions:
        print(f"Thử tải ChromeDriver {version}...")
        try:
            download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/{platform_name}/chromedriver.zip"
            
            response = requests.get(download_url, timeout=20)
            if response.status_code == 200:
                print(f"✅ Tìm thấy ChromeDriver {version}!")
                
                # Lưu và giải nén
                zip_filename = f"chromedriver_{version}.zip"
                with open(zip_filename, 'wb') as f:
                    f.write(response.content)
                
                with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                    zip_ref.extractall("./")
                
                # Di chuyển file
                extracted_path = f"chromedriver-{platform_name}/{exe_name}"
                if os.path.exists(extracted_path):
                    if os.path.exists(exe_name):
                        os.remove(exe_name)
                    os.rename(extracted_path, exe_name)
                    import shutil
                    shutil.rmtree(f"chromedriver-{platform_name}")
                
                os.remove(zip_filename)
                print(f"✅ ChromeDriver {version} đã được cài đặt thành công!")
                return True
            else:
                print(f"❌ Không tìm thấy ChromeDriver {version}")
                
        except Exception as e:
            print(f"❌ Lỗi khi tải {version}: {e}")
    
    return False

def main():
    """Hàm chính"""
    print("=== Công cụ cập nhật ChromeDriver tự động ===")
    print("Đang kiểm tra phiên bản Chrome hiện tại...")
    
    # Lấy phiên bản Chrome
    chrome_version = get_chrome_version()
    if not chrome_version:
        print("Không thể phát hiện phiên bản Chrome. Vui lòng đảm bảo Chrome đã được cài đặt.")
        print("Thử tải ChromeDriver thủ công...")
        return download_manual_chromedriver()
    
    # Lấy phiên bản ChromeDriver tương thích
    chromedriver_version = get_chromedriver_version(chrome_version)
    if not chromedriver_version:
        print("Không thể xác định phiên bản ChromeDriver tương thích.")
        print("Thử tải ChromeDriver thủ công...")
        return download_manual_chromedriver()
    
    # Kiểm tra xem đã có ChromeDriver phiên bản này chưa
    if os.path.exists("chromedriver.exe"):
        try:
            result = subprocess.run(["./chromedriver.exe", "--version"], 
                                 capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                current_version = result.stdout.split()[1]
                if current_version == chromedriver_version:
                    print(f"ChromeDriver đã ở phiên bản mới nhất: {current_version}")
                    return True
                else:
                    print(f"ChromeDriver hiện tại: {current_version}, cần cập nhật lên: {chromedriver_version}")
        except Exception:
            print("Không thể kiểm tra phiên bản ChromeDriver hiện tại.")
    
    # Tải ChromeDriver mới
    print("Đang tải ChromeDriver...")
    success = download_chromedriver(chromedriver_version)
    
    if success:
        print("✅ Cập nhật ChromeDriver thành công!")
        print("Bây giờ bạn có thể chạy AI Web Scraper mà không gặp lỗi version mismatch.")
    else:
        print("❌ Cập nhật ChromeDriver thất bại.")
        print("Thử tải ChromeDriver thủ công...")
        success = download_manual_chromedriver()
        
        if not success:
            print("❌ Tất cả các phương thức đều thất bại.")
            print("Bạn có thể thử tải thủ công từ: https://chromedriver.chromium.org/downloads")
    
    return success

if __name__ == "__main__":
    main() 