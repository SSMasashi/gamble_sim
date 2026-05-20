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
            padding-top: 1.2rem;
            padding-bottom: 4rem;
            padding-left: 0.9rem;
            padding-right: 0.9rem;
            max-width: 720px;
        }
        div.stButton > button {
            width: 100%;
            height: 3.2rem;
            font-size: 1.15rem;
            font-weight: 700;
            border-radius: 0.8rem;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.7rem;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem;
        }
        .stNumberInput input {
            font-size: 1.1rem;
            height: 2.6rem;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 1rem;
            padding: 0.6rem 0.8rem;
        }
        h1 { font-size: 1.6rem !important; }
        h2 { font-size: 1.2rem !important; }
        h3 { font-size: 1.05rem !important; }
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
        "win_probability": 50.0,
        "last_judgment": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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

st.title("🎰 カジノ収支記録")
st.metric("現在の持ち金", f"¥{st.session_state.money:,}")

tab_record, tab_analysis, tab_history = st.tabs(["💰 記録", "📊 分析", "📜 履歴"])

# ---------------- 記録タブ ----------------
with tab_record:
    with st.expander("💵 持ち金を直接変更", expanded=False):
        new_money = st.number_input(
            "持ち金",
            value=st.session_state.money,
            step=1000,
            key="money_input",
        )
        if st.button("この金額に更新", key="update_money_btn"):
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

    st.subheader("ベッド設定")
    col_bet, col_mul = st.columns(2)
    with col_bet:
        st.number_input(
            "ベッド額",
            min_value=0,
            step=100,
            key="bet",
        )
    with col_mul:
        st.number_input(
            "倍率(整数)",
            min_value=1,
            step=1,
            key="multiplier",
        )

    bet = int(st.session_state.bet)
    mul = int(st.session_state.multiplier)
    win_change = bet * (mul - 1)
    st.caption(f"成功 → **+¥{win_change:,}**（賭け金は支払い済み）　／　失敗 → **-¥{bet:,}**")

    st.subheader("結果を記録")
    col_win, col_lose = st.columns(2)
    with col_win:
        if st.button("✅ 成功", type="primary", key="win_btn"):
            record("成功", win_change, bet, mul)
            st.rerun()
    with col_lose:
        if st.button("❌ 失敗", key="lose_btn"):
            record("失敗", -bet, bet, mul)
            st.rerun()

    with st.expander("🎲 確率で判定（おまけ）", expanded=False):
        st.number_input(
            "成功確率 (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.1f",
            key="win_probability",
        )
        if st.button("🎲 判定する", key="judge_btn"):
            p = round(float(st.session_state.win_probability), 1)
            threshold = int(round(p * 10))
            roll_int = random.randint(1, 1000)
            st.session_state.last_judgment = {
                "success": roll_int <= threshold,
                "probability": p,
                "roll": roll_int / 10,
                "time": datetime.now().strftime("%H:%M:%S"),
            }
            st.rerun()

        if st.session_state.last_judgment is not None:
            j = st.session_state.last_judgment
            if j["success"]:
                st.success(
                    f"✨ **成功**　ロール {j['roll']:.1f} ≤ {j['probability']:.1f}%　({j['time']})"
                )
            else:
                st.error(
                    f"💧 **失敗**　ロール {j['roll']:.1f} > {j['probability']:.1f}%　({j['time']})"
                )
        st.caption("判定は表示のみ。持ち金やベッドには影響しません。上のボタンで手動で記録してください。")

    st.divider()

    col_undo, col_reset = st.columns(2)
    with col_undo:
        if st.button("↩️ 直前を取消", key="undo_btn"):
            undo_last()
            st.rerun()
    with col_reset:
        with st.popover("🗑️ 全リセット", use_container_width=True):
            st.write("履歴と持ち金を初期化します。")
            new_start = st.number_input(
                "リセット後の持ち金",
                value=10000,
                step=1000,
                key="reset_money_input",
            )
            if st.button("リセット実行", key="reset_confirm"):
                st.session_state.history = []
                st.session_state.money = int(new_start)
                st.rerun()


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

            # 連勝/連敗
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
