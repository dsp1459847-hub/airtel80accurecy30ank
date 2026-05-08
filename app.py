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
            pattern_history = defaultdict(list)
            pattern_after_map = defaultdict(Counter)

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

            base_dead, base_exhausted =
