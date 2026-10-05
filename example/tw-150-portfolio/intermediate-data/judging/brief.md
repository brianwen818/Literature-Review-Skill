# Judging brief (tw-150-portfolio)

## Research question
Author: a student who built a Taiwan-stock (TW50 + Mid-Cap 100, monthly) price/volume ML stock-selection
system (v1). v1 beat simple rules before costs but lost after costs (too much turnover); its failure in 2025
came from an unnoticed low-volatility / sector tilt; self-supervised pretraining (~50 GPU hours) gave no
benefit; the most effective fix was a hand-written buffer rule ("buy if top 20, sell if out of top 30").

Overarching question for graduate study: *In a market with weak signals and non-negligible trading costs,
what do ML stock-selection models actually learn, how much of it is new, and how much survives costs?*

Four directions:
- **A Factor exposure (main line)**: Is the ML signal new or just known factors (volatility, momentum, size,
  value, industry)? ML return prediction (Gu-Kelly-Xiu), IPCA (Kelly-Pruitt-Su), low-vol / BAB anomaly,
  ML profits concentrated in hard-to-trade stocks (Avramov et al.), anomaly decay, factor zoo / multiple testing.
- **B Cost-aware learning**: putting transaction costs into the training objective. Garleanu-Pedersen partial
  adjustment, smart predict-then-optimize, differentiable optimization layers, end-to-end Sharpe portfolios,
  implementable efficient frontier, turnover penalties.
- **F Representation learning**: why did pretraining fail; when does it help? Autoencoder asset pricing,
  no-arbitrage deep learning (Chen-Pelger-Zhu), virtue of complexity, self-supervised / transformer time-series
  models, cross-stock relation models.
- **G Reinforcement learning**: can rebalancing timing/size be learned? Direct RL trading (Moody-Saffell),
  deep hedging, RL in simulated markets with known optimum, optimal execution, RL portfolio management, surveys.
- Cross-cutting: rigorous validation (backtest overfitting, deflated Sharpe, out-of-sample tests).

## Rubric
For each article in `batch-NNN.json`, write `judged-NNN.json` in the same folder: a JSON list (UTF-8), one object
per article, every item_id in the batch exactly once:
`{"item_id": "...", "relevance": 1-5, "reason": "...", "theme": "..."}`
- relevance: 5 = central to one of the four directions; 4 = directly useful; 3 = useful background;
  2 = loosely related; 1 = off topic. Judge against the research question, not keyword overlap.
  Generic finance (corporate finance, banking, macro, accounting), generic ML applications outside
  asset pricing / trading, and comments/replies without substance are usually 1-2.
- reason: ONE sentence in Traditional Chinese (繁體中文) saying what the article would contribute to this
  research (which direction and how). Be specific. If there is no abstract, judge from title and journal.
- theme: use exactly one of these labels:
  - `A 機器學習與已知因子`
  - `A 低波動與低beta異象`
  - `A 異象、套利限制與因子動物園`
  - `B 交易成本與換手`
  - `B 決策導向與端到端學習`
  - `F 深度學習資產定價`
  - `F 時間序列表示學習`
  - `G 強化學習交易與配置`
  - `G 避險與下單執行`
  - `驗證與回測過度配適`
  - `其他`
