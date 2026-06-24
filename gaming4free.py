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

# ================= CF（GitHub 适配：主动点击版） =================

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
        sb.is_element_present('iframe[src*="turnstile"]') or
        sb.is_element_present('input[name="cf-turnstile-response"]')
    )


def try_click_cf(sb, server_num, screenshot_dir):
    try:
        # 1. 滚动 iframe 到可视区域（提高命中率）
        sb.execute_script("""
            let frames = document.querySelectorAll('iframe');
            for (let i = 0; i < frames.length; i++) {
                frames[i].scrollIntoView({block:'center'});
            }
        """)
        time.sleep(2)

        # 2. 物理点击 / UC GUI 点击
        sb.uc_gui_click_captcha()
        sb.uc_gui_handle_captcha()

    except Exception as e:
        print(f"[CF CLICK ERROR] {e}")
        try:
            sb.save_screenshot(f"{screenshot_dir}/cf_click_fail_{server_num}.png")
        except:
            pass


def wait_for_cf_pass(sb, server_num, screenshot_dir, max_rounds=3):
    """
    GitHub Actions 专用：
    - 主动检测
    - 主动点击
    - retry
    """

    for round_idx in range(max_rounds):
        print(f"🛡️ CF round {round_idx + 1}/{max_rounds}")

        if not detect_cloudflare(sb):
            return True

        try:
            sb.save_screenshot(f"{screenshot_dir}/cf_{server_num}_r{round_idx}.png")
        except:
            pass

        time.sleep(5)

        # 🔥 核心：主动触发点击（GitHub 适配关键）
        try_click_cf(sb, server_num, screenshot_dir)

        time.sleep(8)

    return not detect_cloudflare(sb)

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
            except:
                remaining_text = "未知"
        return remaining_text

    def send_telegram_notify(self, message, photo_path=None):
        if not TG_TOKEN or not TG_CHAT_ID:
            self.log("⚠️ 未配置 TG")
            return
        try:
            if photo_path and os.path.exists(photo_path):
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                with open(photo_path, 'rb') as f:
                    requests.post(url, data={'chat_id': TG_CHAT_ID, 'caption': message}, files={'photo': f})
            else:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                requests.post(url, data={'chat_id': TG_CHAT_ID, 'text': message})
        except Exception as e:
            self.log(f"❌ TG失败: {e}")

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
                self.log("✅ 浏览器已启动")

                sb.uc_open_with_reconnect(URL_APP_PANEL, reconnect_time=5)
                self.human_wait(6, 10)

                if "login" in sb.get_current_url().lower():
                    self.log("❌ 登录失效")
                    return

                before = self.get_remaining_time(sb)

                self.log("🖱️ 点击 ADD 90 MIN")
                sb.click("//button[contains(., 'ADD 90 MIN')]")

                self.human_wait(6, 10)

                sb.save_screenshot(f"{self.screenshot_dir}/before_cf_{server_num}.png")

                # ================= CF 替换核心 =================
                self.log("🛡️ 处理 Cloudflare（GitHub 主动点击模式）...")

                ok = wait_for_cf_pass(sb, server_num, self.screenshot_dir)

                if not ok:
                    self.log("❌ CF 未通过")
                    sb.save_screenshot(f"{self.screenshot_dir}/cf_fail_{server_num}.png")
                    return
                # =================================================

                after = self.get_remaining_time(sb)

                final = f"{self.screenshot_dir}/final_{server_num}.png"
                sb.save_screenshot(final)

                msg = f"✅ [{region}] 成功\n{before} → {after}"
                self.send_telegram_notify(msg, final)

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
