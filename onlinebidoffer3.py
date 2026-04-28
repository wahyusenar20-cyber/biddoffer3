import streamlit as st
import pandas as pd
import re
from datetime import datetime
import asyncio
import aiohttp

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="STOCKHOLDER - MULTI RADAR", layout="wide")

# ==========================================
# 1. INPUT TOKEN (PENGGANTI CONFIG.JSON)
# ==========================================
st.sidebar.title("🔑 Akses Mesin")
TOKEN_INPUT = st.sidebar.text_input("Paste Token Bearer Stockbit:", type="password")

if not TOKEN_INPUT:
    st.sidebar.warning("⚠️ Masukkan Token Bearer dulu untuk menyalakan Radar!")
    st.stop() # Mesin berhenti di sini menunggu input token

TOKEN = TOKEN_INPUT.replace("Bearer ", "").strip()

# ==========================================
# 2. HEADERS EXODUS
# ==========================================
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Bearer {TOKEN}",
    "origin": "https://stockbit.com",
    "referer": "https://stockbit.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
}

# ==========================================
# 3. MESIN BACKEND (AVERAGE MODE)
# ==========================================
async def fetch_orderbook_async(session, ticker, semaphore):
    url = f"https://exodus.stockbit.com/company-price-feed/v2/orderbook/companies/{ticker}"
    async with semaphore:
        try:
            async with session.get(url, headers=HEADERS, timeout=5) as resp:
                if resp.status == 200:
                    data_json = await resp.json()
                    data_obj = data_json.get('data', {})
                    res = {"best_bid_price": 0, "best_offer_price": 0, "change_pct": 0,
                           "Level_1": {"bid_lot": 0, "offer_lot": 0, "bid_freq": 0, "offer_freq": 0}, 
                           "Level_2": {"bid_lot": 0, "offer_lot": 0, "bid_freq": 0, "offer_freq": 0}, 
                           "Level_3": {"bid_lot": 0, "offer_lot": 0, "bid_freq": 0, "offer_freq": 0}}
                    bids = data_obj.get('bid', [])
                    offers = data_obj.get('offer', [])
                    if bids: res["best_bid_price"] = int(float(bids[0].get('price', 0)))
                    if offers: res["best_offer_price"] = int(float(offers[0].get('price', 0)))
                    try: res["change_pct"] = round(float(data_obj.get('percentage_change', 0)), 2)
                    except: res["change_pct"] = 0
                    
                    def sum_level_local(arr, depth):
                        tot_lot, tot_freq = 0, 0
                        for i in range(min(depth, len(arr))):
                            item = arr[i]
                            tot_lot += float(item.get('volume', item.get('vol', 0))) / 100 
                            tot_freq += int(item.get('que_num', item.get('freq', 0)))
                        return tot_lot, tot_freq
                    
                    for l in [1, 2, 3]:
                        d = 3 if l==1 else (5 if l==2 else 8)
                        bl, bf = sum_level_local(bids, d); ol, of = sum_level_local(offers, d)
                        res[f"Level_{l}"] = {"bid_lot": bl, "offer_lot": ol, "bid_freq": bf, "offer_freq": of}
                    return res
        except: pass
    return None

async def process_saham_average_async(session, ticker, level_acuan, bobot_lot, bobot_freq, semaphore, min_pct, max_pct):
    ob_data = await fetch_orderbook_async(session, ticker, semaphore)
    if not ob_data: return None
    chg = ob_data.get('change_pct', 0)
    if not (min_pct <= chg <= max_pct): return None

    sum_pct_bid_lot, sum_pct_off_lot = 0, 0
    sum_pct_bid_freq, sum_pct_off_freq = 0, 0
    valid_lot_levels, valid_freq_levels = 0, 0

    for l in range(1, level_acuan + 1):
        data = ob_data.get(f"Level_{l}", {"bid_lot": 0, "offer_lot": 0, "bid_freq": 0, "offer_freq": 0})
        tot_l = data['bid_lot'] + data['offer_lot']
        tot_f = data['bid_freq'] + data['offer_freq']
        if tot_l > 0:
            sum_pct_bid_lot += (data['bid_lot'] / tot_l); sum_pct_off_lot += (data['offer_lot'] / tot_l); valid_lot_levels += 1
        if tot_f > 0:
            sum_pct_bid_freq += (data['bid_freq'] / tot_f); sum_pct_off_freq += (data['offer_freq'] / tot_f); valid_freq_levels += 1

    avg_bid_lot = (sum_pct_bid_lot / valid_lot_levels) if valid_lot_levels > 0 else 0
    avg_off_lot = (sum_pct_off_lot / valid_lot_levels) if valid_lot_levels > 0 else 0
    avg_bid_freq = (sum_pct_bid_freq / valid_freq_levels) if valid_freq_levels > 0 else 0
    avg_off_freq = (sum_pct_off_freq / valid_freq_levels) if valid_freq_levels > 0 else 0
    score = (avg_off_lot * bobot_lot) + (avg_off_freq * bobot_freq)

    return {
        "ticker": ticker, "score": round(score, 2), "chg": chg,
        "best_bid": ob_data.get('best_bid_price', 0), "best_off": ob_data.get('best_offer_price', 0),
        "avg_bid_lot": avg_bid_lot, "avg_off_lot": avg_off_lot,
        "avg_bid_freq": avg_bid_freq, "avg_off_freq": avg_off_freq,
        "avg_off_freq_raw": avg_off_freq
    }

# ==========================================
# 4. RENDERING & STYLING
# ==========================================
def render_tabel_avg(data_list, rank_history):
    rows = []
    current_tickers = [item['ticker'] for item in data_list]
    for i, item in enumerate(data_list):
        t = item['ticker']; chg = item['chg']
        arrow = ""
        if rank_history:
            if t in rank_history:
                old_rank = rank_history.index(t)
                if i < old_rank: arrow = "<span style='color:#00e676;'>⬆️</span>"
                elif i > old_rank: arrow = "<span style='color:#ff4d4d;'>⬇️</span>"
            else: arrow = "🆕"
        
        c_color = "#00e676" if chg > 0 else ("#ff4d4d" if chg < 0 else "#aaaaaa")
        ticker_cell = f"<b>{t}</b> <span style='color:{c_color};'>({chg:+}%)</span> {arrow}"
        price_cell = f"<span style='color:#bbb;'>({item['best_bid']:,} - {item['best_off']:,})</span>"
        l_str = f"<span style='color:#ff6666;'>{round(item['avg_bid_lot']*100)}%</span> | <span style='color:#4da6ff; font-weight:bold;'>{round(item['avg_off_lot']*100)}%</span>"
        f_str = f"<span style='color:#ff6666;'>{round(item['avg_bid_freq']*100)}%</span> | <span style='color:#4da6ff; font-weight:bold;'>{round(item['avg_off_freq']*100)}%</span>"
        
        rows.append({"No": i+1, "Ticker & Kenaikan": ticker_cell, "Harga": price_cell, "Avg Lot (Bid|Off)": l_str, "Avg Freq (Bid|Off)": f_str, "Skor": f"<span style='color:#4da6ff;'><b>{item['score']}</b></span>"})
    return pd.DataFrame(rows), current_tickers

def style_dataframe(df):
    return df.style.set_properties(**{
        'background-color': '#1e1e1e', 'color': '#ffffff', 'border-color': '#333333',
        'padding': '2px 8px', 'font-size': '0.95em'
    }).hide(axis="index").to_html(escape=False)

# ==========================================
# 5. UI UTAMA & NAVIGASI
# ==========================================
st.sidebar.markdown("---")
st.sidebar.title("📊 RADAR MULTI-MODE")
mode = st.sidebar.radio("Pilih Sumber Data:", ["📁 Mode CSV (Auto Filter)", "📝 Mode TXT (Custom Watchlist)"])
st.sidebar.markdown("---")

# Parameter Global
jeda_auto = st.sidebar.number_input("Interval Refresh (Detik):", 1, 3600, 6)
kecepatan_turbo = st.sidebar.number_input("Kecepatan Scan (1-10x):", 1, 10, 10)
maks_pct = st.sidebar.number_input("Batas Maks. Kenaikan (%)", value=3.0, step=0.5)
min_pct = st.sidebar.number_input("Batas Maks. Penurunan (%)", value=-5.0, step=0.5)
bl_eod = st.sidebar.number_input("Bobot Lot (%)", 0, 100, 100)
lvl_eod = st.sidebar.selectbox("Kedalaman Level Avg (1-3):", [1, 2, 3], index=1)

# Logic Per Halaman
if mode == "📁 Mode CSV (Auto Filter)":
    # Murni membaca otomatis dari server/github, file_uploader dihapus.
    st.sidebar.markdown("**📁 Sumber Data:** `Ringkasan_Saham.csv` *(Auto-Read)*")
    min_freq = st.sidebar.number_input("Min Freq:", 0, value=1000)
    limit_scan = st.sidebar.selectbox("Limit Scan:", [20, 50, 100, 200, 300, 400, 500, 600], index=6)
    
    if st.sidebar.button("🚀 START SCAN CSV"):
        try:
            # Langsung membaca file CSV di direktori yang sama
            df = pd.read_csv("Ringkasan_Saham.csv")
            st.session_state['active_tickers'] = [t.strip().upper() for t in df[df['Frequency'] >= min_freq].sort_values(by='Frequency', ascending=False)['StockCode'].tolist() if len(str(t).strip()) == 4][:limit_scan]
            st.session_state['radar_active'] = True; st.rerun()
        except FileNotFoundError:
            st.sidebar.error("⚠️ File 'Ringkasan_Saham.csv' tidak ditemukan di server!")

else: # Mode TXT
    file_txt = st.sidebar.file_uploader("Upload Watchlist.txt", type=["txt"])
    if st.sidebar.button("🎯 START WATCHLIST TXT"):
        if file_txt:
            content = file_txt.getvalue().decode("utf-8")
            # Ekstrak ticker 4 huruf kapital
            found = re.findall(r'\b[A-Z]{4}\b', content)
            st.session_state['active_tickers'] = list(dict.fromkeys(found)) # Unik & urut
            st.session_state['radar_active'] = True; st.rerun()

# Execution Display
if st.session_state.get('radar_active'):
    if st.sidebar.button("🛑 STOP RADAR"): 
        st.session_state['radar_active'] = False; st.rerun()

    st.title(f"📊 Radar Anti-Fake ({'Watchlist' if mode == '📝 Mode TXT (Custom Watchlist)' else 'Screener'})")
    
    @st.fragment(run_every=jeda_auto)
    def live_radar():
        async def run():
            sem = asyncio.Semaphore(kecepatan_turbo * 2) 
            async with aiohttp.ClientSession() as session:
                tasks = [process_saham_average_async(session, t, lvl_eod, bl_eod, 100-bl_eod, sem, min_pct, maks_pct) for t in st.session_state['active_tickers']]
                return await asyncio.gather(*tasks)
        
        res = [r for r in asyncio.run(run()) if r is not None]
        if res:
            col1, col2 = st.columns([1, 2])
            # PERUBAHAN DI SINI: index=2 agar "TOP" menjadi default
            with col1: sort_by = st.selectbox("Urutkan:", ["Skor Gabungan", "Avg % Freq Off", "TOP"], index=2)
            
            # Logika Sortir & Filter Baru
            if sort_by == "TOP":
                # Filter: Hanya yang Avg Off Lot > 51%, lalu urutkan berdasarkan Freq Off
                filtered_res = [x for x in res if x['avg_off_lot'] > 0.51]
                sorted_res = sorted(filtered_res, key=lambda x: x['avg_off_freq_raw'], reverse=True)
            else:
                def sort_key_avg(x): 
                    return x['avg_off_freq_raw'] if sort_by == "Avg % Freq Off" else x['score']
                sorted_res = sorted(res, key=sort_key_avg, reverse=True)
            df_html, new_ranks = render_tabel_avg(sorted_res, st.session_state.get('rank_history', []))
            st.session_state['rank_history'] = new_ranks 
            
            st.markdown(f"**Last Sync:** {datetime.now().strftime('%H:%M:%S')} | **Tickers:** {len(st.session_state['active_tickers'])}")
            if sorted_res:
                st.write(style_dataframe(df_html), unsafe_allow_html=True)
            else:
                st.warning('Tidak ada saham dengan Avg Off Lot > 51%')
        else:
            st.warning("Belum ada data yang masuk kriteria.")
    live_radar()
else:
    st.info("Pilih file sumber di sidebar dan tekan START.")