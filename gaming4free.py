import time
import os
import json
import re
import random
import requests

# 智能环境配置
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":1"
    
if "XAUTHORITY" not in os.environ:
    if os.path.exists("/home/headless/.Xauthority"):
        os.environ["XAUTHORITY"] = "/home/headless/.Xauthority"

print(f"[DEBUG] Env DISPLAY: {os.environ.get('DISPLAY')}")
print(f"[DEBUG] Env XAUTHORITY: {os.environ.get('XAUTHORITY')}")

from seleniumbase import SB

# ================= CF（从你提取版本原样移植） =================

def detect_cloudflare(sb):
    try:
        text = sb.get_text("body").lower()
    except:
        text = ""

    return (
        "just a moment" in text or
        "checking your browser" in text or
        "verify you are human" in text or
        "challenge" in text or
        "complete the captcha" in text or
        sb.is_element_present('iframe') or
        sb.is_element_present('iframe[src*="cloudflare"]') or
        sb.is_element_present('iframe[src*="turnstile"]') or
        sb.is_element_present('input[name="cf-turnstile-response"]')
    )


def wait_for_cf_pass(sb, server_num, screenshot_dir, max_wait=180):
    start = time.time()

    while time.time() - start < max_wait:
        if not detect_cloudflare(sb):
            return True

        print("🛡️ 检测到 Cloudflare / 验证页面...")
        try:
            sb.save_screenshot(f"{screenshot_dir}/captcha_found_{server_num}.png")
        except:
            pass

        time.sleep(5)

    return False

# ===========================================================


# ================= 配置区域 =================
PROXY_URL = os.getenv("PROXY", "")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
SERVERS = os.getenv("SERVERS", "").strip()

SERVER_LIST = []
if SERVERS:
    for item in SERVERS.split("|"):
        try:
            num, region = item.split(",", 1)
            SERVER_LIST.append({"num": num.strip(), "region": region.strip()})
        except:
            print(f"⚠️ SERVERS 配置格式错误: {item}")
# ===========================================


class Game4FreeRenewal:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.screenshot_dir = os.path.join(self.BASE_DIR, "artifacts")
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    def log(self, msg):
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] [INFO] {msg}", flush=True)

    def human_wait(self, min_s=6, max_s=10):
        time.sleep(random.uniform(min_s, max_s))

    def move_mouse_human(self, sb):
        try:
            for _ in range(3):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                sb.slow_click("body", force=True)
                time.sleep(random.uniform(0.5, 1.2))
        except:
            pass

    def get_remaining_time(self, sb):
        remaining_text = "未知"
        try:
            sb.wait_for_element_visible('div.countdown-time', timeout=15)
            time.sleep(2)
            remaining_text = sb.get_text('div.countdown-time').strip()
            self.log(f"✅ 获取剩余时间成功: {remaining_text}")
        except Exception as e:
            self.log(f"⚠️ 获取剩余时间失败: {e}")
            try:
                remaining_text = sb.execute_script("""
                    var el = document.querySelector('div.countdown-time');
                    return el ? el.innerText.trim() : null;
                """)
                if remaining_text:
                    self.log(f"✅ JS获取剩余时间成功: {remaining_text}")
                else:
                    remaining_text = "未知"
            except Exception as js_e:
                self.log(f"⚠️ JS获取失败: {js_e}")
                remaining_text = "未知"
        return remaining_text

    def send_telegram_notify(self, message, photo_path=None):
        if not TG_TOKEN or not TG_CHAT_ID:
            self.log("⚠️ 未配置 TG_TOKEN 或 TG_CHAT_ID，跳过推送。")
            return
        try:
            if photo_path and os.path.exists(photo_path):
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                with open(photo_path, 'rb') as f:
                    requests.post(url, data={'chat_id': TG_CHAT_ID, 'caption': message}, files={'photo': f})
            else:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                requests.post(url, data={'chat_id': TG_CHAT_ID, 'text': message})
            self.log("✅ TG 推送已发送")
        except Exception as e:
            self.log(f"❌ TG 推送失败: {e}")

    def run_single_server(self, server_num, region):
        URL_APP_PANEL = f"https://g4f.gg/{server_num}"

        self.log("=" * 40)
        self.log(f"🚀 开始续期 [{region}] ({server_num})")
        self.log("=" * 40)

        with SB(
            uc=True,
            test=True,
            headed=True,
            headless=False,
            xvfb=False,
            chromium_arg="--no-sandbox,--disable-dev-shm-usage,--disable-gpu,--window-position=0,0,--start-maximized",
            proxy=PROXY_URL if PROXY_URL else None
        ) as sb:
            try:
                self.log("✅ 浏览器已启动！")

                sb.uc_open_with_reconnect(URL_APP_PANEL, reconnect_time=5)
                self.human_wait(6, 10)

                if "login" in sb.get_current_url().lower():
                    self.log(f"❌ 权限失效")
                    return

                timestamp_before = self.get_remaining_time(sb)

                self.log("🖱️ 点击 ADD 90 MIN")
                sb.click("//button[contains(., 'ADD 90 MIN')]")

                self.human_wait(6, 10)

                sb.save_screenshot(f"{self.screenshot_dir}/before_cf_{server_num}.png")

                # ================= CF 替换（核心） =================
                self.log("🛡️ 检测 Cloudflare...")

                ok = wait_for_cf_pass(sb, server_num, self.screenshot_dir)

                if not ok:
                    self.log("❌ CF 未通过（超时）")
                    sb.save_screenshot(f"{self.screenshot_dir}/cf_fail_{server_num}.png")
                    return
                # ===================================================

                final_screenshot = f"{self.screenshot_dir}/final_{server_num}.png"
                sb.save_screenshot(final_screenshot)

                timestamp_after = self.get_remaining_time(sb)

                msg = f"✅ [{region}] 续期成功\n{timestamp_before} → {timestamp_after}"
                self.send_telegram_notify(msg, final_screenshot)

            except Exception as e:
                self.log(f"❌ 运行异常: {e}")
                sb.save_screenshot(f"{self.screenshot_dir}/error_{server_num}.png")

    def run(self):
        if not SERVER_LIST:
            self.log("❌ 未配置 SERVERS")
            return

        for server in SERVER_LIST:
            self.run_single_server(server["num"], server["region"])


if __name__ == "__main__":
    Game4FreeRenewal().run()
