# Data Diggers — AlgoTrade 2025 Solution

> Repository accompanying our *AlgoTrade 2025* victory. It preserves source code, slides, leaderboard, and a concise walkthrough of the ideas that worked—and those that did not.
>
> **Disclaimer – exhibition only.** The bot is frozen exactly as submitted for the competition. It is *not* hardened for real‑money trading.

---

## Repository map

| Path                                                           | Description                                                             |
| -------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `src/UnderpricedOptionBuyer.py`                                | Final 100‑line Python strategy exploiting systematic option mis‑pricing |
| `docs/AlgoTrade_task.pdf`                                      | Official task & API handbook (refer here for exact rules)               |
| `docs/Leaderboard.pdf`                                         | Final standings confirming first place                                  |
| `docs/presentation/Data Diggers.pptx`                          | Pitch deck summarising approach                                         |
| [▶ Presentation recording](https://github.com/PapakMate/algotrade-2025-data-diggers/releases/download/v1.0.0-hackathon/Presentation_full_res.mp4) | Recording of our live presentation + Q&A (GitHub Release asset) |
| `README.md`                                                    | You are here                                                            |
| `LICENSE`                                                      | MIT licence                                                             |

---

## 1  Competition context

AlgoTrade 2025 simulated a high‑frequency options exchange. Teams started with identical virtual capital and traded European calls & puts over several timed rounds. Full mechanics—instrument universe, tick schedule, fees, position limits—are detailed in the rulebook (see `docs/AlgoTrade_task.pdf`).

### Constraints of note

* **Latency matters:** first‑come‑first‑served matching rewarded microsecond reactions.
* **Risk exposure:** hard caps on contracts per asset; cash collateral locked on order entry.
* **No external data:** only live order‑book updates provided.

---

## 2  Idea evolution (chronology)

| Stage              | Observation                                                                  | Decision & outcome                                                                                            |
| ------------------ | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| *Planning*         | Wanted to back‑out implied vol via inverse Black‑Scholes.                    | Produced unstable smiles → abandoned.                                                                         |
| *Late‑night pivot* | Order book routinely quoted far from intrinsic value.                        | Switched to a *one‑line* intrinsic‑vs‑ask heuristic.                                                          |
| **Round 1**        | Simple rule profitable out‑of‑the‑box.                                       | Keep; collect benchmark metrics.                                                                              |
| **Round 2**        | Cash locked in long‑dated options.                                           | Filter down to nearest expiries.                                                                              |
| **Round 3**        | Competitors converge → speed race.                                           | Prune prints, template JSON; cleaned code structure for efficiency.                     |
| **Rounds 4‑5**     | Marginal tweaks only (α manual tuning); volatility spikes from \$HEST asset. | Held first place; risk accepted.                                                                              |

---

## 3  Core heuristic (excerpt)

```python
fair = max(0, spot - strike) if is_call else max(0, strike - spot)
if fair * alpha > ask_price:      # alpha ∈ [0.85, 0.95]
    send_buy(symbol, 1)
```

* **Alpha (α)** tunes aggressiveness; narrower (<0.9) buys only deep bargains.
* **Expiry filter** targets options maturing within few ticks to recycle capital quickly.

---

## 4  Implementation highlights

* **Lines of code:** \~100 (single file, stdlib only).
* **Execution path:** single‑pass loop; one‑by‑one evaluation with immediate order dispatch.
* **Latency tricks:** pre‑built JSON messages, zero `print`, single‑core on Raspberry Pi 4 (colocated for near‑zero network delay).
* **Manual override:** hotkey to adjust α based on current cash reserves.

---

## 5  Results & validation

Outcome metrics are preserved verbatim in `docs/Leaderboard.pdf`. We placed first in every round, usually by a large margin. Round 4 was the closest contest, but we still finished on top.

Round 4 draw‑down came from concentrated call exposure to `$HEST`, a jump‑risk asset highlighted during Q\&A.

---

## 6  Q\&A excerpt (condensed)

> **Q:** Why accept large variance?
> **A:** Expected value dominates over many trades; volatility tolerated.
>
> **Q:** How was latency optimised?
> **A:** One‑by‑one evaluation with immediate order dispatch; no multi‑processing overhead; Raspberry Pi at exchange rack.

Full transcript is included in the presentation folder.

---

## 7  Lessons

1. **Elegant models ≠ competition winners**—microstructure noise crushed inverse‑BS pricing.
2. **Latency > everything** in a speed‑priority exchange.

---

## 8  Team

| Member                                                     | Domain       |
| ---------------------------------------------------------- | ------------ |
| [Filip Aleksić](https://www.linkedin.com/in/aleksicfilip) | Data Science |
| [Mate Papak](https://www.linkedin.com/in/papakmate)       | Data Science |
| [Niko Perica](https://www.linkedin.com/in/niko-perica-ba373a197)     | Statistics   |
| [Vice Perica](https://www.linkedin.com/in/vice-perica-a66616163)     | Statistics   |

---

## 9  Licence

Released under the **MIT License**—see `LICENSE` for terms.
