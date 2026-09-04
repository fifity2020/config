import re
import time
import urllib.request

UPSTREAM_URL = "https://raw.githubusercontent.com/LingJingMaster/Shadowrocket-Rules/main/Shadowrocket.conf"

# 高倍率节点排除正则
NO_HIGH_RATE = r"^(?!(.*(\[[0-9]+\.[0-9]+(x|X|倍)\]?|\[[2-9](x|X|倍)\]?|\[1[0-9](x|X|倍)\]?|[2-9]倍|1\.[0-9]倍))).*"

# 自动优选正则
AUTO_TEST_FILTER = f"{NO_HIGH_RATE}.*(?i)(Hong|HK|香港|TW|Taiwan|台湾|Japan|JP|日本|SG|Singapore|新加坡|KR|Korea|韩国)"

# 我方核心策略组
MY_CORE_GROUPS = f"""
# -------------------------- 自动优选与主选择组 --------------------------
自动优选 = url-test, url = "http://www.gstatic.com/generate_204", interval = 300, tolerance = 50, policy-regex-filter = "{AUTO_TEST_FILTER}"
🚀 节点选择 = select, 自动优选, HK 香港节点, TW 台湾节点, JP 日本节点, US 美国节点, PROXY, DIRECT

# -------------------------- 故障转移组 --------------------------
香港故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(Hong|HK|香港)"
台湾故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(TW|Taiwan|台湾|臺灣)"
日本故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(Japan|JP|日本)"
狮城故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(Singapore|SG|新加坡|狮城)"
美国故转 = fallback, url = "http://www.gstatic.com/generate_204", interval = 120, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(USA|US|United States|美国)"

# -------------------------- 基础地区组 --------------------------
HK 香港节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(Hong|HK|香港)"
TW 台湾节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(TW|Taiwan|台湾|臺灣)"
JP 日本节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(Japan|JP|日本)"
US 美国节点 = url-test, url = "http://www.gstatic.com/generate_204", interval = 600, tolerance = 50, policy-regex-filter = "{NO_HIGH_RATE}.*(?i)(USA|US|United States|美国)"
"""

MY_CUSTOM_RULES = """
# -------------------------- IPTV规则 --------------------------
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

DOMAIN-KEYWORD,astro,狮城故转
DOMAIN-KEYWORD,wavve,狮城故转
DOMAIN-SUFFIX,starhubgo.com,狮城故转
DOMAIN-SUFFIX,stream-link.org,狮城故转

DOMAIN-KEYWORD,mytv265,香港故转
DOMAIN-SUFFIX,tvb.com,香港故转
DOMAIN-SUFFIX,hrtn.net,香港故转
DOMAIN-SUFFIX,hoy.tv,香港故转
DOMAIN-SUFFIX,rthk.tv,香港故转
DOMAIN-SUFFIX,loc.ccv,香港故转
DOMAIN-SUFFIX,ofiii.passwdword.xyz,香港故转
DOMAIN-SUFFIX,mytvsuper.com,香港故转

IP-CIDR,50.7.158.194/32,日本故转
IP-CIDR,123.51.231.132/32,台湾故转
IP-CIDR,60.250.121.103/32,台湾故转

DOMAIN-SUFFIX,lioncdn.net,自动优选
DOMAIN-SUFFIX,passwdword.xyz,自动优选

# 直连规则
DOMAIN-SUFFIX,mobaibox.com,DIRECT
IP-CIDR,183.207.0.0/16,DIRECT,no-resolve
DOMAIN-SUFFIX,cctv.cn,DIRECT
DOMAIN-SUFFIX,yangshipin.cn,DIRECT
DOMAIN-SUFFIX,dnsany.com,DIRECT
DOMAIN-SUFFIX,cmvideo.cn,DIRECT
DOMAIN-SUFFIX,chinamobile.com,DIRECT
DOMAIN-KEYWORD,fengshows,DIRECT

# AI类规则
DOMAIN-KEYWORD,gemini,AI
DOMAIN-KEYWORD,generativelanguage,AI
"""

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

    # 1. 精确捕捉 [Proxy Group] 区块（包含 [Proxy Group] 这一行，到下一个 [ 块为止）
    pg_pattern = re.compile(r"(\[Proxy Group\][\s\S]*?)(?=\n\[|\Z)", re.IGNORECASE)
    pg_match = pg_pattern.search(content)

    if pg_match:
        upstream_pg_full = pg_match.group(1)
        
        # 过滤上游已有的冲突策略组，保留第三方业务组
        skip_keywords = ["节点选择", "自动优选", "香港节点", "台湾节点", "日本节点", "美国节点", "其他节点"]
        cleaned_upstream_lines = []
        
        for line in upstream_pg_full.splitlines():
            # 跳过区块头行（我们后面统一重新加）
            if line.strip().lower() == "[proxy group]":
                continue
            # 如果行中包含冲突的顶级选择组或基础节点组名称，跳过
            if any(kw in line for kw in skip_keywords):
                continue
            cleaned_upstream_lines.append(line)

        # 组合新 [Proxy Group] 区块：头部 + 我方核心组 + 上游清洗后的第三方组
        new_pg_block = "[Proxy Group]\n" + MY_CORE_GROUPS.strip() + "\n" + "\n".join(cleaned_upstream_lines)
        
        # 替换回原文
        content = content[:pg_match.start()] + new_pg_block + content[pg_match.end():]
    else:
        print("未找到 [Proxy Group] 标记，直接追加核心组")

    # 2. 插入自定义规则 [Rule]
    rule_pattern = re.compile(r"(\[Rule\])", re.IGNORECASE)
    if rule_pattern.search(content):
        content = rule_pattern.sub(r"\1\n" + MY_CUSTOM_RULES.strip(), content, count=1)

    # 3. 写入文件
    with open("shadow.conf", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("shadow.conf 更新成功！成功将自定义规则与上游所有第三方组融合。")

if __name__ == "__main__":
    merge_config()
