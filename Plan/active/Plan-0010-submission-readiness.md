# 90+ Submission Plan Set

## Goal

コードを大きく変更せず、評価者が5分で理解・再現・採点できる提出物へ整える。

## Current risk

現状のREADMEは参考文献メモであり、プロジェクト説明ではない。
実装は強いが、評価者が最初に読む README で価値が伝わらない。

## Minimum executable plan

### P0: README replacement

Replace `README.md` with the provided submission-ready version.

Acceptance criteria:

- First 10 linesで「何を自動化したか」が分かる
- 背景・動機がある
- 参考文献4本と実装判断が対応している
- 使い方、テスト、出力例、制約がある
- 投資助言ではないことが明確

### P1: Reproducible sample input / output

Add:

- `samples/request.example.json`
- `outputs/example/report.md`

Acceptance criteria:

- 評価者が入力形式をすぐ理解できる
- 最終成果物の見た目がREADME上でもファイル上でも確認できる
- 外部API取得が不安定でも提出物の意図が伝わる

### P2: CI proof

Add:

- `.github/workflows/pytest.yml`

Patch:

- `pyproject.toml` dev dependencies に `httpx>=0.27.0` を追加

Acceptance criteria:

- GitHub上でpytestが実行される
- API keyなしでcontract / workflow testsが通る
- READMEに書いた「テスト可能なworkflow」が証拠化される

### P3: Final smoke test

Run:

```bash
python -m pip install -e ".[dev]"
pytest
```

If using an LLM API key:

```bash
cp .env.example .env
earnings-debate serve --host 127.0.0.1 --port 8000
earnings-debate run --input-json samples/request.example.json --out outputs
```

## Do not do in this pass

- Web UI
- 多銘柄一括分析
- 自動売買
- 株価予測
- portfolio optimization
- agent数の追加
- SEC parserの過度な作り込み

## Execution Tracking

### Task Breakdown

| Task | Plan item | Files | Status |
| --- | --- | --- | --- |
| T1 | P0 README replacement | `README.md` | Done |
| T2 | P1 sample input / output | `samples/request.example.json`, `outputs/example/report.md` | Done |
| T3 | P2 CI proof | `.github/workflows/pytest.yml`, `pyproject.toml` | Done |
| T4 | P3 final smoke test | local validation commands | Done |

### Branch / PR Plan

- Branch: `submission/0010-readiness`
- PR scope: P0 through P3 as a single submission-readiness change set.

### Log

#### 2026-05-27

- Branch: `submission/0010-readiness`
- Copied source plan from `earnings_debate_90_plan_bundle/PLAN_90.md` to
  `Plan/active/Plan-0010-submission-readiness.md`.
- Task split:
  - T1: Replace README with submission-ready project description.
  - T2: Add reproducible sample request and example report.
  - T3: Add pytest workflow and `httpx` dev dependency.
  - T4: Run install and pytest validation.
- Validation:
  - `python -m pip install -e ".[dev]"` could not run because this local shell
    does not provide a `python` executable.
  - `python3 -m pip install -e ".[dev]"` passed.
  - `pytest` passed with 46 tests.

## Target scoring effect

| Area | Current risk | Fix |
| --- | --- | --- |
| README | 実装価値が伝わらない | submission-ready README |
| Reproducibility | 実行イメージが弱い | sample input/output |
| Engineering proof | テストの存在が見えにくい | CI |
| Scope control | 未実装との混同リスク | limitations / no-go section |

Expected score after execution: 90+ if tests pass and README is not shortened.
