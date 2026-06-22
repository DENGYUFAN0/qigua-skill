# 起卦 · qigua-skill

> 卦象供路，事实定夺。 · *The hexagram opens a path; the facts make the call.*

一个**决策预演**工具：在正式决策、启动或解决问题之前，先以三枚铜钱法真随机起一卦，沿卦象推演出**非显然的思考方向**，再用事实把结论钉死。它不是预言——随机性的作用是**打破思维定势**，最终一切以事实为准。

A **decision-rehearsal** tool: before you commit to a decision, cast a hexagram with true randomness, let it inject a *non-obvious* angle of thought, then nail the conclusion down with facts. It is not fortune-telling — the randomness exists to **break cognitive ruts**; facts always have the final say.

仓库内含**两套模式**，共享同一套方法论：

| 模式 | 跑在哪 | 摇卦（真随机） | 解卦 | 适合 |
|---|---|---|---|---|
| **A · Claude Code Skill** | Claude Code | PowerShell `Get-Random` | Claude | 已用 Claude Code 的人，手动 `/qigua` |
| **B · DeepSeek 模式** | 任意 Python 环境 | `secrets`（代码内） | DeepSeek API | 想接 DeepSeek 做 agent / 自建服务 |

---

## 核心理念 · Core ideas

1. **真随机，不可挑选**　摇卦必须由程序完成（`Get-Random` / `secrets`），**模型不许自己"心算"或挑卦**——LLM 自选卦有强烈偏好，随机性一假，整个工具就失效。
2. **排盘归代码，解卦归模型**　识卦、体用生克、旺衰、取辞规则都由代码算好喂给模型。这正好补上 LLM（尤其 DeepSeek）**排盘易错**的短板，让它专注最擅长的**解读卦辞爻辞**。
3. **不二筮**　一事一卦，摇出什么解什么，不因卦不顺眼而重摇。
4. **事实定夺**　卦象只负责**出题**（把卦义转成可核证的假设 + 一个证伪点），事实负责**判卷**。卦象与事实冲突时，弃卦从实。
5. **解卦有出处**　断卦力度借《梅花易数》体用生克，象义并重借高岛吞象《高岛易断》——不是凭空编玄学。

## 模式 A：Claude Code Skill

```bash
# 安装：拷到你的 skills 目录
cp -r claude-skill ~/.claude/skills/qigua      # 或 Windows 对应路径

# 使用：在 Claude Code 里手动触发
/qigua 要不要现在重构登录模块？
# 或消息以「起卦」开头
```

手动触发、用完即休眠；输入 `/exit-qigua` 或「收卦」干净退出。详见 [`claude-skill/SKILL.md`](claude-skill/SKILL.md)。

## 模式 B：DeepSeek 模式

```bash
cd deepseek-mode
pip install -r requirements.txt
export DEEPSEEK_API_KEY=sk-xxx          # Windows: $env:DEEPSEEK_API_KEY="sk-xxx"
python qigua_agent.py "要不要现在重构登录模块？"
```

`qigua_agent.py` 在本地用 `secrets` 真随机摇卦、算好本卦/变卦/体用/旺衰，再调 DeepSeek（默认 `deepseek-reasoner` 思考模式）解卦。系统提示词见 [`deepseek-mode/SYSTEM_PROMPT.md`](deepseek-mode/SYSTEM_PROMPT.md)，可直接搬进任何 DeepSeek-API agent。

> 模型名提示：`deepseek-chat` / `deepseek-reasoner` 自 **2026-07-24** 起迁移到 `deepseek-v4-flash`（非思考/思考模式）。届时把 `DEEPSEEK_MODEL` 改为 `deepseek-v4-flash` 即可。

## 维护：同步两套拷贝

模式 A 的 `claude-skill/SKILL.md` 是已安装 skill（`~/.claude/skills/qigua/SKILL.md`）的拷贝。日常在已安装那份上迭代后，跑一键同步脚本回灌仓库：

```powershell
./sync-skill.ps1            # 同步 + 显示差异
./sync-skill.ps1 -Push      # 同步并自动 commit & push
```

> 脚本只同步模式 A 的 `SKILL.md`。模式 B 的 `SYSTEM_PROMPT.md` 是独立手写文件——若改的是解卦方法论本身，需手动跟进，避免两套模式漂移。

## 免责声明 · Disclaimer

本项目是**结构化的换角度思考工具 + 情绪反思工具**，不是预测，也**不得**用于医疗、具体投资标的买卖、法律行动的决策依据。Entertainment & self-reflection only — not a predictor, and not a basis for medical, investment, or legal decisions.

## License

[MIT](LICENSE) © 2026 DENG YUFAN
