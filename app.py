import random
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="カジノ収支記録",
    page_icon="🎰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 0.6rem;
            padding-bottom: 3rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
            max-width: 420px;
            margin-left: 0 !important;
            margin-right: auto !important;
        }
        div.stButton > button {
            width: 100%;
            height: 2.7rem;
            font-size: 1.05rem;
            font-weight: 700;
            border-radius: 0.7rem;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.55rem;
            margin-top: 0 !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.78rem;
        }
        .stNumberInput input {
            font-size: 1.0rem;
            height: 2.3rem;
        }
        .stNumberInput label {
            font-size: 0.82rem;
            margin-bottom: 0.1rem !important;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.95rem;
            padding: 0.4rem 0.6rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            margin-bottom: 0.3rem !important;
        }
        h1 { font-size: 1.1rem !important; margin: 0 0 0.2rem 0 !important; padding: 0 !important; }
        h2 { font-size: 1.0rem !important; margin: 0.2rem 0 !important; }
        h3 { font-size: 0.95rem !important; margin: 0.2rem 0 !important; }
        [data-testid="stExpander"] summary { padding: 0.35rem 0.7rem !important; font-size: 0.92rem; }
        div[data-testid="stCaptionContainer"], .stCaption {
            margin: 0.1rem 0 !important;
            font-size: 0.82rem;
        }
        .stPopover button { height: 2.7rem; min-width: 8.5rem; white-space: nowrap !important; }
        [data-testid="stVerticalBlock"] { gap: 0.4rem; }
        .btn-row div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-wrap: nowrap !important;
            justify-content: flex-start !important;
            align-items: center !important;
            gap: 0.45rem !important;
        }
        .btn-row div[data-testid="column"] {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: unset !important;
            padding: 0 !important;
        }
        .btn-row .stButton > button,
        .btn-row .stPopover > button {
            width: auto !important;
            min-width: 0 !important;
            padding: 0.6rem 1rem !important;
            white-space: nowrap !important;
        }
        .btn-row .stButton {
            width: auto !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    defaults = {
        "money": 10000,
        "bet": 1000,
        "multiplier": 2,
        "history": [],
        "win_probability": 48.6,
        "last_judgment": None,
        # マーチンゲール用
        "mg_lose_streak": 0,
        "mg_base_bet": 0,
        "mg_current_bet": 0,
        "mg_max_losses": 4,
        "mg_multiplier": 2,
        "mg_last_judgment": None,
        # フィボナッチ用
        "fib_index": 0,             # 現在のフィボナッチ数列インデックス
        "fib_max_losses": 6,        # 破産までの連敗数（数列の長さ）
        "fib_multiplier": 2,        # 倍率
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def calc_mg_base_bet(money: int, max_losses: int) -> int:
    """
    持ち金を全部使い切る連敗回数が max_losses になるような基本ベット額を返す。
    累積損失 = base * (2^n - 1) = money  =>  base = money / (2^n - 1)
    端数は切り捨て・最低1
    """
    denom = (2 ** max_losses) - 1
    if denom <= 0:
        return max(1, money)
    return max(1, money // denom)


def record(action: str, change: int, bet: int, multiplier: int) -> None:
    st.session_state.money += change
    st.session_state.history.append(
        {
            "no": len(st.session_state.history) + 1,
            "time": datetime.now().strftime("%H:%M:%S"),
            "action": action,
            "bet": bet,
            "multiplier": multiplier,
            "change": change,
            "money_after": st.session_state.money,
        }
    )


def undo_last() -> None:
    if not st.session_state.history:
        return
    last = st.session_state.history.pop()
    st.session_state.money -= last["change"]


init_state()

st.markdown("**🎰 カジノ収支記録**")

tab_record, tab_martingale, tab_fibonacci, tab_analysis, tab_history = st.tabs(
    ["💰 記録", "📈 マーチンゲール", "🌀 フィボナッチ", "📊 分析", "📜 履歴"]
)

# ---------------- 記録タブ ----------------
with tab_record:
    st.markdown(f"**現在の持ち金　¥{st.session_state.money:,}**")

    st.number_input("ベッド額", min_value=0, step=100, key="bet")
    st.number_input("倍率(整数)", min_value=1, step=1, key="multiplier")

    bet = int(st.session_state.bet)
    mul = int(st.session_state.multiplier)
    win_change = bet * (mul - 1)

    st.markdown('<div class="btn-row">', unsafe_allow_html=True)
    col_win, col_lose = st.columns(2)
    with col_win:
        if st.button("✅ 成功", type="primary", key="win_btn"):
            record("成功", win_change, bet, mul)
            st.rerun()
    with col_lose:
        if st.button("❌ 失敗", key="lose_btn"):
            record("失敗", -bet, bet, mul)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("🎲 確率で判定（おまけ）", expanded=False):
        st.number_input(
            "成功確率 (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.1f",
            key="win_probability",
        )
        def _roll_judgment() -> dict:
            p = round(float(st.session_state.win_probability), 1)
            threshold = int(round(p * 10))
            roll_int = random.randint(1, 1000)
            return {
                "success": roll_int <= threshold,
                "probability": p,
                "roll": roll_int / 10,
                "time": datetime.now().strftime("%H:%M:%S"),
                "applied": False,
            }

        def _apply_judgment(j: dict) -> None:
            if j["success"]:
                record("成功", win_change, bet, mul)
            else:
                record("失敗", -bet, bet, mul)

        st.markdown('<div class="btn-row">', unsafe_allow_html=True)
        col_judge, col_apply, col_both = st.columns(3)
        with col_judge:
            if st.button("🎲 判定", key="judge_btn"):
                st.session_state.last_judgment = _roll_judgment()
                st.rerun()
        with col_apply:
            apply_disabled = (
                st.session_state.last_judgment is None
                or st.session_state.last_judgment.get("applied", False)
            )
            if st.button("➡️ 反映", key="apply_btn", disabled=apply_disabled):
                _apply_judgment(st.session_state.last_judgment)
                st.session_state.last_judgment["applied"] = True
                st.rerun()
        with col_both:
            if st.button("🎲➡️ 判定&反映", key="judge_apply_btn"):
                j = _roll_judgment()
                _apply_judgment(j)
                j["applied"] = True
                st.session_state.last_judgment = j
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.last_judgment is not None:
            j = st.session_state.last_judgment
            applied_mark = "  📝 反映済み" if j.get("applied") else ""
            if j["success"]:
                st.success(
                    f"✨ **成功**　ロール {j['roll']:.1f} ≤ {j['probability']:.1f}%　({j['time']}){applied_mark}"
                )
            else:
                st.error(
                    f"💅 **失敗**　ロール {j['roll']:.1f} > {j['probability']:.1f}%　({j['time']}){applied_mark}"
                )

    with st.popover("✏️ 持ち金を編集", use_container_width=True):
        new_money = st.number_input(
            "新しい持ち金",
            value=st.session_state.money,
            step=1000,
            key="money_input",
        )
        if st.button("この金額に更新", key="update_money_btn", use_container_width=True):
            diff = int(new_money) - st.session_state.money
            st.session_state.money = int(new_money)
            st.session_state.history.append(
                {
                    "no": len(st.session_state.history) + 1,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "action": "持ち金変更",
                    "bet": 0,
                    "multiplier": 0,
                    "change": diff,
                    "money_after": st.session_state.money,
                }
            )
            st.rerun()

    st.markdown('<div class="btn-row">', unsafe_allow_html=True)
    col_undo, col_reset = st.columns(2)
    with col_undo:
        if st.button("↩️ 取消", key="undo_btn"):
            undo_last()
            st.rerun()
    with col_reset:
        if st.button("🗑️ リセット", key="reset_btn"):
            st.session_state.history = []
            st.session_state.money = 10000
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------- マーチンゲールタブ ----------------
with tab_martingale:
    st.markdown(f"**現在の持ち金　¥{st.session_state.money:,}**")

    # 設定
    mg_max = st.number_input(
        "破産までの連敗数",
        min_value=1,
        max_value=20,
        step=1,
        key="mg_max_losses",
        help="この回数連敗すると持ち金が尽きるようにベット額を計算します",
    )
    mg_mul = st.number_input(
        "倍率(整数)",
        min_value=2,
        step=1,
        key="mg_multiplier",
    )

    mg_max = int(st.session_state.mg_max_losses)
    mg_mul = int(st.session_state.mg_multiplier)

    # 基本ベット = 持ち金 / (mul^1 + mul^2 + ... + mul^n) で累積損失が持ち金に等しくなる計算
    # 累積損失 = base * (mul^1 + mul^2 + ... + mul^n) = base * mul*(mul^n - 1)/(mul-1)  [mul>1]
    # ただし倍率2の場合は classic: base*(2^n - 1)
    # 一般化: 各ステップのベット = base, base*mul, base*mul^2, ...
    # => 累積損失 = base * sum_{k=0}^{n-1} mul^k = base * (mul^n - 1)/(mul - 1)
    def calc_mg_base_bet_general(money: int, max_losses: int, multiplier: int) -> int:
        if multiplier == 1:
            return max(1, money // max_losses)
        denom = (multiplier ** max_losses - 1) // (multiplier - 1)
        if denom <= 0:
            return max(1, money)
        return max(1, money // denom)

    # 現在の推奨ベット計算
    lose_streak = st.session_state.mg_lose_streak
    base_bet = calc_mg_base_bet_general(st.session_state.money, mg_max, mg_mul)
    current_bet = base_bet * (mg_mul ** lose_streak)

    # 連敗が深い場合に持ち金を超えないようキャップ
    current_bet = min(current_bet, st.session_state.money)

    win_change_mg = current_bet * (mg_mul - 1)

    # ステータス表示
    st.divider()

    # 連敗ステージの視覚的表示
    stage_icons = ""
    for i in range(mg_max):
        if i < lose_streak:
            stage_icons += "🔴"
        else:
            stage_icons += "⚪"
    st.markdown(f"**連敗ステージ　{stage_icons}**")
    st.caption(f"現在の連敗数: {lose_streak} / {mg_max}（あと {mg_max - lose_streak} 回で破産ライン）")

    c1, c2, c3 = st.columns(3)
    c1.metric("基本ベット", f"¥{base_bet:,}")
    c2.metric("今回のベット", f"¥{current_bet:,}")
    c3.metric("勝った場合", f"+¥{win_change_mg:,}")

    st.divider()

    # 成功/失敗ボタン
    st.markdown('<div class="btn-row">', unsafe_allow_html=True)
    col_win_mg, col_lose_mg = st.columns(2)
    with col_win_mg:
        if st.button("✅ 成功", type="primary", key="mg_win_btn"):
            record("成功", win_change_mg, current_bet, mg_mul)
            # 勝ったら連敗リセット
            st.session_state.mg_lose_streak = 0
            st.rerun()
    with col_lose_mg:
        if st.button("❌ 失敗", key="mg_lose_btn"):
            record("失敗", -current_bet, current_bet, mg_mul)
            # 負けたら連敗カウント +1（上限で止める）
            st.session_state.mg_lose_streak = min(
                st.session_state.mg_lose_streak + 1, mg_max
            )
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 破産警告
    if lose_streak >= mg_max:
        st.error("⚠️ 破産ラインに到達しました。持ち金を確認してリセットしてください。")
    elif lose_streak >= mg_max - 1 and mg_max > 1:
        st.warning(f"⚠️ 次に負けると破産ラインです！")

    # 連敗リセットボタン
    st.markdown('<div class="btn-row">', unsafe_allow_html=True)
    col_mg_undo, col_mg_reset_streak = st.columns(2)
    with col_mg_undo:
        if st.button("↩️ 取消", key="mg_undo_btn"):
            if st.session_state.history:
                last = st.session_state.history[-1]
                # 取消時に連敗数も戻す
                if last["action"] == "成功":
                    st.session_state.mg_lose_streak = min(
                        st.session_state.mg_lose_streak + 1, mg_max
                    )
                elif last["action"] == "失敗":
                    st.session_state.mg_lose_streak = max(
                        st.session_state.mg_lose_streak - 1, 0
                    )
            undo_last()
            st.rerun()
    with col_mg_reset_streak:
        if st.button("🔄 連敗リセット", key="mg_reset_streak_btn"):
            st.session_state.mg_lose_streak = 0
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # マーチンゲール説明
    with st.expander("ℹ️ マーチンゲール法について", expanded=False):
        st.markdown(f"""
**マーチンゲール法**とは、負けるたびにベット額を倍(×{mg_mul})にしていき、
1回勝つと全ての損失を取り戻せる賭け方です。

- **基本ベット**: 持ち金 ÷ (連敗{mg_max}回分の累積損失係数)
- **負けた時**: 前回ベット × {mg_mul}
- **勝った時**: 基本ベットに戻す（持ち金を元に再計算）

> ⚠️ 連敗が続くとベット額が急増し、{mg_max}連敗で持ち金が尽きるリスクがあります。
        """)



# ---------------- フィボナッチタブ ----------------
with tab_fibonacci:
    st.markdown(f"**現在の持ち金　¥{st.session_state.money:,}**")

    fib_max = st.number_input(
        "破産までの連敗数",
        min_value=2,
        max_value=20,
        step=1,
        key="fib_max_losses",
        help="この回数連敗すると持ち金が尽きるようにベット額を計算します",
    )
    fib_mul = st.number_input(
        "倍率(整数)",
        min_value=2,
        step=1,
        key="fib_multiplier",
    )

    fib_max = int(st.session_state.fib_max_losses)
    fib_mul = int(st.session_state.fib_multiplier)

    # フィボナッチ数列を生成（長さ fib_max）
    # 各ステップのベット倍数: 1, 1, 2, 3, 5, 8, ...
    def gen_fib_sequence(length: int) -> list[int]:
        seq = [1, 1]
        while len(seq) < length:
            seq.append(seq[-1] + seq[-2])
        return seq[:length]

    # 基本ベット計算: 累積損失 = base * sum(fib) = money
    def calc_fib_base_bet(money: int, max_losses: int) -> int:
        seq = gen_fib_sequence(max_losses)
        denom = sum(seq)
        return max(1, money // denom)

    fib_seq = gen_fib_sequence(fib_max)
    fib_idx = min(st.session_state.fib_index, fib_max - 1)
    base_bet_fib = calc_fib_base_bet(st.session_state.money, fib_max)
    current_bet_fib = base_bet_fib * fib_seq[fib_idx]
    current_bet_fib = min(current_bet_fib, st.session_state.money)
    win_change_fib = current_bet_fib * (fib_mul - 1)

    st.divider()

    # フィボナッチ数列のステップ表示
    seq_display = ""
    for i, v in enumerate(fib_seq):
        bet_val = base_bet_fib * v
        if i < fib_idx:
            seq_display += f"~~¥{bet_val:,}~~ → "
        elif i == fib_idx:
            seq_display += f"**[¥{bet_val:,}]** → "
        else:
            seq_display += f"¥{bet_val:,} → "
    seq_display = seq_display.rstrip(" → ")
    st.markdown(f"**ベット数列**　{seq_display}")

    # ステージアイコン
    stage_icons = ""
    for i in range(fib_max):
        if i < fib_idx:
            stage_icons += "🔴"
        elif i == fib_idx:
            stage_icons += "🟡"
        else:
            stage_icons += "⚪"
    st.markdown(f"**現在位置　{stage_icons}**")
    st.caption(
        f"フィボナッチ {fib_idx + 1} ステップ目（数列: {fib_seq[fib_idx]}）"
        f"　あと {fib_max - fib_idx - 1} 回で破産ライン"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("基本ベット", f"¥{base_bet_fib:,}")
    c2.metric("今回のベット", f"¥{current_bet_fib:,}")
    c3.metric("勝った場合", f"+¥{win_change_fib:,}")

    st.divider()

    # 成功/失敗ボタン
    # フィボナッチ法のルール:
    #   負け → 1つ右（インデックス+1）
    #   勝ち → 2つ左（インデックス-2）、0未満なら0に戻す
    st.markdown('<div class="btn-row">', unsafe_allow_html=True)
    col_win_fib, col_lose_fib = st.columns(2)
    with col_win_fib:
        if st.button("✅ 成功", type="primary", key="fib_win_btn"):
            record("成功", win_change_fib, current_bet_fib, fib_mul)
            new_idx = max(0, fib_idx - 2)
            st.session_state.fib_index = new_idx
            st.rerun()
    with col_lose_fib:
        if st.button("❌ 失敗", key="fib_lose_btn"):
            record("失敗", -current_bet_fib, current_bet_fib, fib_mul)
            new_idx = min(fib_idx + 1, fib_max - 1)
            st.session_state.fib_index = new_idx
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 警告
    if fib_idx >= fib_max - 1:
        st.error("⚠️ 破産ラインに到達しました。持ち金を確認してリセットしてください。")
    elif fib_idx >= fib_max - 2 and fib_max > 2:
        st.warning("⚠️ 次に負けると破産ラインです！")

    st.markdown('<div class="btn-row">', unsafe_allow_html=True)
    col_fib_undo, col_fib_reset = st.columns(2)
    with col_fib_undo:
        if st.button("↩️ 取消", key="fib_undo_btn"):
            if st.session_state.history:
                last = st.session_state.history[-1]
                if last["action"] == "成功":
                    # 勝ちを取消 → インデックスを+2戻す（上限あり）
                    st.session_state.fib_index = min(fib_idx + 2, fib_max - 1)
                elif last["action"] == "失敗":
                    # 負けを取消 → インデックスを-1戻す
                    st.session_state.fib_index = max(fib_idx - 1, 0)
            undo_last()
            st.rerun()
    with col_fib_reset:
        if st.button("🔄 数列リセット", key="fib_reset_btn"):
            st.session_state.fib_index = 0
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("ℹ️ フィボナッチ法について", expanded=False):
        seq_str = " → ".join(str(v) for v in fib_seq)
        st.markdown(f"""
**フィボナッチ法**とは、フィボナッチ数列（{seq_str}…）の倍数でベット額を管理する賭け方です。

- **負けた時**: 数列を1つ右に進む（ベット増加）
- **勝った時**: 数列を2つ左に戻る（大きく減らす）
- **基本ベット**: 持ち金 ÷ 数列{fib_max}項の合計

マーチンゲール法より増加が緩やかで、{fib_max}連敗で持ち金が尽きる設計です。

> ⚠️ 勝っても2つ戻るだけなので、連敗が続くと回収に時間がかかります。
        """)


# ---------------- 分析タブ ----------------
with tab_analysis:
    if not st.session_state.history:
        st.info("まだ記録がありません。「💰 記録」タブから始めましょう。")
    else:
        df = pd.DataFrame(st.session_state.history)
        gamble_df = df[df["action"].isin(["成功", "失敗"])].copy()

        if gamble_df.empty:
            st.info("成功/失敗の記録がまだありません。")
        else:
            wins = gamble_df[gamble_df["action"] == "成功"]
            losses = gamble_df[gamble_df["action"] == "失敗"]
            n = len(gamble_df)
            net = int(gamble_df["change"].sum())

            st.subheader("成績サマリー")
            c1, c2, c3 = st.columns(3)
            c1.metric("試行回数", n)
            c2.metric("勝ち", len(wins))
            c3.metric("負け", len(losses))

            c4, c5 = st.columns(2)
            c4.metric("勝率", f"{len(wins) / n * 100:.1f}%")
            c5.metric("純損益", f"¥{net:,}", delta=f"{net:,}")

            st.subheader("勝ち負けの詳細")
            cw, cl = st.columns(2)
            with cw:
                st.markdown("**勝ち**")
                st.metric("総額", f"¥{int(wins['change'].sum()):,}" if len(wins) else "¥0")
                st.metric("最大", f"¥{int(wins['change'].max()):,}" if len(wins) else "¥0")
                st.metric("平均", f"¥{int(wins['change'].mean()):,}" if len(wins) else "¥0")
            with cl:
                st.markdown("**負け**")
                st.metric("総額", f"¥{int(losses['change'].sum()):,}" if len(losses) else "¥0")
                st.metric("最大", f"¥{int(losses['change'].min()):,}" if len(losses) else "¥0")
                st.metric("平均", f"¥{int(losses['change'].mean()):,}" if len(losses) else "¥0")

            max_win_streak = 0
            max_lose_streak = 0
            current_kind = None
            current_streak = 0
            for a in gamble_df["action"]:
                if a == current_kind:
                    current_streak += 1
                else:
                    current_kind = a
                    current_streak = 1
                if a == "成功":
                    max_win_streak = max(max_win_streak, current_streak)
                else:
                    max_lose_streak = max(max_lose_streak, current_streak)

            cs1, cs2, cs3 = st.columns(3)
            cs1.metric("最大連勝", max_win_streak)
            cs2.metric("最大連敗", max_lose_streak)
            cs3.metric("平均ベッド", f"¥{int(gamble_df['bet'].mean()):,}")

            st.subheader("資金推移")
            chart_df = df.copy()
            line = (
                alt.Chart(chart_df)
                .mark_line(point=True, strokeWidth=2)
                .encode(
                    x=alt.X("no:Q", title="記録番号"),
                    y=alt.Y("money_after:Q", title="持ち金 (¥)"),
                    tooltip=["no", "time", "action", "change", "money_after"],
                )
                .properties(height=300)
            )
            st.altair_chart(line, use_container_width=True)

            st.subheader("1試行ごとの変動")
            bar = (
                alt.Chart(gamble_df)
                .mark_bar()
                .encode(
                    x=alt.X("no:Q", title="記録番号"),
                    y=alt.Y("change:Q", title="変動 (¥)"),
                    color=alt.condition(
                        alt.datum.change > 0,
                        alt.value("#22c55e"),
                        alt.value("#ef4444"),
                    ),
                    tooltip=["no", "action", "bet", "multiplier", "change"],
                )
                .properties(height=240)
            )
            st.altair_chart(bar, use_container_width=True)


# ---------------- 履歴タブ ----------------
with tab_history:
    if not st.session_state.history:
        st.info("まだ記録がありません。")
    else:
        full_df = pd.DataFrame(st.session_state.history)
        csv = full_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 CSVをダウンロード",
            data=csv,
            file_name="casino_history.csv",
            mime="text/csv",
            use_container_width=True,
        )

        display_df = full_df[::-1].reset_index(drop=True)
        st.dataframe(
            display_df,
            column_config={
                "no": "#",
                "time": "時刻",
                "action": "種別",
                "bet": st.column_config.NumberColumn("ベッド", format="¥%d"),
                "multiplier": "倍率",
                "change": st.column_config.NumberColumn("変動", format="¥%d"),
                "money_after": st.column_config.NumberColumn("残高", format="¥%d"),
            },
            hide_index=True,
            use_container_width=True,
        )