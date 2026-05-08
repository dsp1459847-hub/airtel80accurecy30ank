import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide")

st.title("MAYA AI: Dynamic T-1/T-2/T-3 + Numerology + Pattern‑Logic Engine")
st.write("T1/T2/T3 patterns + PATTERNS_32 + numerology (3/8/9/5/0→0, 1→4) + pattern‑behaviour rules (double, counting, cross‑day) से compact और accurate top‑30 generation.")

uploaded_file = st.file_uploader("Apni 0DSP0.xlsx ya CSV file upload karein", type=['csv', 'xlsx'])

def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    if v in ['nan', 'XX', '']: return ""
    if len(v) == 1 and v.isdigit(): return '0' + v
    if len(v) >= 2 and v[:2].isdigit(): return v[:2]
    return ""

PATTERNS_32 = [
    (0,1), (0,-1), (1,0), (-1,0), (0,5), (0,-5), (5,0), (-5,0),
    (1,4), (-1,-4), (4,1), (-4,-1), (1,6), (-1,-6), (6,1), (-6,-1),
    (1,1), (-1,-1), (1,-1), (-1,1), (5,5), (-5,-5), (5,-5), (-5,5),
    (1,5), (-1,-5), (1,-5), (-1,5), (5,1), (-5,-1), (5,-1), (-5,1)
]

ROUTE_MAP_T1 = {'DS': ['FD', 'GD', 'GL'], 'GD': ['DS', 'GL', 'GD'], 'DB': ['GL', 'SG', 'DS'], 'SG': ['GL', 'DS', 'GD']}
ROUTE_MAP_T2 = {'FD': ['GD', 'FD', 'DS'], 'GL': ['FD', 'GL', 'DS']}

DYNAMIC_WINNER = {'DS': 'KAL', 'FD': 'PARSON', 'GD': 'KAL', 'GL': 'PARSON', 'DB': 'KAL', 'SG': 'KAL'}


def apply_strict_patterns(val_str, active_patterns):
    if not val_str or len(val_str) != 2: return []
    A, B = int(val_str[0]), int(val_str[1])
    res = []
    for da, db in active_patterns:
        na, nb = A + da, B + db
        if 0 <= na <= 9 and 0 <= nb <= 9:
            res.append(f"{na}{nb}")
    return res

def get_worked(s1_str, t1_str):
    if not s1_str or not t1_str or len(s1_str) != 2 or len(t1_str) != 2: return []
    s1, s2 = int(s1_str[0]), int(s1_str[1])
    t1, t2 = int(t1_str[0]), int(t1_str[1])
    return [p for p in PATTERNS_32 if s1 + p[0] == t1 and s2 + p[1] == t2]

def format_p(p):
    return f"({'+' if p[0] > 0 else ''}{p[0]},{'+' if p[1] > 0 else ''}{p[1]})"


NUMEROLOGY_MAP = {
    '3': ['0'], '9': ['0'], '5': ['0'], '8': ['0'], '1': ['4'],
    '0': ['3', '5', '8', '9']   # 0 → 3,5,8,9
}

def get_numero_substs(digit):
    if digit in NUMEROLOGY_MAP:
        return NUMEROLOGY_MAP[digit]
    return [digit]

def expand_jodi_by_numerology(jodi):
    if len(jodi) != 2:
        return [jodi]
    a, b = jodi[0], jodi[1]
    a_opts = get_numero_substs(a)
    b_opts = get_numero_substs(b)
    res = []
    for xa in a_opts:
        for xb in b_opts:
            res.append(f"{xa}{xb}")
    return list(set(res))

# ====== Jodi type और pattern‑behaviour helpers ======
def classify_jodi_type(jodi):
    if len(jodi) != 2:
        return "other"
    a, b = int(jodi[0]), int(jodi[1])
    if a == b:
        return "double"
    if b == a + 1:
        return "forward_count"
    if b == a - 1:
        return "reverse_count"
    return "other"

def digit_type(d):
    if d in '3958':
        return 'num_zero'
    if d == '1':
        return 'num_four'
    return 'normal'

def classify_jodi_digit_type(jodi):
    if len(jodi) != 2:
        return "other"
    a_type = digit_type(jodi[0])
    b_type = digit_type(jodi[1])
    if a_type == 'num_zero' and b_type == 'num_zero':
        return "double_zero"
    if a_type == 'num_zero' or b_type == 'num_zero':
        return "num_zero_mix"
    if a_type == 'num_four' or b_type == 'num_four':
        return "num_four_mix"
    return "normal"

def render_jodi_box(jodis, passed_set=None):
    if not jodis: return "<p>Pending / N/A</p>"
    if passed_set is None: passed_set = set()
    html = "<div style='display: flex; flex-wrap: wrap; gap: 4px; padding: 2px; line-height: 1;'>"
    for jodi in sorted(list(jodis)):
        if jodi in passed_set:
            html += f"<span style='background:#28a745; color:#fff; padding:0 4px; border-radius:3px; border:1px solid #155724; font-size:11px; font-weight:bold;'>{jodi}</span>"
        else:
            html += f"<span style='background:#fff; color:#000; padding:0 4px; border-radius:3px; border:1px solid #aaa; font-size:11px; font-weight:bold;'>{jodi}</span>"
    html += "</div>"
    return html


# ====== T1 / T2 / T3 बनाने वाला जनरल फ़ंक्शन ======
def generate_pool(df, target_shift, idx, src_cols, day_type, max_history=1500):
    if day_type == "T1":
        s_idx = idx - 1
    elif day_type == "T2":
        s_idx = idx - 2
    elif day_type == "T3":
        s_idx = idx - 3
    else:
        return set(), set()

    if s_idx < 0:
        return set(), set()

    start_hist = max(0, idx - max_history)
    hist = {p: 0 for p in PATTERNS_32}
    for i in range(start_hist, idx):
        vt = df.iloc[i][target_shift]
        if vt:
            for s_col in src_cols:
                if s_idx - 1 < 0: continue
                vs = df.iloc[s_idx - 1][s_col]
                for w in get_worked(vs, vt):
                    hist[w] += 1
    dead_patterns = set(p[0] for p in sorted(hist.items(), key=lambda x: x[1])[:8])

    yest_worked = Counter()
    for t_col in ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']:
        if s_idx < len(df):
            vt = df.iloc[s_idx][t_col]
            if vt:
                for s_col in ROUTE_MAP_T1.get(t_col, []):
                    if s_idx - 1 < 0: continue
                    vs = df.iloc[s_idx - 1][s_col]
                    for w in get_worked(vs, vt):
                        yest_worked[w] += 1
    exhausted = set(p for p, c in yest_worked.items() if c >= 2)

    return dead_patterns, exhausted


if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df = df.dropna(subset=['DATE'])
        df['DATE'] = pd.to_datetime(df['DATE'])
        df = df.sort_values('DATE').reset_index(drop=True)
        cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
        for c in cols: df[c] = df[c].apply(get_val_str)

        st.markdown("### Tareekh aur Shift Chunein")
        max_valid_date = df['DATE'].max().date()
        selected_date = st.date_input("Aaj ki tareekh:", value=max_valid_date)
        sel_date_pd = pd.to_datetime(selected_date)
        date_match = df[df['DATE'] == sel_date_pd]

        if not date_match.empty and date_match.index[0] > 3:
            idx_aaj = date_match.index[0]
            idx_kal = idx_aaj - 1
            idx_parson = idx_aaj - 2

            target_shift = st.selectbox("Aaj Kis Shift ka Number nikalna hai?", cols)
            aaj_actual = set([df.iloc[idx_aaj][target_shift]] if df.iloc[idx_aaj][target_shift] else [])

            winner_day = DYNAMIC_WINNER[target_shift]
            best_sources = ROUTE_MAP_T1.get(target_shift, []) if winner_day == 'KAL' else ROUTE_MAP_T2.get(target_shift, [])

            st.markdown(f"<h3>Maya AI: T1 / T2 / T3 + Numerology + Pattern‑Logic Engine</h3>", unsafe_allow_html=True)
            st.info(f"**{target_shift}** shift ke numbers zyada tar **{winner_day}** ke patterns se bante hain; engine ne '{winner_day}' ko choose kiya hai.")


            with st.spinner("T1 / T2 / T3 + pattern‑behaviour rules generate kar rahi hai..."):
                pattern_history = defaultdict(list)   # { (date, shift): list_of_patterns }
                pattern_after_map = defaultdict(Counter)  # { (type, shift) : pattern -> count }

                # 7‑साल के लिए pattern‑behaviour पहले से record कर लें
                for i in range(1, len(df)):
                    for col in cols:
                        val = get_val_str(df.iloc[i][col])
                        if not val: continue
                        j_type = classify_jodi_type(val)
                        d_type = classify_jodi_digit_type(val)

                        prev_val = get_val_str(df.iloc[i-1][col])
                        if not prev_val: continue
                        worked = get_worked(prev_val, val)
                        pattern_history[(df.iloc[i]['DATE'], col)] = worked

                        for p in worked:
                            pattern_after_map[(j_type, col)][p] += 1
                            pattern_after_map[(d_type, col)][p] += 1

                # आज के लिए base‑patterns निकालें
                base_dead, base_exhausted = set(), set()
                for d_type in ['T1','T2','T3']:
                    d, e = generate_pool(df, target_shift, idx_aaj, best_sources, d_type)
                    base_dead.update(d)
                    base_exhausted.update(e)

                # आज की जोड़ी का type / digit‑type देखें
                jodi_t = df.iloc[idx_aaj][target_shift]
                if pd.isna(jodi_t) and idx_aaj - 1 >= 0:
                    jodi_t = df.iloc[idx_aaj-1][target_shift]
                jodi_t = get_val_str(jodi_t)
                j_type_today = classify_jodi_type(jodi_t) if jodi_t else "other"
                d_type_today = classify_jodi_digit_type(jodi_t) if jodi_t else "other"

                fav_patterns = set(p for p, c in pattern_after_map[(j_type_today, target_shift)].items() if c > 10)
                fav_num_patterns = set(p for p, c in pattern_after_map[(d_type_today, target_shift)].items() if c > 8)

                # कल / दो दिन पहले आए patterns को avoid‑score
                avoid_patterns = set()
                if idx_kal >= 0:
                    for p in pattern_history.get((df.iloc[idx_kal]['DATE'], target_shift), []):
                        avoid_patterns.add(p)
                if idx_parson >= 0:
                    for p in pattern_history.get((df.iloc[idx_parson]['DATE'], target_shift), []):
                        avoid_patterns.add(p)

                # ====== pattern‑based active‑patterns निकालें ======
                active = []
                for p in PATTERNS_32:
                    score = 1.0
                    if p in base_dead:
                        score -= 1.5
                    if p in base_exhausted:
                        score -= 0.8
                    if p in avoid_patterns:
                        score -= 0.5
                    if p in fav_patterns:
                        score += 1.2
                    if p in fav_num_patterns:
                        score += 1.0
                    if score > 0.5:
                        active.append(p)

                # base‑pool बनाएँ
                base_pool = set()
                for src in best_sources:
                    if idx_kal < len(df):
                        vs = get_val_str(df.iloc[idx_kal][src])
                        if vs:
                            applied = apply_strict_patterns(vs, active)
                            for j in applied:
                                base_pool.add(j)

                # numerology expansion
                numerology_expanded = set()
                for j in base_pool:
                    if j and len(j) == 2:
                        expanded = expand_jodi_by_numerology(j)
                        numerology_expanded.update(expanded)

                # frequency‑based trust
                freq_hist = Counter()
                start = max(0, idx_aaj - 1000)
                for i in range(start, idx_aaj):
                    val = df.iloc[i][target_shift]
                    if val:
                        freq_hist[val] += 1

                final_score = defaultdict(float)
                for j in numerology_expanded:
                    # pattern‑based preference
                    j_type = classify_jodi_type(j)
                    d_type = classify_jodi_digit_type(j)
                    p_score = 0.0
                    if j_type in ['double', 'forward_count', 'reverse_count']:
                        p_score += 0.5
                    if d_type in ['num_zero_mix', 'double_zero']:
                        p_score += 0.5
                    if d_type == 'num_four_mix':
                        p_score += 0.5

                    # basic score
                    final_score[j] = 1.0 + p_score

                    # frequency‑adjustment
                    if j in freq_hist:
                        cnt = freq_hist[j]
                        if cnt < 5:
                            freq_mult = 0.8
                        elif cnt < 15:
                            freq_mult = 1.0
                        else:
                            freq_mult = 1.2
                    else:
                        freq_mult = 1.0

                    final_score[j] *= freq_mult

                sorted_final = sorted(final_score.items(), key=lambda x: -x[1])
                top_30 = [j for j, _ in sorted_final[:30]]
                top_15 = [j for j, _ in sorted_final[:15]]

            # ====== UI – एक ही पेज पर छोटा, बोल्ड display ======
            if top_30:
                st.write(f"**T1/T2/T3 + Numerology + Pattern‑Logic से निकली हुई top‑30 जोड़ियाँ**")
                st.markdown(f"**Top‑15 Prediction (Recommended for Play):** {', '.join(top_15)}", unsafe_allow_html=True)
                st.markdown("<h4>Prediction Box (Top‑30)</h4>", unsafe_allow_html=True)
                st.markdown(render_jodi_box(top_30, passed_set=aaj_actual), unsafe_allow_html=True)

            # ====== 7‑Saal backtest (optional) ======
            if st.checkbox("7‑Saal ka backtest dekhna hai?"):
                with st.spinner("7‑Saal backtest process kar rahi hai..."):
                    backtest_results = []
                    for m in df['DATE'].dt.to_period('M').unique():
                        df_m = df[df['DATE'].dt.to_period('M') == m]
                        for shift in cols:
                            hits_top30,
