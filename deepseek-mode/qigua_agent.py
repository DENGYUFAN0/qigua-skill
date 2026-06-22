#!/usr/bin/env python3
"""
qigua_agent.py — 易经起卦·决策预演 · DeepSeek 模式参考实现

设计要点（与 Claude Code 版铁律一致）：
  · 摇卦＝真随机，由本代码用 secrets 完成，DeepSeek 不参与、不可改卦（不二筮）。
  · 排盘（识卦/体用/旺衰/取辞规则）由代码算好喂给模型——补 DeepSeek 排盘易错的短板。
  · DeepSeek 只做它最擅长的「解卦」，并保留「事实定夺」红线。

用法：
    pip install -r requirements.txt
    export DEEPSEEK_API_KEY=sk-xxx      # Windows: $env:DEEPSEEK_API_KEY="sk-xxx"
    python qigua_agent.py "要不要现在重构登录模块？"
"""

import os
import sys
import secrets
import datetime

# 注：openai 在 main() 里惰性导入，使本文件的摇卦/识卦/体用纯逻辑无需依赖即可测试。

# ---------- 1. 卦象数据 ----------

# 八卦：键为 (初,中,上) 三爻阴阳（自下而上，1=阳 0=阴）→ (卦名, 符号, 五行)
TRIGRAMS = {
    (1, 1, 1): ("乾", "☰", "金"),
    (1, 1, 0): ("兑", "☱", "金"),
    (1, 0, 1): ("离", "☲", "火"),
    (1, 0, 0): ("震", "☳", "木"),
    (0, 1, 1): ("巽", "☴", "木"),
    (0, 1, 0): ("坎", "☵", "水"),
    (0, 0, 1): ("艮", "☶", "土"),
    (0, 0, 0): ("坤", "☷", "土"),
}

# 六十四卦：KING_WEN[(下卦, 上卦)] = (卦名, 序号)
_UPPER_ORDER = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
_TABLE = {
    "乾": [("乾", 1), ("夬", 43), ("大有", 14), ("大壮", 34), ("小畜", 9), ("需", 5), ("大畜", 26), ("泰", 11)],
    "兑": [("履", 10), ("兑", 58), ("睽", 38), ("归妹", 54), ("中孚", 61), ("节", 60), ("损", 41), ("临", 19)],
    "离": [("同人", 13), ("革", 49), ("离", 30), ("丰", 55), ("家人", 37), ("既济", 63), ("贲", 22), ("明夷", 36)],
    "震": [("无妄", 25), ("随", 17), ("噬嗑", 21), ("震", 51), ("益", 42), ("屯", 3), ("颐", 27), ("复", 24)],
    "巽": [("姤", 44), ("大过", 28), ("鼎", 50), ("恒", 32), ("巽", 57), ("井", 48), ("蛊", 18), ("升", 46)],
    "坎": [("讼", 6), ("困", 47), ("未济", 64), ("解", 40), ("涣", 59), ("坎", 29), ("蒙", 4), ("师", 7)],
    "艮": [("遁", 33), ("咸", 31), ("旅", 56), ("小过", 62), ("渐", 53), ("蹇", 39), ("艮", 52), ("谦", 15)],
    "坤": [("否", 12), ("萃", 45), ("晋", 35), ("豫", 16), ("观", 20), ("比", 8), ("剥", 23), ("坤", 2)],
}
KING_WEN = {}
for _lower, _row in _TABLE.items():
    for _i, (_name, _num) in enumerate(_row):
        KING_WEN[(_lower, _UPPER_ORDER[_i])] = (_name, _num)

# 五行生克
_SHENG = {"金": "水", "水": "木", "木": "火", "火": "土", "土": "金"}  # A 生 B
_KE = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}      # A 克 B


# ---------- 2. 摇卦与识卦 ----------

def cast():
    """三枚铜钱 × 6，secrets 真随机。字=2、背=3。返回 6 个爻和（6/7/8/9），自下而上。"""
    sums = []
    for _ in range(6):
        coins = [secrets.choice((2, 3)) for _ in range(3)]
        sums.append(sum(coins))
    return sums


def _bits(line_sums, resolved):
    """三爻和 → 阴阳三元组。resolved=True 按变后（6→阳,9→阴）；否则本卦（7,9阳 / 6,8阴）。"""
    out = []
    for s in line_sums:
        if resolved:
            out.append(1 if s in (6, 7) else 0)
        else:
            out.append(1 if s in (7, 9) else 0)
    return tuple(out)


def identify(line_sums, resolved=False):
    lower = TRIGRAMS[_bits(line_sums[0:3], resolved)]
    upper = TRIGRAMS[_bits(line_sums[3:6], resolved)]
    name, num = KING_WEN[(lower[0], upper[0])]
    return {"name": name, "num": num, "lower": lower, "upper": upper}


def _relation(ti_wx, yong_wx):
    if ti_wx == yong_wx:
        return "体用比和", "顺——谋事顺遂，无大碍"
    if _SHENG[yong_wx] == ti_wx:
        return "用生体", "大吉——有外力来助，顺势可进"
    if _SHENG[ti_wx] == yong_wx:
        return "体生用", "耗——你在倒贴心力，费而难得"
    if _KE[ti_wx] == yong_wx:
        return "体克用", "吉——你掌控此事，略费力而无妨"
    if _KE[yong_wx] == ti_wx:
        return "用克体", "凶——此事反压制你，受制于外，慎动"
    return "无", "—"


def _season_wang():
    """简化版当令五行（按公历月份近似；土旺四季月做近似处理）。"""
    m = datetime.date.today().month
    return {3: "木", 4: "木", 6: "火", 7: "火", 9: "金", 10: "金", 12: "水", 1: "水"}.get(m, "土")


def analyze(line_sums):
    moving = [i + 1 for i, s in enumerate(line_sums) if s in (6, 9)]  # 变爻位 1..6
    ben = identify(line_sums, resolved=False)
    bian = identify(line_sums, resolved=True) if moving else None

    ti_yong = None
    if moving:
        in_lower = all(p <= 3 for p in moving)
        in_upper = all(p >= 4 for p in moving)
        if in_lower != in_upper:  # 变爻恰好都在一边，体用法适用
            if in_lower:
                yong, ti = ben["lower"], ben["upper"]
            else:
                yong, ti = ben["upper"], ben["lower"]
            rel, judge = _relation(ti[2], yong[2])
            wang = _season_wang()
            ti_yong = {
                "ti": ti, "yong": yong, "rel": rel, "judge": judge, "wang": wang,
                "ti_state": "体卦当令而旺" if ti[2] == wang else "体卦非当令（偏弱）",
            }

    n = len(moving)
    quci = {
        0: "本卦卦辞",
        1: f"第 {moving[0] if moving else '-'} 爻爻辞",
        2: "两变爻爻辞，以上爻为主",
        3: "本卦+变卦卦辞，本卦为体",
        4: "变卦中两不变爻爻辞，以下爻为主",
        5: "变卦中唯一不变爻爻辞",
        6: "乾用九/坤用六，余卦读变卦卦辞",
    }[n]

    return {"line_sums": line_sums, "moving": moving, "ben": ben, "bian": bian,
            "ti_yong": ti_yong, "quci": quci}


# ---------- 3. 组装 prompt 并调用 DeepSeek ----------

def build_user_message(question, a):
    lines_str = " ".join(f"{i + 1}爻={s}" for i, s in enumerate(a["line_sums"]))
    b = a["ben"]
    parts = [
        f"【所问之事】{question}",
        f"【摇卦（宿主真随机，已成卦，不可改）】{lines_str}（6老阴变·7少阳·8少阴·9老阳变）",
        f"【本卦】{b['name']}（{b['num']}）＝上{b['upper'][0]}{b['upper'][1]}下{b['lower'][0]}{b['lower'][1]}",
    ]
    if a["bian"]:
        parts.append(f"【变爻】第 {', '.join(map(str, a['moving']))} 爻 → 【变卦】{a['bian']['name']}（{a['bian']['num']}）")
    else:
        parts.append("【变爻】无（六爻不变），局面稳定，以本卦卦辞为断")
    if a["ti_yong"]:
        t = a["ti_yong"]
        parts.append(
            f"【体用生克（已算）】体={t['ti'][0]}（{t['ti'][2]}）·用={t['yong'][0]}（{t['yong'][2]}）"
            f" → {t['rel']}：{t['judge']}；时令当旺={t['wang']}，{t['ti_state']}"
        )
    else:
        parts.append("【体用生克】不适用（变爻跨上下卦或无变爻），以卦爻辞为主")
    parts.append(f"【取辞规则】{a['quci']}")
    parts.append("请据此解卦：思考阶段走完 体用断力度→象义位三层→倾向四档→可核证假设(含证伪点)，"
                 "再给≤1 行的一句话定论，并标注卦象与事实各自的作用。")
    return "\n".join(parts)


def main():
    if len(sys.argv) < 2:
        sys.exit('用法: python qigua_agent.py "你要决策的问题"')
    question = sys.argv[1]
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        sys.exit("请先设置环境变量 DEEPSEEK_API_KEY（见 .env.example）")

    try:
        from openai import OpenAI  # DeepSeek 兼容 OpenAI SDK
    except ImportError:
        sys.exit("缺少依赖：pip install -r requirements.txt")

    a = analyze(cast())

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "SYSTEM_PROMPT.md"), encoding="utf-8") as f:
        system_prompt = f.read()

    client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
    # deepseek-reasoner = 思考模式。注意：该别名于 2026-07-24 起迁移到 deepseek-v4-flash，
    # 届时把默认值改为 deepseek-v4-flash 即可（仍走思考模式）。
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-reasoner")

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": build_user_message(question, a)},
        ],
        stream=False,
    )
    msg = resp.choices[0].message
    reasoning = getattr(msg, "reasoning_content", None)
    if reasoning:
        print("===== 思考（reasoning_content）=====\n" + reasoning + "\n")
    print("===== 解卦 =====\n" + (msg.content or ""))


if __name__ == "__main__":
    main()
