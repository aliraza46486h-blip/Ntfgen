import requests
import json
import os
import time
import concurrent.futures
from datetime import datetime

if not os.path.exists("cookies"):
    os.makedirs("cookies")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    print("=" * 30)
    print("  🎬 NETFLIX TOKEN GENERATOR SITE BYPASSED")
    print("=" * 30)
    print()

def get_cookie_from_file():
    cookie_files = [f for f in os.listdir("cookies") if f.endswith('.txt')]
    
    if not cookie_files:
        print("❌ No cookie files found in 'cookies' folder!")
        print("\n💡 Please add your Netflix cookie in a .txt file in the 'cookies' folder")
        print("   Example: cookies/netflix_cookie.txt")
        return None
    
    print("\n📁 Available cookie files:")
    for i, file in enumerate(cookie_files, 1):
        print(f"   {i}. {file}")
    
    try:
        choice = input(f"\n👉 Select cookie file (1-{len(cookie_files)}): ")
        idx = int(choice) - 1
        if 0 <= idx < len(cookie_files):
            with open(f"cookies/{cookie_files[idx]}", 'r') as f:
                cookie = f.read().strip()
                print(f"\n✅ Loaded: {cookie_files[idx]}")
                return cookie
        else:
            print("❌ Invalid selection!")
            return None
    except:
        print("❌ Invalid input!")
        return None

def parse_webshare_proxy(proxy_string):
    parts = proxy_string.split(':')
    
    if len(parts) == 4:
        host, port, username, password = parts
        proxy_url = f'http://{username}:{password}@{host}:{port}'
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    elif len(parts) == 2:
        return {
            'http': f'http://{proxy_string}',
            'https': f'http://{proxy_string}'
        }
    return None

def test_proxy_single(proxy_string):
    try:
        proxy_dict = parse_webshare_proxy(proxy_string)
        if not proxy_dict:
            return None
        
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxy_dict,
            timeout=5
        )
        if response.status_code == 200:
            return proxy_string
    except:
        pass
    return None

def get_working_proxies(proxies):
    print(f"\n[*] Testing {len(proxies)} proxies...")
    
    working = []
    for proxy in proxies:
        if test_proxy_single(proxy):
            working.append(proxy)
            if ':' in proxy and proxy.count(':') == 3:
                parts = proxy.split(':')
                masked = f"{parts[0]}:{parts[1]}:{parts[2][:3]}***:{parts[3][:3]}***"
                print(f"✅ Working: {masked}")
            else:
                print(f"✅ Working: {proxy}")
    
    return working

def get_proxies():
    print("\n" + "=" * 30)
    print("  PROXY SETUP")
    print("=" * 30)
    print("💡 For webshare.io rotating proxy use format:")
    print("   proxy.webshare.io:port:username:password")
    print("   Example: p.webshare.io:80:username:password")
    print("=" * 30)
    

    if os.path.exists("proxies.txt"):
        print("\n📁 Found proxies.txt")
        use_file = input("   Use proxies from file? (y/n): ").lower()
        
        if use_file == 'y':
            with open("proxies.txt", 'r') as f:
                proxies = [p.strip() for p in f.readlines() if p.strip()]
                print(f"✅ Loaded {len(proxies)} proxies from file")
                return proxies
    print("\n📝 Enter proxies (one per line)")
    print("   For webshare: host:port:username:password")
    print("   For regular: ip:port")
    print("   Type 'done' when finished")
    
    proxies = []
    while True:
        proxy = input("   > ").strip()
        if proxy.lower() == 'done':
            break
        if proxy and ':' in proxy:
            proxies.append(proxy)
            parts = proxy.split(':')
            if len(parts) == 4:
                print(f"   ✅ Added webshare proxy: {parts[0]}:{parts[1]}")
            else:
                print(f"   ✅ Added: {proxy}")
        elif proxy:
            print("   ❌ Invalid format! Use ip:port or host:port:user:pass")
    
    if proxies:
        with open("proxies.txt", 'w') as f:
            f.write("\n".join(proxies))
        print(f"\n✅ Saved {len(proxies)} proxies to proxies.txt")
    
    return proxies

def solve_captcha(question):
    try:
        question = question.replace('×', '*').replace('−', '-').replace('÷', '/')
        result = eval(question)
        return str(int(result))
    except:
        return None

def get_netflix_token(cookie, proxy_string=None):
    headers = {
        'authority': 'nftoken-api-webapp.onrender.com',
        'accept': 'application/json',
        'accept-language': 'en-MM,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'referer': 'https://nftoken-api-webapp.onrender.com/playground',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'
    }
    
    proxies = None
    if proxy_string:
        proxy_dict = parse_webshare_proxy(proxy_string)
        if proxy_dict:
            proxies = proxy_dict
    
    try:
        response = requests.get(
            'https://nftoken-api-webapp.onrender.com/v1/pg-token',
            headers=headers,
            proxies=proxies,
            timeout=10
        )
        
        if response.status_code != 200:
            return None, f"PG token failed: {response.status_code}"
        
        data = response.json()
        pg_token = data.get("token")
        captcha_sig = data.get("ans_sig")
        question = data.get("question")
        
        captcha_answer = solve_captcha(question)
        if not captcha_answer:
            return None, "Failed to solve captcha"
        
        payload = {
            'cookie': cookie,
            'pg_token': pg_token,
            'captcha_answer': captcha_answer,
            'captcha_sig': captcha_sig,
            'captcha_expected': captcha_answer
        }
        
        response = requests.post(
            'https://nftoken-api-webapp.onrender.com/v1/playground',
            headers={**headers, 'content-type': 'application/json'},
            json=payload,
            proxies=proxies,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and 'data' in result:
                return result, None
            else:
                return None, f"API error: {result.get('error', 'Unknown')}"
        elif response.status_code == 429:
            return None, "Rate limited (2/day) - Need proxy bypass"
        else:
            return None, f"Status {response.status_code}"
            
    except Exception as e:
        return None, f"Error: {str(e)[:50]}"

def save_results(cookie, data, proxy=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"result_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write("#" + "=" * 30 + "\n")
        f.write("# NETFLIX TOKEN GENERATOR RESULT\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if proxy:
            f.write(f"# Proxy used: {proxy}\n")
        f.write("#" + "=" * 30 + "\n\n")

        f.write("=" * 30 + "\n")
        f.write("ACCOUNT DETAILS\n")
        f.write("=" * 30 + "\n")
        f.write(f"Name: {data.get('Name', 'N/A')}\n")
        f.write(f"Email: {data.get('Email', 'N/A')}\n")
        f.write(f"Phone: {data.get('Phone', 'N/A')}\n")
        f.write(f"Country: {data.get('Country', 'N/A')}\n")
        f.write(f"Plan: {data.get('Plan', 'N/A')}\n")
        f.write(f"Member Since: {data.get('Memb', 'N/A')}\n")
        f.write(f"Expires: {data.get('expires', 'N/A')}\n")
        f.write(f"Profiles: {data.get('Profiles', 'N/A')}\n")
        f.write(f"Streams: {data.get('Streams', 'N/A')}\n\n")

        token = data.get('token')
        if token:
            f.write("=" * 30 + "\n")
            f.write("TOKEN\n")
            f.write("=" * 30 + "\n")
            f.write(f"{token}\n\n")

        f.write("=" * 30 + "\n")
        f.write("LOGIN LINKS\n")
        f.write("=" * 30 + "\n")
        
        pc_link = data.get('PC')
        if pc_link:
            f.write(f"PC LINK: {pc_link}\n")
        
        phone_link = data.get('Phone_Link')
        if phone_link:
            f.write(f"PHONE LINK: {phone_link}\n")
        
        tv_link = data.get('TV')
        if tv_link:
            f.write(f"TV LINK: {tv_link}\n")
        f.write("\n")

        f.write("#" * 30 + "\n")
        f.write("# COOKIE (Copy this for reuse)\n")
        f.write("#" * 30 + "\n")
        f.write(f"{cookie}\n")
    
    return filename

def display_result(result, proxy=None):
    data = result['data']
    
    print("\n" + "=" * 30)
    print("✅ SUCCESS! Netflix Account Info:")
    print("=" * 30)
    print(f"👤 Name: {data.get('Name', 'N/A')}")
    print(f"📧 Email: {data.get('Email', 'N/A')}")
    print(f"📱 Phone: {data.get('Phone', 'N/A')}")
    print(f"🌍 Country: {data.get('Country', 'N/A')}")
    print(f"📅 Member Since: {data.get('Memb', 'N/A')}")
    print(f"💳 Plan: {data.get('Plan', 'N/A')}")
    print(f"📺 Streams: {data.get('Streams', 'N/A')}")
    print(f"⏰ Expires: {data.get('expires', 'N/A')}")
    print(f"📊 Profiles: {data.get('Profiles', 'N/A')}")
    
    token = data.get('token')
    if token:
        print("\n" + "=" * 30)
        print("🎯 NETFLIX TOKEN:")
        print("=" * 30)
        print(token)
        print("=" * 30)
    
    print("\n" + "=" * 30)
    print("🔗 LOGIN LINKS:")
    print("=" * 30)
    
    pc_link = data.get('PC')
    if pc_link:
        print("\n💻 PC Login Link:")
        print(pc_link)
    
    phone_link = data.get('Phone_Link')
    if phone_link:
        print("\n📱 Phone Login Link:")
        print(phone_link)
    
    tv_link = data.get('TV')
    if tv_link:
        print("\n📺 TV Login Link:")
        print(tv_link)
    
    if proxy:
        if ':' in proxy and proxy.count(':') == 3:
            parts = proxy.split(':')
            masked = f"{parts[0]}:{parts[1]}:{parts[2][:3]}***:{parts[3][:3]}***"
            print(f"\n✅ Used proxy: {masked}")
        else:
            print(f"\n✅ Used proxy: {proxy}")

def main():
    clear_screen()
    display_banner()

    if not os.path.exists("cookies") or not os.listdir("cookies"):
        print("⚠️  No cookie files found in 'cookies' folder!")
        print("\n📝 Instructions:")
        print("   1. Create a 'cookies' folder")
        print("   2. Add your Netflix cookie in a .txt file")
        print("   3. Cookie format: netflix.com\tTRUE\t/\tFALSE\t...")
        print("\n💡 To get your Netflix cookie:")
        print("   - Login to Netflix in browser")
        print("   - Open DevTools (F12)")
        print("   - Go to Application → Cookies")
        print("   - Copy the entire cookie string")
        return

    cookie = get_cookie_from_file()
    if not cookie:
        return
    
    print("\n[*] Checking direct connection...")

    result, error = get_netflix_token(cookie)
    
    if result and result.get('success'):
        display_result(result)
        filename = save_results(cookie, result['data'])
        print(f"\n✅ Results saved to: {filename}")
        return
    
    print(f"[-] Direct connection failed: {error}")
    print("\n[*] Trying with proxy bypass...")
    
    proxies = get_proxies()
    if not proxies:
        print("❌ No proxies available!")
        return

    working = get_working_proxies(proxies)
    
    if not working:
        print("❌ No working proxies found!")
        return

    for i, proxy in enumerate(working[:5], 1):
        print(f"\n[*] Trying proxy {i}/{min(len(working), 5)}...")
        result, error = get_netflix_token(cookie, proxy)
        
        if result and result.get('success'):
            display_result(result, proxy)
            filename = save_results(cookie, result['data'], proxy)
            print(f"\n✅ Results saved to: {filename}")
            return
        else:
            print(f"   ❌ Failed: {error}")
    
    print("\n❌ All proxies failed!")
    
    print("\n" + "=" * 30)
    print("=" * 30)

if __name__ == "__main__":
    main()