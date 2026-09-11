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


# 自定义核心策略组（新增 🤖 AI 优选 专用自动测速）
MY_CORE_GROUPS = f"""
# -------------------- 自动优选与主选择组 --------------------
自动优选 = url-test, url=http://www.gstatic.com/generate_204, interval=300, tolerance=50, policy-regex-filter={AUTO_TEST_FILTER}
🚀 节点选择 = select, 自动优选, 🇭🇰 香港节点, 🇹🇼 台湾节点, 🇯🇵 日本节点, 🇺🇸 美国节点, 🇸🇬 狮城节点, PROXY, DIRECT, REJECT, 🌐 其他节点

# -------------------- AI 专属策略组 --------------------
🤖 AI 优选 = url-test, url=https://gemini.google.com, interval=300, tolerance=50, policy-regex-filter={AI_TEST_FILTER}
🤖 AI 服务 = select, 🤖 AI 优选, 🇯🇵 日本节点, 🇹🇼 台湾节点, 🇸🇬 狮城节点, 🇺🇸 美国节点, 🚀 节点选择

# -------------------- 故障转移组 --------------------
🇭🇰 香港故转 = fallback, url=http://www.gstatic.com/generate_204, interval=120, policy-regex-filter={NO_HIGH_RATE}.*(?i)(Hong|HK|香港)
🇹🇼 台湾故转 = fallback, url=http://www.gstatic.com/generate_204, interval=120, policy-regex-filter={NO_HIGH_RATE}.*(?i)(TW|Taiwan|台湾|臺灣)
🇯🇵 日本故转 = fallback, url=http://www.gstatic.com/generate_204, interval=120, policy-regex-filter={NO_HIGH_RATE}.*(?i)(Japan|JP|日本)
🇸🇬 狮城故转 = fallback, url=http://www.gstatic.com/generate_204, interval=120, policy-regex-filter={NO_HIGH_RATE}.*(?i)(Singapore|SG|新加坡|狮城)
🇺🇸 美国故转 = fallback, url=http://www.gstatic.com/generate_204, interval=120, policy-regex-filter={NO_HIGH_RATE}.*(?i)(USA|US|United States|美国)

# -------------------- 基础地区组 --------------------
🇭🇰 香港节点 = url-test, url=http://www.gstatic.com/generate_204, interval=600, tolerance=50, policy-regex-filter={NO_HIGH_RATE}.*(?i)(Hong|HK|香港)
🇹🇼 台湾节点 = url-test, url=http://www.gstatic.com/generate_204, interval=600, tolerance=50, policy-regex-filter={NO_HIGH_RATE}.*(?i)(TW|Taiwan|台湾|臺灣)
🇯🇵 日本节点 = url-test, url=http://www.gstatic.com/generate_204, interval=600, tolerance=50, policy-regex-filter={NO_HIGH_RATE}.*(?i)(Japan|JP|日本)
🇸🇬 狮城节点 = url-test, url=http://www.gstatic.com/generate_204, interval=600, tolerance=50, policy-regex-filter={NO_HIGH_RATE}.*(?i)(Singapore|SG|新加坡|狮城)
🇺🇸 美国节点 = url-test, url=http://www.gstatic.com/generate_204, interval=600, tolerance=50, policy-regex-filter={NO_HIGH_RATE}.*(?i)(USA|US|United States|美国)
🌐 其他节点 = url-test, url=http://www.gstatic.com/generate_204, interval=600, tolerance=50, policy-regex-filter=^((?!(Hong|HK|香港|TW|Taiwan|台湾|臺灣|Japan|JP|日本|Singapore|SG|新加坡|狮城|USA|US|United States|美国)).)*$
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
url-test-url = http://www.gstatic.com/generate_204
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

    # 3. 插入自定义规则至 [Rule] 顶端
    rule_pattern = re.compile(r"(\[Rule\])", re.IGNORECASE)
    if rule_pattern.search(content):
        content = rule_pattern.sub(
            r"\1\n" + MY_CUSTOM_RULES, content, count=1
        )

    # 4. 写入文件
    with open("shadow.conf", "w", encoding="utf-8") as f:
        f.write(content)

    print(
        "shadow.conf 整合成功！新增 AI 专用优选组，GitHub/Docker 及 Gemini 规则已强化。"
    )


if __name__ == "__main__":
    merge_config()
