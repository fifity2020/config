import re
import time
import urllib.request

UPSTREAM_URL = "https://raw.githubusercontent.com/LingJingMaster/Shadowrocket-Rules/main/Shadowrocket.conf"

# 高倍率节点排除正
NO_HIGH_RATE = r"^(?!.*([2-9]\d*(\.\d+)?|1\.[1-9]\d*)(x|X|倍)).*"

# 自动优选正则
AUTO_TEST_FILTER = f"{NO_HIGH_RATE}.*(?i)(Hong|HK|香港|TW|Taiwan|台湾|Japan|JP|日本|SG|Singapore|新加坡|KR|Korea|韩国)"

# 🤖 AI 专用优选正则（剔除香港与高倍率）
AI_TEST_FILTER = f"{NO_HIGH_RATE}.*(?i)(Japan|JP|日本|TW|Taiwan|台湾|SG|Singapore|新加坡|USA|US|美国)"

#地区正则
# 排除高倍率：匹配 1.x / 2x / 3x 等高倍率标识（若无高倍率可留空或简化）
FILTER_HK = "(?i)(Hong|HK|香港)"
FILTER_TW = "(?i)(TW|Taiwan|台湾|臺灣)"
FILTER_JP = "(?i)(Japan|JP|日本)"
FILTER_SG = "(?i)(Singapore|SG|新加坡|狮城)"
FILTER_US = "(?i)(USA|US|United States|美国)"

# 自定义核心策略组 （ 🤖 AI 优选 专用自动测速） 
MY_CORE_GROUPS = f"""
# -------------------- 自动优选与主选择组 --------------------
自动优选 = url-test, url=https://www.gstatic.com/generate_204, interval=300, tolerance=50, policy-regex-filter=(?i)(Hong|HK|香港|TW|Taiwan|台湾|Japan|JP|日本|SG|Singapore|新加坡|USA|US|美国)
🚀 节点选择 = select, 自动优选, 🇭🇰 香港节点, 🇹🇼 台湾节点, 🇯🇵 日本节点, 🇸🇬 狮城节点, 🇺🇸 美国节点, PROXY, DIRECT, REJECT, 🌐 其他节点

# -------------------- AI 专属策略组 --------------------
🤖 AI 优选 = url-test, url=https://gemini.google.com, interval=300, tolerance=50, policy-regex-filter={FILTER_JP}|{FILTER_TW}|{FILTER_SG}|{FILTER_US}
🤖 AI 服务 = select, 🤖 AI 优选, 🇯🇵 日本节点, 🇹🇼 台湾节点, 🇸🇬 狮城节点, 🇺🇸 美国节点, 🚀 节点选择

# -------------------- 故障转移组 --------------------
🇭🇰 香港故转 = fallback, url=https://www.gstatic.com/generate_204, interval=120, policy-regex-filter={FILTER_HK}
🇹🇼 台湾故转 = fallback, url=https://www.gstatic.com/generate_204, interval=120, policy-regex-filter={FILTER_TW}
🇯🇵 日本故转 = fallback, url=https://www.gstatic.com/generate_204, interval=120, policy-regex-filter={FILTER_JP}
🇸🇬 狮城故转 = fallback, url=https://www.gstatic.com/generate_204, interval=120, policy-regex-filter={FILTER_SG}
🇺🇸 美国故转 = fallback, url=https://www.gstatic.com/generate_204, interval=120, policy-regex-filter={FILTER_US}

# -------------------- 基础地区组 --------------------
🇭🇰 香港节点 = url-test, url=https://www.gstatic.com/generate_204, interval=600, tolerance=50, policy-regex-filter={FILTER_HK}
🇹🇼 台湾节点 = url-test, url=https://www.gstatic.com/generate_204, interval=600, tolerance=50, policy-regex-filter={FILTER_TW}
🇯🇵 日本节点 = url-test, url=https://www.gstatic.com/generate_204, interval=600, tolerance=50, policy-regex-filter={FILTER_JP}
🇸🇬 狮城节点 = url-test, url=https://www.gstatic.com/generate_204, interval=600, tolerance=50, policy-regex-filter={FILTER_SG}
🇺🇸 美国节点 = url-test, url=https://www.gstatic.com/generate_204, interval=600, tolerance=50, policy-regex-filter={FILTER_US}
🌐 其他节点 = select, PROXY, DIRECT
""".strip()

# 自定义注入规则（增强 AI 与 开发者/代码 规则）
MY_CUSTOM_RULES = """
# -------------------------- Gemini & OpenAI 专属高优先级分流 --------------------------
DOMAIN-KEYWORD,alkalimakersuite,🤖 AI 服务
DOMAIN-KEYWORD,openai,🤖 AI 服务
DOMAIN-KEYWORD,chatgpt,🤖 AI 服务
DOMAIN-KEYWORD,anthropic,🤖 AI 服务
DOMAIN-KEYWORD,claude,🤖 AI 服务
DOMAIN-SUFFIX,bard.google.com,🤖 AI 服务
DOMAIN-SUFFIX,gemini.google.com,🤖 AI 服务
DOMAIN-SUFFIX,generativelanguage.googleapis.com,🤖 AI 服务
DOMAIN-SUFFIX,ai.google.dev,🤖 AI 服务
DOMAIN-SUFFIX,deepmind.com,🤖 AI 服务
DOMAIN-SUFFIX,deepmind.google,🤖 AI 服务

# -------------------------- 代码托管与开发者服务 --------------------------
DOMAIN-KEYWORD,github,🐱 代码托管
DOMAIN-SUFFIX,github.com,🐱 代码托管
DOMAIN-SUFFIX,githubusercontent.com,🐱 代码托管
DOMAIN-SUFFIX,gitlab.com,🐱 代码托管
DOMAIN-SUFFIX,docker.com,🐱 代码托管
DOMAIN-SUFFIX,docker.io,🐱 代码托管

# --- Telegram 优先匹配 ---
DOMAIN-KEYWORD,telegram,🚀 节点选择
DOMAIN-KEYWORD,t.me,🚀 节点选择
IP-CIDR,91.108.4.0/22,🚀 节点选择,no-resolve
IP-CIDR,149.154.160.0/20,🚀 节点选择,no-resolve
GEOIP,TELEGRAM,🚀 节点选择

# --- X (Twitter) 优先匹配 ---
DOMAIN-SUFFIX,x.com,🚀 节点选择
DOMAIN-SUFFIX,twitter.com,🚀 节点选择
DOMAIN-SUFFIX,twimg.com,🚀 节点选择
DOMAIN-SUFFIX,t.co,🚀 节点选择

# -------------------------- IPTV 规则 --------------------------
DOMAIN-SUFFIX,4gtv.tv,🇹🇼 台湾故转
DOMAIN-SUFFIX,ofissaifreepc.akamaized.net,🇹🇼 台湾故转
DOMAIN-KEYWORD,hamivideo,🇹🇼 台湾故转
DOMAIN-SUFFIX,akamaized.net,🇹🇼 台湾故转
DOMAIN-SUFFIX,163189.xyz,🇹🇼 台湾故转
DOMAIN-SUFFIX,litv.tv,🇹🇼 台湾故转
DOMAIN-SUFFIX,ofiii.com,🇹🇼 台湾故转
DOMAIN-SUFFIX,livednow.com,🇹🇼 台湾故转
DOMAIN-SUFFIX,hinet.net,🇹🇼 台湾故转

DOMAIN-SUFFIX,todesk.com,🔯 美国故转  
DOMAIN-SUFFIX,789505.xyz,🔯 美国故转
DOMAIN-SUFFIX,706726.xyz,🔯 美国故转
DOMAIN-SUFFIX,163189.xyz,🔯 美国故转
DOMAIN-SUFFIX,zenfit.cfd,🔯 美国故转
DOMAIN-SUFFIX,pixman.passwdwork.cc.cd,🔯 美国故转
DOMAIN-SUFFIX,pixman.us.ci,🔯 美国故转
DOMAIN-SUFFIX,cdnipcs.com,🔯 美国故转
DOMAIN-SUFFIX,test96.178.indevs.in,🔯 美国故转
DOMAIN-SUFFIX,tuta.com,🔯 美国故转
DOMAIN-SUFFIX,astro.com,🔯 美国故转
DOMAIN-SUFFIX,veloxmedia.com,🔯 美国故转
DOMAIN-SUFFIX,newtvsuper.com,🔯 美国故转
DOMAIN-SUFFIX,iptv.vip-tptv.xyz,🔯 美国故转
DOMAIN-SUFFIX,migu.8plus.eu.org,🔯 美国故转
DOMAIN-SUFFIX,nodeseek.com,🔯 美国故转
DOMAIN-SUFFIX,hudsonvalleyhost.com,🔯 美国故转
DOMAIN-SUFFIX,catvod.com,🔯 美国故转
DOMAIN-SUFFIX,go-iptv.ggff.net,🔯 美国故转
DOMAIN-SUFFIX,go-iptv.us.ci,🔯 美国故转
DOMAIN-SUFFIX,z2u.com,🔯 美国故转
DOMAIN-SUFFIX,amazonaws.com,🔯 美国故转
DOMAIN-SUFFIX,cloudflare.com,🔯 美国故转
DOMAIN-SUFFIX,qzz.io,🔯 美国故转
DOMAIN-SUFFIX,bee.tzh911.qzz.io,🔯 美国故转
DOMAIN-SUFFIX,pendy.dpdns.org,🔯 美国故转
DOMAIN-SUFFIX,wrod.diver.eu.org,🔯 美国故转
DOMAIN-SUFFIX,judy.xx.kg,🔯 美国故转
DOMAIN-SUFFIX,8plus.eu.org,🔯 美国故转
DOMAIN-SUFFIX,ru8.dpdns.org,🔯 美国故转
DOMAIN-SUFFIX,vip-tptv.xyz,🔯 美国故转
DOMAIN-SUFFIX,password.xyz,🔯 美国故转
DOMAIN-SUFFIX,hudsonvalleyhost.com,🔯 美国故转
DOMAIN-SUFFIX,diver.eu.org,🔯 美国故转
DOMAIN-SUFFIX,r2.hfyrw.com,🔯 美国故转
DOMAIN-SUFFIX,hudsonvalleyhost.com,🔯 美国故转

  

DOMAIN-KEYWORD,astro,🔯 狮城故转
DOMAIN-KEYWORD,wavve,🔯 狮城故转
DOMAIN-SUFFIX,starhubgo.com,🔯 狮城故转
DOMAIN-SUFFIX,stream-link.org,🔯 狮城故转
 
DOMAIN-SUFFIX,cloudflare.com,🔯 香港故转
DOMAIN-SUFFIX,cloudflaremirrors.com,🔯 香港故转
DOMAIN-KEYWORD,mytv265,🔯 香港故转
DOMAIN-SUFFIX,now.com,🔯 香港故转
DOMAIN-SUFFIX,now-tv.com,🔯 香港故转
DOMAIN-SUFFIX,ovhcloud.com,🔯 香港故转
DOMAIN-SUFFIX,tvb.com,🔯 香港故转
DOMAIN-SUFFIX,hrtn.net,🔯 香港故转
DOMAIN-SUFFIX,4gtv.passwd.bond,🔯 香港故转
DOMAIN-SUFFIX,852851.xyz,🔯 香港故转

IP-CIDR,50.7.158.194/32,🇯🇵 日本故转
IP-CIDR,123.51.231.132/32,🇹🇼 台湾故转

DOMAIN-SUFFIX,lioncdn.net,自动优选
DOMAIN-SUFFIX,passwdword.xyz,自动优选

# 直连规则
DOMAIN-SUFFIX,mobaibox.com,DIRECT
IP-CIDR,183.207.0.0/16,DIRECT,no-resolve
DOMAIN-SUFFIX,cctv.cn,DIRECT
DOMAIN-SUFFIX,yangshipin.cn,DIRECT
DOMAIN-SUFFIX,cmvideo.cn,DIRECT
""".strip()


def fetch_upstream_config(url, retries=3):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    for attempt in range(1, retries + 1):
        try:
            print(f"正在拉取上游配置 (第 {attempt} 次尝试)...")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read().decode("utf-8")
        except Exception as e:
            print(f"第 {attempt} 次拉取失败: {e}")
            if attempt < retries:
                time.sleep(3)
            else:
                raise RuntimeError(f"无法获取上游配置文件: {e}")

def merge_config():
    content = fetch_upstream_config(UPSTREAM_URL)

    # 1. 防止 DNS 锁死
    content = re.sub(
        r"dns-server\s*=\s*https://cloudflare-dns\.com/dns-query#proxy",
        "dns-server = 223.5.5.5, 119.29.29.29, https://dns.alidns.com/dns-query",
        content,
    )
    content = re.sub(
        r"fallback-dns-server\s*=\s*https://dns\.google/dns-query#proxy",
        "fallback-dns-server = https://1.1.1.1/dns-query",
        content,
    )

    # 2. 注入全局测速参数：将参数直接拼接到 [General] 标题下方
    general_params = """[General]
url-test-url = https://www.gstatic.com/generate_204
url-test-timeout = 5"""

    content = re.sub(r"\[General\]", general_params, content, flags=re.IGNORECASE, count=1)

    # 3. 提取并清洗 [Proxy Group]
    pg_pattern = re.compile(
        r"(\[Proxy Group\][\s\S]*?)(?=\n\[|\Z)", re.IGNORECASE
    )
    pg_match = pg_pattern.search(content)

    if pg_match:
        upstream_pg_full = pg_match.group(1)

        # 清理上游重复的策略组，避免覆盖自己的 AI 组和核心组
        skip_keywords = [
            "节点选择",
            "自动优选",
            "AI 服务",
            "AI 优选",
            "香港节点",
            "台湾节点",
            "日本节点",
            "美国节点",
            "狮城节点",
            "其他节点",
            "香港故转",
            "台湾故转",
            "日本故转",
            "美国故转",
            "狮城故转",
        ]

        cleaned_upstream_lines = []
        for line in upstream_pg_full.splitlines():
            line_str = line.strip()
            if line_str.lower() == "[proxy group]" or not line_str:
                continue

            if "=" in line_str:
                var_name = line_str.split("=")[0].strip()
                if any(kw in var_name for kw in skip_keywords):
                    continue

            # 移除锁死默认节点的 policy-select-name 参数
            line_modified = re.sub(r",\s*policy-select-name=[^,]+", "", line)
            line_modified = re.sub(
                r"(📌|🚀)?\s*节点选择", "🚀 节点选择", line_modified
            )
            cleaned_upstream_lines.append(line_modified)

        new_pg_block = (
            "[Proxy Group]\n"
            + MY_CORE_GROUPS
            + "\n"
            + "\n".join(cleaned_upstream_lines)
        )
        content = (
            content[: pg_match.start()]
            + new_pg_block
            + content[pg_match.end() :]
        )

    # 4. 插入自定义规则至 [Rule] 顶端
    rule_pattern = re.compile(r"(\[Rule\])", re.IGNORECASE)
    if rule_pattern.search(content):
        content = rule_pattern.sub(
            r"\1\n" + MY_CUSTOM_RULES, content, count=1
        )

    # 5. 写入文件
    with open("shadow.conf", "w", encoding="utf-8") as f:
        f.write(content)

    print(
        "shadow.conf 整合成功！新增 AI 专用优选组，GitHub/Docker 及 Gemini 规则已强化。"
    )


if __name__ == "__main__":
    merge_config()
