import re
import urllib.request

# 1. 填入第三方的远程配置 URL
UPSTREAM_URL = "https://github.com/LingJingMaster/Shadowrocket-Rules/blob/main/Shadowrocket.conf"

# 2. 你的自定义追加配置
MY_CUSTOM_GROUPS = """
香港节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "^(?!(.*(\\[[2-9]x\\]|\\[1[0-9]x\\]|\\[0\\.[5-9]x\\]|2倍|3倍))).*(?i)(Hong|HK|香港|🇭🇰)"
自动优选 = url-test, url = "http://www.gstatic.com/generate_204", interval = 300, tolerance = 50, policy-regex-filter = "(?i)(Hong|HK|香港|TW|Taiwan|台湾|Japan|JP|日本|SG|Singapore|新加坡|KR|Korea|韩国)"
香港故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "^(?!(.*(\\[[2-9]x\\]|\\[1[0-9]x\\]|\\[0\\.[5-9]x\\]|2倍|3倍))).*(?i)(Hong|HK|香港)"
AI = select, 美国故转, 狮城故转, 日本故转, 台湾故转
"""

MY_CUSTOM_RULES = """
# 自定义IPTV规则
DOMAIN-SUFFIX,4gtv.tv,台湾故转
DOMAIN-SUFFIX,litv.tv,台湾故转
DOMAIN-KEYWORD,gemini,AI
"""


def fetch_upstream_config(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Shadowrocket/2.2.0"})
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")


def merge_config():
    try:
        content = fetch_upstream_config(UPSTREAM_URL)
    except Exception as e:
        print(f"拉取上游配置失败: {e}")
        return

    # 在 [Proxy Group] 下插入你的策略组
    if "[Proxy Group]" in content:
        content = content.replace(
            "[Proxy Group]\n", f"[Proxy Group]\n{MY_CUSTOM_GROUPS.strip()}\n"
        )

    # 在 [Rule] 顶部插入你的自定义优先规则
    if "[Rule]" in content:
        content = content.replace(
            "[Rule]\n", f"[Rule]\n{MY_CUSTOM_RULES.strip()}\n"
        )

    # 保存生成最终的配置文件
    with open("shadow.conf", "w", encoding="utf-8") as f:
        f.write(content)
    print("配置文件构建并合并成功！")


if __name__ == "__main__":
    merge_config()
