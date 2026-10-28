import os
import re
import time
import urllib.request

UPSTREAM_URL = "https://raw.githubusercontent.com/LingJingMaster/Shadowrocket-Rules/main/Shadowrocket.conf"

# 本地规则文件: 与 clash-adapter 的 my_rules.yaml 对应的自定义内容
MY_RULES_FILE = "my_rules.conf"
# 生成的远端规则集输出目录 (提交到仓库后, 由 RULES_BASE_URL 引用)
RULES_OUT_DIR = "rules"
# 远端规则集基地址: 填你自己的 GitHub 用户名即可, 仓库名 config、分支 main 已按截图填好:
#   https://raw.githubusercontent.com/<用户名>/config/main/rules
# 构建时每个内联 / 转换型 RuleSet 生成 rules/<名>.list, 主配置引用
#   RULE-SET,<RULES_BASE_URL>/<名>.list,<policy>
RULES_BASE_URL = "https://raw.githubusercontent.com/<用户名>/config/main/rules"

# 高倍率节点排除正 (仅作保留, 当前未接入组过滤器: Shadowrocket 不支持前瞻,
# 接入会清空分组, 详见 2026-10-07 验证)
NO_HIGH_RATE = r"^(?!.*([2-9]\d*(\.\d+)?|1\.[1-9]\d*)(x|X|倍)).*"

# Clash payload 中可原样转入 Shadowrocket 的规则类型, 其余丢弃并计数警告
SR_COMPAT_TYPES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
    "GEOIP", "IP-CIDR", "IP-CIDR6",
}
# payload 行中保留的 flag (其余尾字段, 如 Clash 的策略名, 剥离)
KEPT_FLAGS = {"no-resolve"}

RULE_TYPES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-REGEX",
    "GEOIP", "IP-CIDR", "IP-CIDR6", "IP-ASN", "DST-PORT", "SRC-PORT",
    "URL-REGEX", "USER-AGENT", "PROCESS-NAME", "AND", "OR", "NOT",
}


def parse_my_rules(path):
    """解析 my_rules.conf, 返回 (proxy_group_block, rule_sets).

    rule_sets: list of dicts: {name, policy, url, source, format, rules}
      - url: 远端已有 Shadowrocket 格式规则集, 直接引用, 不下载
      - source + format: 远端其他格式规则集, 构建时拉取并转换, 生成 rules/<名>.list
          format: clash-yaml | domain-list | shadowrocket
      - rules: 内联规则, 生成 rules/<名>.list
    """
    proxy_lines = []
    rule_sets = []
    current = None  # (kind, payload)

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = re.match(r"\[Proxy Group\]", stripped, re.IGNORECASE)
            if m:
                current = ("proxy", None)
                continue
            m = re.match(r"\[RuleSet\s+([^\]]+)\]", stripped, re.IGNORECASE)
            if m:
                current = ("ruleset", {
                    "name": m.group(1).strip(),
                    "policy": None,
                    "url": None,
                    "source": None,
                    "format": "shadowrocket",
                    "rules": [],
                })
                rule_sets.append(current[1])
                continue
            if current is None:
                continue
            if current[0] == "proxy":
                proxy_lines.append(line)
            else:
                rs = current[1]
                low = stripped.lower()
                if low.startswith("policy"):
                    rs["policy"] = stripped.split("=", 1)[1].strip()
                elif low.startswith("url"):
                    rs["url"] = stripped.split("=", 1)[1].strip()
                elif low.startswith("source"):
                    rs["source"] = stripped.split("=", 1)[1].strip()
                elif low.startswith("format"):
                    rs["format"] = stripped.split("=", 1)[1].strip().lower()
                else:
                    rs["rules"].append(stripped)

    for rs in rule_sets:
        if not rs["policy"]:
            raise ValueError(f"RuleSet {rs['name']} 缺少 policy")
        if not rs["url"] and not rs["source"] and not rs["rules"]:
            raise ValueError(f"RuleSet {rs['name']} 既无 url/source 也无规则")
        if rs["source"] and rs["format"] not in ("clash-yaml", "domain-list", "shadowrocket"):
            raise ValueError(f"RuleSet {rs['name']} format 不支持: {rs['format']}")

    return "\n".join(proxy_lines).strip(), rule_sets


def fetch_text(url, timeout=20):
    """拉取远端规则源文本. 返回 None 表示失败 (含 HTML 验证页等非规则内容)."""
    headers = {"User-Agent": "clash.meta"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  拉取失败 {url}: {e}")
        return None
    if "<!DOCTYPE" in text[:512] or "<html" in text[:512]:
        print(f"  拉取到 HTML (验证页/错误页), 视为失败: {url}")
        return None
    return text


def convert_clash_yaml(text):
    """Clash YAML payload -> Shadowrocket 裸规则. 返回 (rules, dropped)."""
    rules, dropped = [], 0
    in_payload = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("payload:"):
            in_payload = True
            continue
        if not in_payload:
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if not line or line.startswith("#"):
            continue
        # 去引号
        if len(line) >= 2 and line[0] == line[-1] and line[0] in "\"'":
            line = line[1:-1]
        fields = [f.strip() for f in line.split(",")]
        rtype = fields[0].upper()
        if rtype not in SR_COMPAT_TYPES or len(fields) < 2:
            dropped += 1
            continue
        kept = fields[:2] + [f for f in fields[2:] if f in KEPT_FLAGS]
        rules.append(",".join(kept))
    return rules, dropped


def convert_domain_list(text):
    """Clash behavior:domain 域名列表 -> Shadowrocket 裸规则."""
    rules = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        if line.startswith("+."):
            rules.append(f"DOMAIN-SUFFIX,{line[2:]}")
        elif line.startswith("*."):
            rules.append(f"DOMAIN-SUFFIX,{line[2:]}")
        elif "," in line and line.split(",", 1)[0].strip().upper() in RULE_TYPES:
            rules.append(line)  # 已是规则行, 原样保留
        elif "." in line and " " not in line and "/" not in line:
            rules.append(f"DOMAIN,{line}")
        # 其余无法识别的行丢弃
    return rules


def convert_shadowrocket(text):
    """已是 Shadowrocket 格式: 仅清洗注释与空行."""
    return [l.strip() for l in text.splitlines()
            if l.strip() and not l.strip().startswith("#")]


CONVERTERS = {
    "clash-yaml": convert_clash_yaml,
    "domain-list": convert_domain_list,
    "shadowrocket": convert_shadowrocket,
}


def resolve_rule_sets(rule_sets, out_dir):
    """生成/刷新 rules/<名>.list, 返回 {name: url} 与跳过的集合.

    拉取或转换失败时: 已有旧 .list 则保留复用并警告; 无旧文件则跳过该组,
    不产生悬空引用。
    """
    os.makedirs(out_dir, exist_ok=True)
    urls, skipped = {}, []
    for rs in rule_sets:
        name = rs["name"]
        if rs["url"]:
            urls[name] = rs["url"]
            continue
        out_path = os.path.join(out_dir, f"{name}.list")
        if rs["source"]:
            print(f"规则集 {name}: 拉取 {rs['source']} (format={rs['format']})")
            text = fetch_text(rs["source"])
            rules = None
            if text is not None:
                conv = CONVERTERS[rs["format"]](text)
                if rs["format"] == "clash-yaml":
                    rules, dropped = conv
                    if dropped:
                        print(f"  {dropped} 条 Clash 专有规则已丢弃")
                else:
                    rules = conv
                if not rules:
                    print(f"  转换结果为空, 视为失败")
                    rules = None
            if rules is None:
                if os.path.exists(out_path):
                    print(f"  保留旧 {name}.list 继续使用")
                else:
                    print(f"  无旧文件, 跳过 {name}")
                    skipped.append(name)
                    continue
            else:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(rules) + "\n")
                print(f"  {len(rules)} 条 -> {name}.list")
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(rs["rules"]) + "\n")
            print(f"规则集 {name}: {len(rs['rules'])} 条 -> {name}.list")
        urls[name] = f"{RULES_BASE_URL.rstrip('/')}/{name}.list"
    return urls, skipped


def build_rule_set_lines(rule_sets, urls, skipped):
    """生成注入 [Rule] 顶端的 RULE-SET 引用行 (保持定义顺序, 跳过失败组)."""
    return [f"RULE-SET,{urls[rs['name']]},{rs['policy']}"
            for rs in rule_sets if rs["name"] not in skipped]


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
    # 0. 解析本地规则组, 生成/刷新远端规则集文件
    proxy_block, rule_sets = parse_my_rules(MY_RULES_FILE)
    urls, skipped = resolve_rule_sets(rule_sets, RULES_OUT_DIR)
    rule_set_lines = build_rule_set_lines(rule_sets, urls, skipped)

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

    # 2. 注入全局测速参数: 将参数直接拼接到 [General] 标题下方
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

        # 清理上游重复的策略组, 避免覆盖自己的 AI 组和核心组
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
            + proxy_block
            + "\n"
            + "\n".join(cleaned_upstream_lines)
        )
        content = (
            content[: pg_match.start()]
            + new_pg_block
            + content[pg_match.end() :]
        )

    # 4. 插入 RULE-SET 引用至 [Rule] 顶端 (规则内容在远端 .list, 主配置只留引用)
    rule_pattern = re.compile(r"(\[Rule\])", re.IGNORECASE)
    if rule_pattern.search(content):
        content = rule_pattern.sub(
            r"\1\n" + "\n".join(rule_set_lines), content, count=1
        )

    # 5. 写入文件
    with open("shadow.conf", "w", encoding="utf-8") as f:
        f.write(content)

    print(
        f"shadow.conf 整合成功! {len(rule_set_lines)} 个规则集以 RULE-SET 引用"
        + (f", {len(skipped)} 组拉取失败已跳过: {', '.join(skipped)}" if skipped else "")
        + f", 远端规则集见 {RULES_OUT_DIR}/。"
    )


if __name__ == "__main__":
    merge_config()
