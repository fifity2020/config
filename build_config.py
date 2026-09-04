import re
import urllib.request

# 1. Raw 纯文本配置链接
UPSTREAM_URL = "https://raw.githubusercontent.com/LingJingMaster/Shadowrocket-Rules/main/Shadowrocket.conf"

# 高倍率排除正则（排除 0.5x~0.9x、1.1x~19x 以及 2倍、3倍等标识）
NO_HIGH_RATE = r"^(?!(.*(\\[[0-9]+\\.[0-9]+(x|X|倍)\\]?|\\[[2-9](x|X|倍)\\]?|\\[1[0-9](x|X|倍)\\]?|[2-9]倍|1\\.[0-9]倍))).*"

# 2. 新增上游不存在的策略组（故障转移组）
NEW_CUSTOM_GROUPS = f"""
# -------------------------- 故障转移组 (已剔除高倍率) --------------------------
香港故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(Hong|HK|香港)"
台湾故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(TW|Taiwan|台湾|臺灣)"
日本故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(Japan|JP|日本)"
狮城故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(Singapore|SG|新加坡|狮城)"
美国故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(USA|US|United States|美国)"
"""

# 3. 自定义规则
MY_CUSTOM_RULES = """
# --------------------------iptv规则--------------------------
# 台湾节点
DOMAIN-SUFFIX,4gtv.tv,台湾故转
DOMAIN-SUFFIX,ofissaifreepc.akamaized.net,台湾故转
DOMAIN-KEYWORD,hamivideo,台湾故转
DOMAIN-SUFFIX,akamaized.net,台湾故转
DOMAIN-SUFFIX,163189.xyz,台湾故转
DOMAIN-SUFFIX,litv.tv,台湾故转
DOMAIN-SUFFIX,ofiii.com,台湾故转
DOMAIN-SUFFIX,livednow.com,台湾故转
DOMAIN-SUFFIX,hinet.net,台湾故转
DOMAIN-SUFFIX,infini.money,台湾故转

# 美国节点
DOMAIN-SUFFIX,astro.com,美国故转
DOMAIN-SUFFIX,pendy.dpdns.org,美国故转
DOMAIN-SUFFIX,docker.livednow.dpdns.org,美国故转
DOMAIN-SUFFIX,4gtv.livednow.dpdns.org,美国故转
DOMAIN-SUFFIX,iptv.vip-tptv.xyz,美国故转
DOMAIN-SUFFIX,migu.8plus.eu.org,美国故转
DOMAIN-SUFFIX,diver.eu.org,美国故转
DOMAIN-SUFFIX,858.qzz.io,美国故转
DOMAIN-SUFFIX,cluster-cz5nqyh5nreq6ua6gaqd7okl7o.cloudworkstations.dev,美国故转
DOMAIN-SUFFIX,qzz.io,美国故转
DOMAIN-SUFFIX,judy.xx.kg,美国故转
DOMAIN-SUFFIX,8plus.eu.org,美国故转
DOMAIN-SUFFIX,ru8.dpdns.org,美国故转
DOMAIN-SUFFIX,vip-tptv.xyz,美国故转
DOMAIN-SUFFIX,hudsonvalleyhost.com,美国故转
DOMAIN-SUFFIX,r2.hfyrw.com,美国故转
DOMAIN-SUFFIX,go-iptv.ggff.net,美国故转
DOMAIN-SUFFIX,bee.tzh911.qzz.io,美国故转
DOMAIN-SUFFIX,wrod.diver.eu.org,美国故转
DOMAIN-SUFFIX,catvod.com,美国故转
DOMAIN-SUFFIX,z2u.com,美国故转
DOMAIN-SUFFIX,amazonaws.com,美国故转
DOMAIN-SUFFIX,cloudflare.com,美国故转
DOMAIN-SUFFIX,nodeseek.com,美国故转

# 狮城节点
DOMAIN-KEYWORD,astro,狮城故转
DOMAIN-KEYWORD,wavve,狮城故转
DOMAIN-SUFFIX,starhubgo.com,狮城故转
DOMAIN-SUFFIX,stream-link.org,狮城故转

# 香港节点
DOMAIN-KEYWORD,mytv265,香港故转
DOMAIN-SUFFIX,tvb.com,香港故转
DOMAIN-SUFFIX,hrtn.net,香港故转
DOMAIN-SUFFIX,hoy.tv,香港故转
DOMAIN-SUFFIX,rthk.tv,香港故转
DOMAIN-SUFFIX,loc.ccv,香港故转
DOMAIN-SUFFIX,ofiii.passwdword.xyz,香港故转
DOMAIN-SUFFIX,mytvsuper.com,香港故转

# IP规则 
IP-CIDR,50.7.158.194/32,日本故转
IP-CIDR,123.51.231.132/32,台湾故转
IP-CIDR,60.250.121.103/32,台湾故转

# 漏网之鱼
DOMAIN-SUFFIX,lioncdn.net,自动优选
DOMAIN-SUFFIX,passwdword.xyz,自动优选
 
# 直连规则
## TPTV
DOMAIN-SUFFIX,mobaibox.com,DIRECT
IP-CIDR,183.207.0.0/16,DIRECT,no-resolve

## YSP
DOMAIN-SUFFIX,cctv.cn,DIRECT
DOMAIN-SUFFIX,yangshipin.cn,DIRECT

## ITV
DOMAIN-SUFFIX,dnsany.com,DIRECT
DOMAIN-SUFFIX,cmvideo.cn,DIRECT
DOMAIN-SUFFIX,chinamobile.com,DIRECT

## 凤凰秀
DOMAIN-KEYWORD,fengshows,DIRECT

# -------------------------- AI类规则 --------------------------
DOMAIN-KEYWORD,gemini,AI
DOMAIN-KEYWORD,generativelanguage,AI
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

    # 1. 覆写上游同名节点策略组，同时加上高倍率剔除逻辑
    replacements = {
        r"^hk\s*香港节点\s*=.*$": f'hk 香港节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(Hong|HK|香港|🇭🇰)"',
        r"^tw\s*台湾节点\s*=.*$": f'tw 台湾节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(TW|Taiwan|台湾|臺灣|🇹🇼)"',
        r"^jp\s*日本节点\s*=.*$": f'jp 日本节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(Japan|JP|日本|🇯🇵)"',
        r"^us\s*美国节点\s*=.*$": f'us 美国节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(USA|US|United States|美国|🇺🇸)"',
    }

    for pattern, new_line in replacements.items():
        content = re.sub(pattern, new_line, content, flags=re.MULTILINE | re.IGNORECASE)

    # 2. 插入新增故障转移策略组
    if "[Proxy Group]" in content:
        content = content.replace(
            "[Proxy Group]\n", f"[Proxy Group]\n{NEW_CUSTOM_GROUPS.strip()}\n\n"
        )

    # 3. 插入自定义优先规则
    if "[Rule]" in content:
        content = content.replace(
            "[Rule]\n", f"[Rule]\n{MY_CUSTOM_RULES.strip()}\n\n"
        )

    # 4. 保存文件
    with open("shadow.conf", "w", encoding="utf-8") as f:
        f.write(content)
    print("配置文件构建成功！已自动剔除高倍率节点及重复项。")


if __name__ == "__main__":
    merge_config()
