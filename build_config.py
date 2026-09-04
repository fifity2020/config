import re
import urllib.request

# 1. 填入第三方的远程配置 URL

UPSTREAM_URL = "https://raw.githubusercontent.com/LingJingMaster/Shadowrocket-Rules/main/Shadowrocket.conf"

# 2. 你的自定义追加配置
MY_CUSTOM_GROUPS = """
# -------------------------- 区域节点分组 --------------------------
# 已修正：精确使用 \[ 和 \] 转义中括号，排除 [2x] 以上及小数倍率，完美保留香港 01~06
香港节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "^(?!(.*(\\[[2-9]x\\]|\\[1[0-9]x\\]|\\[0\.[5-9]x\\]|2倍|3倍))).*(?i)(Hong|HK|香港|🇭🇰)"
台湾节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "(?i)(TW|Taiwan|台湾|臺灣|🇹🇼)"
日本节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "(?i)(Japan|JP|日本|🇯🇵)"
狮城节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "(?i)(Singapore|SG|新加坡|狮城|🇸🇬)"
美国节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "(?i)(USA|US|United States|美国|🇺🇸)"

# 自动优选 (低延迟地区汇总)
自动优选 = url-test, url = "http://www.gstatic.com/generate_204", interval = 300, tolerance = 50, policy-regex-filter = "^(?!(.*(\\[[2-9]x\\]|\\[1[0-9]x\\]|\\[0\.[5-9]x\\]|2倍|3倍))).*(?i)(Hong|HK|香港|TW|Taiwan|台湾|Japan|JP|日本|SG|Singapore|新加坡|KR|Korea|韩国)"

# -------------------------- 故障转移组 --------------------------
香港故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "^(?!(.*(\\[[2-9]x\\]|\\[1[0-9]x\\]|\\[0\.[5-9]x\\]|2倍|3倍))).*(?i)(Hong|HK|香港)"
台湾故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "(?i)(TW|Taiwan|台湾|臺灣)"
日本故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "(?i)(Japan|JP|日本)"
狮城故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "(?i)(Singapore|SG|新加坡|狮城)"
美国故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "(?i)(USA|US|United States|美国)"
"""

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
