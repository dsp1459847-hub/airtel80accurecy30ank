import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide")

st.title("MAYA AI: Dynamic T-1/T-2/T-3 + Numerology + Pattern‑Logic Engine")
st.write("पिछले 11 दिन, 11 वार‑वार days, और 11–12 तारीख‑वाइज days की compact history; 7‑साल नहीं।")

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

NUMEROLOGY_MAP = {
    '3': ['0'], '9': ['0'], '5': ['0'], '8': ['0'], '1': ['4'],
    '0': ['3', '5', '8', '9']
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

def render_jodi_box(jodis, actual_set=None, pred_set=None):
    if not jodis:
        return "<p>–</p>"
    if actual_set is None:
        actual_set = set()
    if pred_set is None:
        pred_set = set()

    html = "<div style='display: flex; flex-wrap: wrap; gap: 2px; padding: 2px; line-height: 1;'>"
    for jodi in sorted(list(jodis)):
        if jodi in actual_set or jodi in pred_set:
            html += f"<span style='background:#28a745; color:#fff; padding:0 4px; border-radius:3px; border:1px solid #155724; font-size:11px; font-weight:bold;'>{jodi}</span>"
        else:
            html += f"<span style='background:#fff; color:#000; padding:0 4px; border-radius:3px; border:1px solid #ddd; font-size:11px; font-weight:bold; font-style:italic;'>{jodi}</span>"
    html += "</div>"
    return html

def get_day_num(dt):
    return dt.day

def get_weekday(dt):
    return dt.weekday()


if uploaded_file is not None:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df = df.dropna(subset=['DATE'])
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    for c in cols: df[c] = df[c].apply(get_val_str)

    # ========================
    # आज की तारीख और shift
    # ========================
    st.markdown("### 📅 Tareekh aur Shift Chunein")
    max_valid_date = df['DATE'].max().date()
    selected_date = st.date_input("Aaj ki tareekh:", value=max_valid_date)
    sel_date_pd = pd.to_datetime(selected_date)

    date_match = df[df['DATE'] == sel_date_pd]
    if not date_match.empty:
        idx_aaj = date_match.index[0]
        target_shift = st.selectbox("Aaj Kis Shift ka Number nikalna hai?", cols)
        aaj_actual = set()
        for col in cols:
            val = get_val_str(date_match.iloc[0][col])
            if val: aaj_actual.add(val)

        winner_day = DYNAMIC_WINNER[target_shift]
        best_sources = ROUTE_MAP_T1.get(target_shift, []) if winner_day == 'KAL' else ROUTE_MAP_T2.get(target_shift, [])

        st.markdown(f"<h3>Maya AI: T1 / T2 / T3 + Numerology + Pattern‑Logic Engine</h3>", unsafe_allow_html=True)
        st.info(f"**{target_shift}** shift ke numbers zyada tar **{winner_day}** ke patterns se bante hain; engine ne '{winner_day}' ko choose kiya hai.")


        # ========================
        # 1. SERIAL‑DATE HISTORY: पिछले 11 दिन + आज
        # ========================
        NUM_SERIAL_DAYS = 11
        if idx_aaj >= NUM_SERIAL_DAYS:
            serial_start = idx_aaj - NUM_SERIAL_DAYS
        else:
            serial_start = 0
        serial_df = df.iloc[serial_start:idx_aaj + 1]

        st.markdown("### 📅 (1) Last 11 Days History (Serial Date‑Wise)")
        for _, row in serial_df.iterrows():
            date_txt = row['DATE'].strftime("%d %b %Y")
            jodis = []
            for c in cols:
                j = get_val_str(row[c])
                if j:
                    jodis.append(j)

            actual_set = set(jodis) if row['DATE'] == sel_date_pd else set()
            pred_set = aaj_actual.intersection(set(jodis))
            html_line = f"<div style='margin-bottom:2px; font-size:12px;'><b>{date_txt}</b> &nbsp;</div>"
            html_line += render_jodi_box(jodis, actual_set=actual_set, pred_set=pred_set)
            st.markdown(html_line, unsafe_allow_html=True)


        # ========================
        # 2. WEEK‑DAY‑WISE HISTORY: पिछले 11 बार वही दिन + आज
        # ========================
        today_weekday = get_weekday(sel_date_pd)
        weekday_df = df[df['DATE'].dt.weekday == today_weekday]
        weekday_df = weekday_df[weekday_df['DATE'] <= sel_date_pd].copy()
        if len(weekday_df) > 12:
            weekday_df = weekday_df.iloc[-12:].reset_index(drop=True)

        st.markdown("### 🗓️ (2) Last 11 Same‑Weekday History (e.g., 11 Sundays + Today)")
        for _, row in weekday_df.iterrows():
            date_txt = row['DATE'].strftime("%d %b %Y")
            jodis = []
            for c in cols:
                j = get_val_str(row[c])
                if j:
                    jodis.append(j)

            actual_set = set(jodis) if row['DATE'] == sel_date_pd else set()
            pred_set = aaj_actual.intersection(set(jodis))
            html_line = f"<div style='margin-bottom:2px; font-size:12px;'><b>{date_txt}</b> &nbsp;</div>"
            html_line += render_jodi_box(jodis, actual_set=actual_set, pred_set=pred_set)
            st.markdown(html_line, unsafe_allow_html=True)


        # ========================
        # 3. SAME‑DATE‑NUMERICAL HISTORY: वही तारीख संख्या (5, 10, 25) से 11–12 बार + आज
        # ========================
        today_day = get_day_num(sel_date_pd)
        same_date_df = df[df['DATE'].dt.day == today_day]
        same_date_df = same_date_df[same_date_df['DATE'] <= sel_date_pd].copy()
        if len(same_date_df) > 12:
            same_date_df = same_date_df.iloc[-12:].reset_index(drop=True)

        st.markdown("### 📅 (3) Same Date‑Numerical History (same 5th / 10th / 25th + Today)")
        for _, row in same_date_df.iterrows():
            date_txt = row['DATE'].strftime("%d %b %Y")
            jodis = []
            for c in cols:
                j = get_val_str(row[c])
                if j:
                    jodis.append(j)

            actual_set = set(jodis) if row['DATE'] == sel_date_pd else set()
            pred_set = aaj_actual.intersection(set(jodis))
            html_line = f"<div style='margin-bottom:2px; font-size:12px;'><b>{date_txt}</b> &nbsp;</div>"
            html_line += render_jodi_box(jodis, actual_set=actual_set, pred_set=pred_set)
            st.markdown(html_line, unsafe_allow_html=True)


        # ========================
        # PRODUCTION‑BASED PREDICTION (Top‑30 / Top‑15)
        # ========================
        with st.spinner("T1 / T2 / T3 + Numerology + Pattern‑Logic generate kar rahi hai..."):
            # आज के लिए small pattern record
            window = 11
            start = max(0, idx_aaj - window)
            pattern_after_map = defaultdict(Counter)
            base_dead, base_exhausted = set(), set()

            for i in range(start, idx_aaj):
                for col in cols:
                    val = get_val_str(df.iloc[i][col])
                    if not val: continue
                    j_type = classify_jodi_type(val)
                    d_type = classify_jodi_digit_type(val)

                    prev_val = get_val_str(df.iloc[i-1][col])
                    if not prev_val: continue
                    worked = get_worked(prev_val, val)
                    for p in worked:
                        pattern_after_map[(j_type, col)][p] += 1
                        pattern_after_map[(d_type, col)][p] += 1

            # आज की जोड़ी का type / digit‑type
            jodi_t = date_match.iloc[0][target_shift]
            jodi_t = get_val_str(jodi_t)
            j_type_today = classify_jodi_type(jodi_t) if jodi_t else "other"
            d_type_today = classify_jodi_digit_type(jodi_t) if jodi_t else "other"

            fav_patterns = set(p for p, c in pattern_after_map[(j_type_today, target_shift)].items() if c > 5)
            fav_num_patterns = set(p for p, c in pattern_after_map[(d_type_today, target_shift)].items() if c > 5)

            # base pattern score
            final_pscore = defaultdict(float)
            for p in PATTERNS_32:
                s = 1.0
                if p in fav_patterns:
                    s += 1.0
                if p in fav_num_patterns:
                    s += 0.8
                final_pscore[p] = s

            # numerology + pattern‑joined pool
            base_pool = set()
            for src in best_sources:
                vs = get_val_str(df.iloc[idx_aaj - 1][src]) if idx_aaj - 1 >= 0 else ""
                if vs:
                    applied = apply_strict_patterns(vs, PATTERNS_32)
                    for j in applied:
                        base_pool.add(j)

            # numerology expansion
            numerology_expanded = set()
            for j in base_pool:
                if j and len(j) == 2:
                    expanded = expand_jodi_by_numerology(j)
                    numerology_expanded.update(expanded)

            # frequency‑score
            freq_hist = Counter()
            f_start = max(0, idx_aaj - window)
            for i in range(f_start, idx_aaj):
                val = get_val_str(df.iloc[i][target_shift])
                if val:
                    freq_hist[val] += 1

            final_score = defaultdict(float)
            for j in numerology_expanded:
                final_score[j] = 1.0
                if j in freq_hist:
                    cnt = freq_hist[j]
                    if cnt < 3:
                        freq_mult = 0.8
                    elif cnt < 8:
                        freq_mult = 1.0
                    else:
                        freq_mult = 1.2
                else:
                    freq_mult = 1.0
                final_score[j] *= freq_mult

            sorted_final = sorted(final_score.items(), key=lambda x: -x[1])
            top_30 = [j for j, _ in sorted_final[:30]]
            top_15 = [j for j, _ in sorted_final[:15]]

            st.write("### 🎯 Final Top‑30 Jodi (Numerology + Pattern‑Logic)")
            st.write(f"**Top‑15 Prediction (Recommended):** {', '.join(top_15[:10])}")
            st.markdown(render_jodi_box(top_30, actual_set=aaj_actual, pred_set=aaj_actual), unsafe_allow_html=True)
