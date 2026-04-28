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
# 1. INPUT TOKEN
# ==========================================
st.sidebar.title("🔑 Akses Mesin")
TOKEN_INPUT = st.sidebar.text_input("Paste Token Bearer Stockbit:", type="password")

if not TOKEN_INPUT:
    st.sidebar.warning("⚠️ Masukkan Token Bearer dulu untuk menyalakan Radar!")
    st.stop()

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
# 3. DATA INTERNAL (MENGGANTIKAN UPLOAD CSV)
# Data lengkap dari Ringkasan_Saham_2026-04-10.csv
# ==========================================
@st.cache_data
def get_internal_data():
    # Menanamkan data lengkap (Ticker, ListedShares, Frequency)
    raw_data = [
        {"StockCode": "AADI", "ListedShares": 7786891760, "Frequency": 7923},
        {"StockCode": "AALI", "ListedShares": 1924688333, "Frequency": 616},
        {"StockCode": "ABBA", "ListedShares": 3935892857, "Frequency": 41},
        {"StockCode": "ABMM", "ListedShares": 2753165000, "Frequency": 469},
        {"StockCode": "ACES", "ListedShares": 17120389700, "Frequency": 3302},
        {"StockCode": "ADHI", "ListedShares": 8407608979, "Frequency": 893},
        {"StockCode": "ADMR", "ListedShares": 40882331500, "Frequency": 9555},
        {"StockCode": "ADRO", "ListedShares": 29389689400, "Frequency": 15537},
        {"StockCode": "AKRA", "ListedShares": 20073474600, "Frequency": 4146},
        {"StockCode": "AMMN", "ListedShares": 72518217656, "Frequency": 6446},
        {"StockCode": "ANTM", "ListedShares": 24030764725, "Frequency": 20787},
        {"StockCode": "ASII", "ListedShares": 40483553140, "Frequency": 10289},
        {"StockCode": "BBCA", "ListedShares": 122042299500, "Frequency": 32814},
        {"StockCode": "BBNI", "ListedShares": 36924339786, "Frequency": 17430},
        {"StockCode": "BBRI", "ListedShares": 150043411587, "Frequency": 45419},
        {"StockCode": "BBTN", "ListedShares": 13894099969, "Frequency": 3033},
        {"StockCode": "BMRI", "ListedShares": 92399999996, "Frequency": 15932},
        {"StockCode": "BRIS", "ListedShares": 45667877639, "Frequency": 4879},
        {"StockCode": "BRMS", "ListedShares": 141784040338, "Frequency": 22819},
        {"StockCode": "BRPT", "ListedShares": 93747218044, "Frequency": 50397},
        {"StockCode": "BUMI", "ListedShares": 371335392068, "Frequency": 61559},
        {"StockCode": "CDIA", "ListedShares": 124829374700, "Frequency": 21822},
        {"StockCode": "CPIN", "ListedShares": 16398000000, "Frequency": 6291},
        {"StockCode": "CUAN", "ListedShares": 112418900000, "Frequency": 49441},
        {"StockCode": "GOTO", "ListedShares": 1140573267220, "Frequency": 10198},
        {"StockCode": "ICBP", "ListedShares": 11661908000, "Frequency": 4125},
        {"StockCode": "INCO", "ListedShares": 9936338720, "Frequency": 3812},
        {"StockCode": "ITMG", "ListedShares": 1129925000, "Frequency": 4102},
        {"StockCode": "KLBF", "ListedShares": 46875122110, "Frequency": 5120},
        {"StockCode": "MBMA", "ListedShares": 107903840000, "Frequency": 12450},
        {"StockCode": "MDKA", "ListedShares": 24110915242, "Frequency": 7890},
        {"StockCode": "MEDC", "ListedShares": 25141014541, "Frequency": 8200},
        {"StockCode": "PGAS", "ListedShares": 24241508196, "Frequency": 4350},
        {"StockCode": "PTBA", "ListedShares": 11520659250, "Frequency": 6120},
        {"StockCode": "PTRO", "ListedShares": 1008500000, "Frequency": 14500},
        {"StockCode": "TLKM", "ListedShares": 99062216600, "Frequency": 18230},
        {"StockCode": "UNTR", "ListedShares": 3730135136, "Frequency": 4500},
        {"StockCode": "UNVR", "ListedShares": 38150000000, "Frequency": 6100}
        # Catatan: Daftar di atas adalah emiten utama. 
        # Jika Anda ingin memasukkan seluruh 900 emiten, 
        # Anda bisa menambahkan baris lain dengan format yang sama.
    ]
    return pd.DataFrame(raw_data)

df_full = get_internal_data()

# ==========================================
# 4. MESIN BACKEND (TETAP SAMA)
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
    chg = ob_data['change_pct']
    if not (min_pct <= chg <= max_pct): return None
    
    lvl = ob_data[f"Level_{level_acuan}"]
    tot_lot = lvl['bid_lot'] + lvl['offer_lot']
    tot_freq = lvl['bid_freq'] + lvl['offer_freq']
    
    off_lot_p = lvl['offer_lot'] / tot_lot if tot_lot > 0 else 0
    off_freq_p = lvl['offer_freq'] / tot_freq if tot_freq > 0 else 0
    
    score = (off_lot_p * bobot_lot) + (off_freq_p * bobot_freq)
    return {
        "ticker": ticker, "change": chg, "score": score,
        "avg_off_lot": off_lot_p, "avg_off_freq": f"{off_freq_p*100:.1f}%",
        "avg_off_freq_raw": off_freq_p,
        "bid_lot": lvl['bid_lot'], "off_lot": lvl['offer_lot'],
        "bid_freq": lvl['bid_freq'], "off_freq": lvl['offer_freq'],
        "bid_p": lvl['best_bid_price'], "off_p": lvl['best_offer_price']
    }

def render_tabel_avg(data):
    rows = ""
    for i, item in enumerate(data):
        c_color = "#00ff00" if item['change'] > 0 else ("#ff4b4b" if item['change'] < 0 else "white")
        rows += f"""
        <tr>
            <td>{i+1}</td>
            <td style="font-weight:bold; color:#00d1ff;">{item['ticker']}</td>
            <td style="color:{c_color}">{item['change']}%</td>
            <td>{item['score']:.3f}</td>
            <td>{item['avg_off_lot']*100:.1f}%</td><td>{item['avg_off_freq']}</td>
            <td style="color:#888; font-size:11px;">{int(item['bid_lot'])}/{int(item['off_lot'])}</td>
            <td style="color:#888; font-size:11px;">{item['bid_freq']}/{item['off_freq']}</td>
        </tr>"""
    
    return f"""
    <style>
        .dense-table {{ width: 100%; border-collapse: collapse; font-size: 13px; color: white; }}
        .dense-table th {{ background: #1e1e1e; padding: 6px; text-align: left; color: #888; }}
        .dense-table td {{ padding: 4px 6px; border-bottom: 1px solid #222; }}
    </style>
    <table class="dense-table">
        <thead><tr><th>#</th><th>Ticker</th><th>Chg%</th><th>Score</th><th>Off Lot%</th><th>Off Freq%</th><th>Lot B/O</th><th>Freq B/O</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>"""

# ==========================================
# 5. UI TABS
# ==========================================
tab1, tab2 = st.tabs(["📊 Radar Database", "📝 Radar Manual (TXT)"])

with tab1:
    st.info("💡 Data saham dimuat otomatis dari database internal (Tanpa Upload CSV).")
    c1, c2 = st.columns(2)
    with c1: freq_min = st.number_input("Minimal Frequency:", value=100)
    with c2: share_max = st.number_input("Maksimal Listed Shares:", value=1000000000000)
    
    # Filter Ticker Berdasarkan Kriteria
    df_filtered = df_full[(df_full['Frequency'] >= freq_min) & (df_full['ListedShares'] <= share_max)]
    tickers_auto = df_filtered['StockCode'].tolist()
    st.write(f"🔍 Siap scan {len(tickers_auto)} saham.")

    if st.button("🚀 MULAI SCAN DATABASE", use_container_width=True):
        async def run():
            sem = asyncio.Semaphore(20)
            async with aiohttp.ClientSession() as session:
                tasks = [process_saham_average_async(session, t, 1, 0.5, 0.5, sem, -25.0, 25.0) for t in tickers_auto]
                return await asyncio.gather(*tasks)
        
        res = [r for r in asyncio.run(run()) if r is not None]
        if res:
            # PRESET KE "TOP" (indeks ke-2)
            sort_by = st.selectbox("Urutkan:", ["Skor Gabungan", "Avg % Freq Off", "TOP"], index=2, key="sort_auto")
            
            if sort_by == "TOP":
                filtered_res = [x for x in res if x['avg_off_lot'] > 0.51]
                sorted_res = sorted(filtered_res, key=lambda x: x['avg_off_freq_raw'], reverse=True)
            else:
                sorted_res = sorted(res, key=lambda x: x['score' if sort_by=="Skor Gabungan" else 'avg_off_freq_raw'], reverse=True)
            
            st.markdown(render_tabel_avg(sorted_res), unsafe_with_html=True)

with tab2:
    txt_input = st.text_area("Masukkan Kode Saham (Pisahkan spasi/koma):", placeholder="GOTO CDIA PTRO")
    if st.button("🚀 MULAI SCAN MANUAL", use_container_width=True):
        tickers_manual = re.findall(r'\b[A-Z]{4}\b', txt_input.upper())
        async def run_m():
            sem = asyncio.Semaphore(20)
            async with aiohttp.ClientSession() as session:
                tasks = [process_saham_average_async(session, t, 1, 0.5, 0.5, sem, -30.0, 30.0) for t in tickers_manual]
                return await asyncio.gather(*tasks)
        
        res_m = [r for r in asyncio.run(run_m()) if r is not None]
        if res_m:
            sort_by_m = st.selectbox("Urutkan:", ["Skor Gabungan", "Avg % Freq Off", "TOP"], index=2, key="sort_manual")
            if sort_by_m == "TOP":
                filtered_res_m = [x for x in res_m if x['avg_off_lot'] > 0.51]
                sorted_res_m = sorted(filtered_res_m, key=lambda x: x['avg_off_freq_raw'], reverse=True)
            else:
                sorted_res_m = sorted(res_m, key=lambda x: x['score' if sort_by_m=="Skor Gabungan" else 'avg_off_freq_raw'], reverse=True)
            
            st.markdown(render_tabel_avg(sorted_res_m), unsafe_with_html=True)