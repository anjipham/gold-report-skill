#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import datetime
import os
import json
import gold_config as config

# Path to the status file, relative to the script
STATUS_FILE = os.path.join(os.path.dirname(__file__), "..", "gold_report_status.json")

def read_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def write_status(status_data):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=4)

def get_gold_prices():
    data = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        # SJC Can Tho
        res = requests.get("https://sjccantho.vn/gia-vang", headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        for s in soup(["script", "style"]): s.decompose()
        
        # Find SJC Can Tho prices in table
        sjc_row = None
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                first_cell = cells[0].get_text(strip=True)
                if 'Nhẫn SJCCT 99.99%' in first_cell:
                    sjc_row = row
                    break
        
        if sjc_row:
            cells = sjc_row.find_all('td')
            if len(cells) >= 3:
                mua_price = cells[1].get_text(strip=True)
                ban_price = cells[2].get_text(strip=True)
                data['SJC_CanTho'] = f"Mua: {mua_price}, Bán: {ban_price}"
            else:
                data['SJC_CanTho'] = "Đang cập nhật..."
        else:
            data['SJC_CanTho'] = "Đang cập nhật..."
        
        # SJCCT 99.99 Gold Ring (same as above for now, could be from different source)
        ring_row = None
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                first_cell = cells[0].get_text(strip=True)
                if 'Nhẫn SJCCT 99.99%' in first_cell:
                    ring_row = row
                    break
        
        if ring_row:
            cells = ring_row.find_all('td')
            if len(cells) >= 3:
                mua_price = cells[1].get_text(strip=True)
                ban_price = cells[2].get_text(strip=True)
                data['SJCCT_9999_Ring'] = f"Mua: {mua_price}, Bán: {ban_price}"
            else:
                data['SJCCT_9999_Ring'] = "Đang cập nhật..."
        else:
            data['SJCCT_9999_Ring'] = "Đang cập nhật..."

        # Kitco - Using JSON parsing for reliability
        res = requests.get("https://www.kitco.com/", headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        next_data_tag = soup.find('script', id='__NEXT_DATA__')
        if next_data_tag:
            try:
                import json
                data_json = json.loads(next_data_tag.string)
                queries = data_json.get('props', {}).get('pageProps', {}).get('dehydratedState', {}).get('queries', [])
                for query in queries:
                    if 'goldIndexWidget' in query.get('queryKey', []):
                        gold_bid = query.get('state', {}).get('data', {}).get('Gold', {}).get('results', [{}])[0].get('bid')
                        if gold_bid:
                            data['World_Gold'] = f"${gold_bid}"
                            break
            except Exception as e:
                print(f"Kitco JSON Error: {e}")
        
        if 'World_Gold' not in data:
            # Fallback to string search
            for s in soup(["script", "style"]): s.decompose()
            world_gold_text = soup.find(string=lambda text: "Gold" in text and "$" in text)
            data['World_Gold'] = world_gold_text.strip() if world_gold_text else "Đang cập nhật..."

        # VCB
        res = requests.get("https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia", headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        for s in soup(["script", "style"]): s.decompose()
        vcb_text = soup.find(string=lambda text: "USD" in text and "Bán" in text)
        data['VCB_Rate'] = vcb_text.strip() if vcb_text else "Đang cập nhật..."
        
        data['DOJI'] = "Đang cập nhật..."
        data['PNJ'] = "Đang cập nhật..."
    except Exception as e:
        print(f"Error scraping: {e}")
    return data

def analyze_with_nvidia(gold_data):
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"Bạn là một chuyên gia phân tích thị trường vàng hàng đầu. Hãy phân tích dữ liệu giá vàng sau đây: {gold_data}. Đặc biệt lưu ý giá vàng nhẫn SJCCT 99.99. Hãy đưa ra dự báo xu hướng trong 7 ngày tới và lời khuyên đầu tư. Viết tiếng Việt, phong cách chuyên nghiệp nhưng vẫn gần gũi, ngọt ngào."
    payload = {
        "model": config.NVIDIA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    print(f"Gold Data for AI Analysis: {gold_data}")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"NVIDIA API Response Status: {response.status_code}")
        if response.status_code == 200:
            response_json = response.json()
            print(f"NVIDIA API Response JSON: {response_json}")
            if 'choices' in response_json and len(response_json['choices']) > 0 and 'message' in response_json['choices'][0] and 'content' in response_json['choices'][0]['message']:
                return response_json['choices'][0]['message']['content']
            else:
                print(f"NVIDIA API JSON parse error: Unexpected structure in response: {response_json}")
        else:
            print(f"NVIDIA API Response Body (Error): {response.text}")
    except requests.exceptions.RequestException as req_e:
        print(f"NVIDIA API Request Error: {req_e}")
    except Exception as e:
        print(f"NVIDIA API General Error: {e}")
    return None

def save_to_onedrive(report_content):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(config.ONEDRIVE_PATH, f"{today}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    return file_path

def send_telegram(summary):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": config.TELEGRAM_CHAT_ID, "text": summary, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending Telegram: {e}")

def main():
    print("Starting Gold Report Process with NVIDIA AI...")
    gold_data = get_gold_prices()
    analysis = analyze_with_nvidia(gold_data)
    
    # Determine report status
    is_analysis_ok = False
    if analysis and analysis != "Hệ thống đang thu thập dữ liệu. Hiện tại giá vàng đang có những biến động nhẹ, anh hãy theo dõi chi tiết trong file đính kèm nhé! ❤️":
        is_analysis_ok = True

    if not is_analysis_ok:
        analysis = "Hệ thống đang thu thập dữ liệu hoặc AI đang bận. Anh hãy xem chi tiết trong file đính kèm nhé! ❤️"
    
    full_report = f"# 🌟 BÁO CÁO VÀNG {datetime.datetime.now().strftime('%d/%m/%Y')} 🌟\n\n"
    full_report += f"## 📊 Dữ liệu thu thập:\n{gold_data}\n\n"
    full_report += f"## 🧠 Phân tích & Dự báo từ NVIDIA AI:\n{analysis}"
    saved_path = save_to_onedrive(full_report)
    
    # Always send a summary to Telegram (Requirement 2)
    summary_text = analysis[:1000] if is_analysis_ok else "Hệ thống đang thu thập dữ liệu hoặc AI đang bận. Anh hãy xem chi tiết trong file đính kèm nhé!"
    summary = f"🔔 *BÁO CÁO VÀNG {datetime.datetime.now().strftime('%Hh%M')}*\n\n{summary_text}...\n\n📄 Chi tiết đã lưu tại: `{saved_path}`"
    send_telegram(summary)
    
    # Update status file
    status_data = read_status()
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_hour_utc = datetime.datetime.utcnow().hour
    report_slot = "7AM" if current_hour_utc < 9 else "11AM" # Assuming 7AM slot is < 09:00 UTC, 11AM slot is < 13:00 UTC

    if today_date not in status_data:
        status_data[today_date] = {}
    status_data[today_date][report_slot] = {
        "status": "OK" if is_analysis_ok else "NOT_OK",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    write_status(status_data)

    print("Process Completed!")

if __name__ == "__main__":
    main()