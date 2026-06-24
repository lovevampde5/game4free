import time
import os
import json
import re
import random
import requests

# ================= 环境 =================
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":1"

if "XAUTHORITY" not in os.environ:
    if os.path.exists("/home/headless/.Xauthority"):
        os.environ["XAUTHORITY"] = "/home/headless/.Xauthority"

from seleniumbase import SB


# ================= CF 强化模块 V2 =================
def stealth_browser_hardening(sb):
    """
    🔥 强化：降低 automation fingerprint
    """

    try:
        # 1. navigator spoof（关键）
        sb.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # 2. Chrome runtime spoof
        sb.execute_script("""
            window.chrome = {
                runtime: {}
            };
        """)

        # 3. plugins spoof
        sb.execute_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        # 4. languages spoof
        sb.execute_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        print("🧠 stealth patch applied")

    except Exception as e:
        print("stealth error:", e)


def human_like_activity(sb):
    """
    🔥 模拟真实用户行为链（比 warmup 更强）
    """

    try:
        for _ in range(3):
            # scroll pattern
            sb.execute_script(f"window.scrollTo(0, {random.randint(100, 1200)});")
            time.sleep(random.uniform(1.2, 2.8))

            # mouse move event
            sb.execute_script("""
                document.dispatchEvent(new MouseEvent('mousemove', {
                    bubbles: true,
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight
                }));
            """)

            time.sleep(random.uniform(0.8, 1.5))

    except:
        pass


def cf_pre_touch(sb):
    """
    🔥 提前触发 CF 资源加载（重要）
    """

    try:
        # 提前访问 CF 相关资源域
        sb.open("https://www.cloudflare.com")
        time.sleep(random.uniform(2, 4))

        # 再回到空白页制造 session continuity
        sb.open("about:blank")
        time.sleep(1)

    except:
        pass


# ================= 主类 =================
class Game4FreeRenewal:

    def log(self, msg):
        print(time.strftime("[%H:%M:%S]"), msg, flush=True)

    def run_single_server(self, server_num, region):

        url = f"https://g4f.gg/{server_num}"

        self.log(f"🚀 start {region} {server_num}")

        with SB(
            uc=True,
            test=True,
            headed=True,
            headless=False,
            xvfb=False,
            proxy=os.getenv("PROXY", None),
            chromium_arg="--no-sandbox,--disable-dev-shm-usage,--disable-gpu"
        ) as sb:

            try:
                self.log("browser started")

                # =================🔥 强化链开始 =================
                self.log("stealth patch...")
                stealth_browser_hardening(sb)

                self.log("cf pre-touch...")
                cf_pre_touch(sb)

                self.log("human activity chain...")
                human_like_activity(sb)
                # =================================================

                self.log("open target")
                sb.open(url)
                time.sleep(random.uniform(5, 9))

                # 再次行为补偿（关键）
                human_like_activity(sb)

                if "login" in sb.get_current_url():
                    self.log("login failed")
                    return

                # 点击动作（保持你原逻辑）
                self.log("click add 90 min")
                sb.click("//button[contains(., 'ADD 90 MIN')]")
                time.sleep(random.uniform(5, 8))

                # ================= CF 软等待（不再硬 click） =================
                self.log("cf passive wait...")

                for i in range(10):
                    time.sleep(4)

                    try:
                        text = sb.get_text("body").lower()
                    except:
                        text = ""

                    if "just a moment" not in text and "checking your browser" not in text:
                        break

                    # 每轮增加“人类行为”
                    human_like_activity(sb)

                    self.log(f"cf wait {i+1}/10")

                # ===========================================================

                sb.save_screenshot(f"final_{server_num}.png")

                self.log("done")

            except Exception as e:
                self.log(f"error {e}")
                sb.save_screenshot(f"error_{server_num}.png")


# ================= 运行 =================
if __name__ == "__main__":
    Game4FreeRenewal().run_single_server("test", "demo")
