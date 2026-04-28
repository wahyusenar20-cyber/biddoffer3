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
# 3. DATA INTERNAL (PENGGANTI CSV)
# Data diekstrak dari Ringkasan_Saham_2026-04-10.csv
# ==========================================
DATA_SAHAM_INTERNAL = [
    {"t": "AADI", "s": 7786891760, "f": 7923}, {"t": "AALI", "s": 1924688333, "f": 616},
    {"t": "ABBA", "s": 3935892857, "f": 41}, {"t": "ABDA", "s": 620806680, "f": 2},
    {"t": "ABMM", "s": 2753165000, "f": 469}, {"t": "ACES", "s": 17120389700, "f": 3302},
    {"t": "ACRO", "s": 3469345537, "f": 399}, {"t": "ACST", "s": 17675160000, "f": 167},
    {"t": "ADCP", "s": 22222222200, "f": 77}, {"t": "ADES", "s": 589896800, "f": 47},
    {"t": "ADHI", "s": 8407608979, "f": 893}, {"t": "ADMF", "s": 1235803109, "f": 518},
    {"t": "ADMG", "s": 3889179559, "f": 55}, {"t": "ADMR", "s": 40882331500, "f": 9555},
    {"t": "ADRO", "s": 29389689400, "f": 15537}, {"t": "AEGS", "s": 1006080721, "f": 471},
    {"t": "AGAR", "s": 1000000000, "f": 62}, {"t": "AGII", "s": 3066660000, "f": 502},
    {"t": "AGRO", "s": 24493093216, "f": 586}, {"t": "AGRS", "s": 47367057874, "f": 100},
    {"t": "AHAP", "s": 4900000000, "f": 3468}, {"t": "AIMS", "s": 220000000, "f": 875},
    {"t": "AISA", "s": 9311800000, "f": 583}, {"t": "AKPI", "s": 612248000, "f": 35},
    {"t": "AKRA", "s": 20073474600, "f": 4146}, {"t": "AKSI", "s": 720000000, "f": 100},
    {"t": "ALDO", "s": 2700713744, "f": 48}, {"t": "ALII", "s": 15825800000, "f": 1065},
    {"t": "ALKA", "s": 507665055, "f": 734}, {"t": "AMAG", "s": 5001552516, "f": 32},
    {"t": "AMAN", "s": 3873500000, "f": 567}, {"t": "AMAR", "s": 18197283760, "f": 154},
    {"t": "AMFG", "s": 434000000, "f": 7}, {"t": "AMIN", "s": 1080000000, "f": 21},
    {"t": "AMMN", "s": 72518217656, "f": 6446}, {"t": "AMMS", "s": 1235296802, "f": 46},
    {"t": "AMOR", "s": 2222222400, "f": 270}, {"t": "AMRT", "s": 41524501700, "f": 6180},
    {"t": "ANDI", "s": 9350000000, "f": 354}, {"t": "ANJT", "s": 3354175000, "f": 99},
    {"t": "ANTM", "s": 24030764725, "f": 20787}, {"t": "APEX", "s": 3546466661, "f": 1940},
    {"t": "APIC", "s": 11766313488, "f": 904}, {"t": "APII", "s": 1075760000, "f": 33},
    {"t": "APLI", "s": 1362671400, "f": 44}, {"t": "APLN", "s": 22699326779, "f": 1796},
    {"t": "ARCI", "s": 25235000000, "f": 10521}, {"t": "AREA", "s": 2539601000, "f": 191},
    {"t": "ARGO", "s": 3174339029, "f": 44}, {"t": "ARII", "s": 3750000000, "f": 118},
    {"t": "ARKA", "s": 2000000000, "f": 157}, {"t": "ARKO", "s": 2928495000, "f": 1355},
    {"t": "ARNA", "s": 7341430976, "f": 573}, {"t": "ARTA", "s": 446674175, "f": 58},
    {"t": "ARTO", "s": 13722768400, "f": 1275}, {"t": "ASBI", "s": 348386472, "f": 5},
    {"t": "ASDM", "s": 384000000, "f": 8}, {"t": "ASGR", "s": 1348780500, "f": 753},
    {"t": "ASHA", "s": 5000000000, "f": 3227}, {"t": "ASII", "s": 40483553140, "f": 10289},
    {"t": "ASJT", "s": 1400000000, "f": 23}, {"t": "ASLC", "s": 12746354780, "f": 708},
    {"t": "ASLI", "s": 6250000000, "f": 380}, {"t": "ASMI", "s": 8958380460, "f": 114},
    {"t": "ASPI", "s": 681823317, "f": 1181}, {"t": "ASRI", "s": 19649411888, "f": 976},
    {"t": "ASRM", "s": 1277992036, "f": 36}, {"t": "ASSA", "s": 3691137517, "f": 925},
    {"t": "ATAP", "s": 1250000000, "f": 1259}, {"t": "ATIC", "s": 2315361355, "f": 39},
    {"t": "ATLA", "s": 6199577693, "f": 316}, {"t": "AUTO", "s": 4819733000, "f": 1339},
    {"t": "AVIA", "s": 61953555600, "f": 2853}, {"t": "AWAN", "s": 3435000000, "f": 95},
    {"t": "AXIO", "s": 5840126500, "f": 148}, {"t": "AYAM", "s": 4000000000, "f": 5373},
    {"t": "AYLS", "s": 853423236, "f": 420}, {"t": "BABP", "s": 44014333126, "f": 310},
    {"t": "BABY", "s": 2616226706, "f": 486}, {"t": "BACA", "s": 19753494636, "f": 202},
    {"t": "BAIK", "s": 1127497572, "f": 258}, {"t": "BAJA", "s": 1800000000, "f": 297},
    {"t": "BALI", "s": 3934592500, "f": 20}, {"t": "BANK", "s": 14793174908, "f": 484},
    {"t": "BAPA", "s": 661784520, "f": 1831}, {"t": "BAPI", "s": 5591980103, "f": 125},
    {"t": "BATA", "s": 1300000000, "f": 18}, {"t": "BATR", "s": 3025037353, "f": 457},
    {"t": "BAUT", "s": 4800182969, "f": 137}, {"t": "BAYU", "s": 353220780, "f": 68},
    {"t": "BBCA", "s": 122042299500, "f": 32814}, {"t": "BBHI", "s": 21512953877, "f": 158},
    {"t": "BBKP", "s": 185819884852, "f": 933}, {"t": "BBLD", "s": 1645796054, "f": 17},
    {"t": "BBMD", "s": 4049189100, "f": 3}, {"t": "BBNI", "s": 36924339786, "f": 17430},
    {"t": "BBRI", "s": 150043411587, "f": 45419}, {"t": "BBRM", "s": 8479490328, "f": 1046},
    {"t": "BBSI", "s": 3637976068, "f": 18}, {"t": "BBSS", "s": 4800016020, "f": 107},
    {"t": "BBTN", "s": 13894099969, "f": 3033}, {"t": "BBYB", "s": 13216977523, "f": 1850},
    {"t": "BCAP", "s": 42618850927, "f": 744}, {"t": "BCIC", "s": 17926071041, "f": 198},
    {"t": "BCIP", "s": 1429915525, "f": 377}, {"t": "BDKR", "s": 4725101522, "f": 960},
    {"t": "BDMN", "s": 9675817341, "f": 1804}, {"t": "BEEF", "s": 8120249598, "f": 1420},
    {"t": "BEER", "s": 4000000000, "f": 686}, {"t": "BEKS", "s": 51351733883, "f": 389},
    {"t": "BELI", "s": 135842883189, "f": 185}, {"t": "BELL", "s": 7250000000, "f": 9944},
    {"t": "BESS", "s": 3440455528, "f": 115}, {"t": "BEST", "s": 9647311150, "f": 242},
    {"t": "BFIN", "s": 15039383620, "f": 784}, {"t": "BGTG", "s": 23731287132, "f": 414},
    {"t": "BHAT", "s": 5000000000, "f": 6}, {"t": "BHIT", "s": 86068156705, "f": 255},
    {"t": "BIKE", "s": 1293916404, "f": 236}, {"t": "BINA", "s": 6073369498, "f": 126},
    {"t": "BINO", "s": 2275316111, "f": 43}, {"t": "BIPI", "s": 63710196917, "f": 57022},
    {"t": "BIPP", "s": 5028669376, "f": 933}, {"t": "BIRD", "s": 2502100000, "f": 308},
    {"t": "BISI", "s": 3000000000, "f": 192}, {"t": "BJBR", "s": 10416229249, "f": 938},
    {"t": "BJTM", "s": 14865343101, "f": 1105}, {"t": "BKDP", "s": 7513992252, "f": 98},
    {"t": "BKSL", "s": 167708902705, "f": 9304}, {"t": "BKSW", "s": 34806467881, "f": 70},
    {"t": "BLES", "s": 8890206400, "f": 151}, {"t": "BLOG", "s": 3379487200, "f": 319},
    {"t": "BLTA", "s": 25940187103, "f": 196}, {"t": "BLUE", "s": 418000000, "f": 297},
    {"t": "BMAS", "s": 17921635680, "f": 11}, {"t": "BMBL", "s": 1030080995, "f": 356},
    {"t": "BMHS", "s": 8603416176, "f": 120}, {"t": "BMRI", "s": 92399999996, "f": 15932},
    {"t": "BMSR", "s": 1159200024, "f": 311}, {"t": "BMTR", "s": 16583997586, "f": 2800},
    {"t": "BNBA", "s": 3354120000, "f": 47}, {"t": "BNBR", "s": 173416832509, "f": 146162},
    {"t": "BNGA", "s": 24890783784, "f": 748}, {"t": "BNII", "s": 75357433911, "f": 241},
    {"t": "BNLI", "s": 35819545925, "f": 408}, {"t": "BOAT", "s": 3501680000, "f": 849},
    {"t": "BOBA", "s": 1155750000, "f": 41}, {"t": "BOGA", "s": 3803526210, "f": 5},
    {"t": "BOLA", "s": 6000000000, "f": 72}, {"t": "BOLT", "s": 2343750000, "f": 98},
    {"t": "BPFI", "s": 2673995362, "f": 19}, {"t": "BPII", "s": 9884153240, "f": 122},
    {"t": "BPTR", "s": 3534000000, "f": 9463}, {"t": "BRAM", "s": 450056980, "f": 10},
    {"t": "BREN", "s": 133786220000, "f": 15432}, {"t": "BRIS", "s": 45667877639, "f": 4879},
    {"t": "BRMS", "s": 141784040338, "f": 22819}, {"t": "BRNA", "s": 979110000, "f": 16},
    {"t": "BRPT", "s": 93747218044, "f": 50397}, {"t": "BRRC", "s": 994603036, "f": 3773},
    {"t": "BSBK", "s": 25091882375, "f": 1980}, {"t": "BSDE", "s": 21171365812, "f": 842},
    {"t": "BSIM", "s": 19517921842, "f": 35}, {"t": "BSML", "s": 1850225000, "f": 545},
    {"t": "BSSR", "s": 2616500000, "f": 341}, {"t": "BSWD", "s": 3651978177, "f": 6},
    {"t": "BTEK", "s": 46277496376, "f": 1083}, {"t": "BTON", "s": 720000000, "f": 15},
    {"t": "BTPN", "s": 10536203690, "f": 15}, {"t": "BTPS", "s": 7626663000, "f": 766},
    {"t": "BUAH", "s": 2000000000, "f": 63}, {"t": "BUDI", "s": 4498997362, "f": 120},
    {"t": "BUKA", "s": 103167090767, "f": 3835}, {"t": "BUKK", "s": 2640452000, "f": 60},
    {"t": "BULL", "s": 15494436593, "f": 23644}, {"t": "BUMI", "s": 371335392068, "f": 61559},
    {"t": "BUVA", "s": 24617054642, "f": 45168}, {"t": "BVIC", "s": 18235266754, "f": 101},
    {"t": "BWPT", "s": 31525291000, "f": 2510}, {"t": "BYAN", "s": 33333335000, "f": 296},
    {"t": "CAKK", "s": 1203300219, "f": 24}, {"t": "CAMP", "s": 5885000000, "f": 95},
    {"t": "CANI", "s": 833440000, "f": 62}, {"t": "CARE", "s": 33250000000, "f": 333},
    {"t": "CARS", "s": 15000000000, "f": 321}, {"t": "CASA", "s": 54476269803, "f": 31},
    {"t": "CASH", "s": 1431125517, "f": 597}, {"t": "CASS", "s": 2086950000, "f": 109},
    {"t": "CBDK", "s": 5668944500, "f": 3724}, {"t": "CBPE", "s": 1356250000, "f": 82},
    {"t": "CBRE", "s": 4538067441, "f": 2848}, {"t": "CBUT", "s": 3125000000, "f": 95},
    {"t": "CCSI", "s": 1333333331, "f": 54}, {"t": "CDIA", "s": 124829374700, "f": 21822},
    {"t": "CEKA", "s": 595000000, "f": 21}, {"t": "CENT", "s": 31183464900, "f": 925},
    {"t": "CFIN", "s": 3984520457, "f": 155}, {"t": "CGAS", "s": 1771499039, "f": 437},
    {"t": "CHEK", "s": 4113331485, "f": 209}, {"t": "CHEM", "s": 1700014594, "f": 5578},
    {"t": "CHIP", "s": 806000000, "f": 127}, {"t": "CINT", "s": 1000000000, "f": 61},
    {"t": "CITA", "s": 3960361250, "f": 113}, {"t": "CITY", "s": 5405188966, "f": 2089},
    {"t": "CLAY", "s": 2570000000, "f": 167}, {"t": "CLEO", "s": 24000000000, "f": 788},
    {"t": "CLPI", "s": 306338500, "f": 63}, {"t": "CMNP", "s": 6696354391, "f": 56},
    {"t": "CMNT", "s": 17125504000, "f": 347}, {"t": "CMPP", "s": 10685124441, "f": 25},
    {"t": "CMRY", "s": 7934683000, "f": 1878}, {"t": "CNKO", "s": 8956361206, "f": 249},
    {"t": "CNMA", "s": 83345000000, "f": 2107}, {"t": "COAL", "s": 6250000000, "f": 4138},
    {"t": "COCO", "s": 3559455924, "f": 2540}, {"t": "COIN", "s": 14705882400, "f": 5872},
    {"t": "CPIN", "s": 16398000000, "f": 6291}, {"t": "CPRO", "s": 59572382787, "f": 1214},
    {"t": "CRAB", "s": 1950000000, "f": 165}, {"t": "CRSN", "s": 2892000000, "f": 69},
    {"t": "CSAP", "s": 5683175151, "f": 39}, {"t": "CSIS", "s": 1829800000, "f": 511},
    {"t": "CSMI", "s": 816061500, "f": 522}, {"t": "CSRA", "s": 2050000000, "f": 155},
    {"t": "CTBN", "s": 800371500, "f": 8}, {"t": "CTRA", "s": 18535695255, "f": 2801},
    {"t": "CTTH", "s": 1230839821, "f": 3090}, {"t": "CUAN", "s": 112418900000, "f": 49441},
    {"t": "CYBR", "s": 6718019297, "f": 2811}, {"t": "DAAZ", "s": 1997000000, "f": 815},
    {"t": "DADA", "s": 7431530800, "f": 354}, {"t": "DART", "s": 3141390962, "f": 120},
    {"t": "DATA", "s": 1375000000, "f": 4438}, {"t": "DAYA", "s": 2420547025, "f": 22},
    {"t": "DCII", "s": 2383745900, "f": 2}, {"t": "DEFI", "s": 687266666, "f": 1356},
    {"t": "DEPO", "s": 6790000000, "f": 113}, {"t": "DEWA", "s": 40687434244, "f": 36046},
    {"t": "DEWI", "s": 2000000000, "f": 6817}, {"t": "DFAM", "s": 1899852850, "f": 3561},
    {"t": "DGIK", "s": 5541165000, "f": 112}, {"t": "DGNS", "s": 1250000000, "f": 77},
    {"t": "DGWG", "s": 5882353000, "f": 2079}, {"t": "DIGI", "s": 1625000000, "f": 49},
    {"t": "DILD", "s": 10365854185, "f": 1074}, {"t": "DIVA", "s": 1428571400, "f": 10367},
    {"t": "DKFT", "s": 5638246600, "f": 526}, {"t": "DKHH", "s": 2550154464, "f": 872},
    {"t": "DLTA", "s": 800659050, "f": 67}, {"t": "DMAS", "s": 48198111100, "f": 1408},
    {"t": "DMMX", "s": 7692307700, "f": 121}, {"t": "DMND", "s": 9468359000, "f": 41},
    {"t": "DNAR", "s": 16721891185, "f": 160}, {"t": "DNET", "s": 14184000000, "f": 15},
    {"t": "DOID", "s": 7651007132, "f": 493}, {"t": "DOOH", "s": 7738891036, "f": 4119},
    {"t": "DOSS", "s": 1725000000, "f": 339}, {"t": "DPUM", "s": 4175000000, "f": 853},
    {"t": "DRMA", "s": 4705882300, "f": 596}, {"t": "DSFI", "s": 1857135500, "f": 223},
    {"t": "DSNG", "s": 10599842400, "f": 1575}, {"t": "DSSA", "s": 192638080000, "f": 21851},
    {"t": "DUTI", "s": 1850000000, "f": 6}, {"t": "DVLA", "s": 1120000000, "f": 15},
    {"t": "DWGL", "s": 9252820991, "f": 176}, {"t": "DYAN", "s": 4272964279, "f": 103},
    {"t": "EAST", "s": 4126405336, "f": 315}, {"t": "ECII", "s": 1334333000, "f": 302},
    {"t": "EKAD", "s": 3493875000, "f": 145}, {"t": "ELIT", "s": 2031643057, "f": 2245},
    {"t": "ELPI", "s": 7412000000, "f": 556}, {"t": "ELSA", "s": 7298500000, "f": 4800},
    {"t": "ELTY", "s": 43521913019, "f": 2116}, {"t": "EMAS", "s": 14731366060, "f": 3378},
    {"t": "EMDE", "s": 3350000000, "f": 3926}, {"t": "EMTK", "s": 61426451483, "f": 10797},
    {"t": "ENAK", "s": 2166666800, "f": 28}, {"t": "ENRG", "s": 26346230250, "f": 18736},
    {"t": "ENZO", "s": 2162547122, "f": 290}, {"t": "EPAC", "s": 3303400000, "f": 258},
    {"t": "EPMT", "s": 2708640000, "f": 26}, {"t": "ERAA", "s": 15950000000, "f": 2606},
    {"t": "ERAL", "s": 5187500000, "f": 1268}, {"t": "ERTX", "s": 1286539792, "f": 315},
    {"t": "ESIP", "s": 1109953847, "f": 16547}, {"t": "ESSA", "s": 17226975700, "f": 5273},
    {"t": "ESTA", "s": 2425354179, "f": 417}, {"t": "ESTI", "s": 2015208720, "f": 2128},
    {"t": "EURO", "s": 2548826428, "f": 452}, {"t": "EXCL", "s": 18199862451, "f": 2841},
    {"t": "FAPA", "s": 3629411800, "f": 27}, {"t": "FAST", "s": 4523610492, "f": 2112},
    {"t": "FILM", "s": 10887566758, "f": 4698}, {"t": "FIRE", "s": 1475363179, "f": 2610},
    {"t": "FISH", "s": 4800000000, "f": 52}, {"t": "FITT", "s": 1304272051, "f": 1582},
    {"t": "FMII", "s": 6400000000, "f": 103}, {"t": "FOLK", "s": 4091357544, "f": 1196},
    {"t": "FOOD", "s": 650000000, "f": 15}, {"t": "FORE", "s": 8918359270, "f": 14419},
    {"t": "FORU", "s": 465224000, "f": 44}, {"t": "FPNI", "s": 5566414000, "f": 3654},
    {"t": "FUJI", "s": 1300000000, "f": 287}, {"t": "FUTR", "s": 6635551959, "f": 4908},
    {"t": "FWCT", "s": 1963000000, "f": 1774}, {"t": "GDST", "s": 9242500000, "f": 139},
    {"t": "GDYR", "s": 410000000, "f": 4}, {"t": "GEMA", "s": 1600000000, "f": 233},
    {"t": "GEMS", "s": 5882353000, "f": 161}, {"t": "GGRM", "s": 1924088000, "f": 488},
    {"t": "GGRP", "s": 12111376157, "f": 78}, {"t": "GHON", "s": 550000000, "f": 15},
    {"t": "GIAA", "s": 407091703837, "f": 3569}, {"t": "GJTL", "s": 3484800000, "f": 1000},
    {"t": "GLVA", "s": 1500000000, "f": 17}, {"t": "GMFI", "s": 124835258434, "f": 1712},
    {"t": "GMTD", "s": 1015380000, "f": 1}, {"t": "GOLD", "s": 1277276000, "f": 9},
    {"t": "GOLF", "s": 19486760000, "f": 678}, {"t": "GOOD", "s": 36897901455, "f": 104},
    {"t": "GOTO", "s": 1140573267220, "f": 10198}
]

# ==========================================
# 4. MESIN BACKEND
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
    
    bid_lot_p = lvl['bid_lot'] / tot_lot if tot_lot > 0 else 0
    off_lot_p = lvl['offer_lot'] / tot_lot if tot_lot > 0 else 0
    bid_freq_p = lvl['bid_freq'] / tot_freq if tot_freq > 0 else 0
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

# ==========================================
# 5. UI COMPONENTS
# ==========================================
def render_tabel_avg(data, prev_ranks):
    rows = ""
    current_ranks = {x['ticker']: i+1 for i, x in enumerate(data)}
    for i, item in enumerate(data):
        rank = i + 1
        old_rank = prev_ranks.get(item['ticker'])
        if old_rank is None: move = "⚪"
        elif rank < old_rank: move = f"<span style='color:#00ff00'>▲{old_rank-rank}</span>"
        elif rank > old_rank: move = f"<span style='color:#ff4b4b'>▼{rank-old_rank}</span>"
        else: move = "➖"
        
        c_color = "#00ff00" if item['change'] > 0 else ("#ff4b4b" if item['change'] < 0 else "white")
        rows += f"""
        <tr>
            <td>{rank}</td><td>{move}</td>
            <td style="font-weight:bold; color:#00d1ff;">{item['ticker']}</td>
            <td style="color:{c_color}">{item['change']}%</td>
            <td style="background-color:rgba(255,255,255,0.05)">{item['score']:.3f}</td>
            <td>{item['avg_off_lot']*100:.1f}%</td><td>{item['avg_off_freq']}</td>
            <td style="color:#888; font-size:11px;">{int(item['bid_lot'])} / {int(item['off_lot'])}</td>
            <td style="color:#888; font-size:11px;">{item['bid_freq']} / {item['off_freq']}</td>
            <td style="font-size:12px;">{item['bid_p']} | {item['off_p']}</td>
        </tr>"""
    
    html = f"""
    <style>
        .dense-table {{ width: 100%; border-collapse: collapse; font-family: 'Segoe UI', sans-serif; font-size: 13px; color: white; }}
        .dense-table th {{ background: #1e1e1e; padding: 6px; text-align: left; border-bottom: 2px solid #333; font-size: 11px; text-transform: uppercase; color: #888; }}
        .dense-table td {{ padding: 4px 6px; border-bottom: 1px solid #222; }}
        .dense-table tr:hover {{ background: #2b2b2b; }}
    </style>
    <table class="dense-table">
        <thead>
            <tr><th>#</th><th>Move</th><th>Ticker</th><th>Chg%</th><th>Score</th><th>Avg Off Lot</th><th>Avg Off Freq</th><th>Lot B/O</th><th>Freq B/O</th><th>Price B/O</th></tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""
    return html, current_ranks

# ==========================================
# 6. HALAMAN RADAR AUTO (PREVIOUS CSV)
# ==========================================
def view_radar_auto():
    st.header("📊 Radar Saham Otomatis (Preset Data)")
    
    # Filter Controls
    c1, c2, c3 = st.columns(3)
    with c1: max_shares = st.number_input("Maksimal Saham Beredar:", value=5000000000, step=1000000)
    with c2: min_base_freq = st.number_input("Minimal Frekuensi Dasar:", value=100, step=10)
    with c3: limit_scan = st.slider("Limit Ticker Scan:", 10, 200, 100)
    
    # Filter Logic
    df_filtered = [d for d in DATA_SAHAM_INTERNAL if d['s'] <= max_shares and d['f'] >= min_base_freq]
    tickers = [d['t'] for d in df_filtered]
    
    st.info(f"Ditemukan {len(tickers)} saham sesuai kriteria. Menampilkan top {limit_scan} ticker.")
    active_tickers = tickers[:limit_scan]
    
    # Engine Settings
    with st.expander("⚙️ Pengaturan Mesin Scan"):
        ec1, ec2, ec3 = st.columns(3)
        with ec1: lvl_ref = ec1.selectbox("Level Acuan:", [1, 2, 3], index=0)
        with ec2: w_lot = ec2.slider("Bobot Lot %:", 0.0, 1.0, 0.5)
        with ec3: w_freq = 1.0 - w_lot; st.write(f"Bobot Freq: {w_freq:.1f}")
        
        pc1, pc2 = st.columns(2)
        with pc1: min_chg = pc1.number_input("Min Change %", value=-25.0)
        with pc2: max_chg = pc2.number_input("Max Change %", value=25.0)

    if st.button("🚀 MULAI SCAN AUTO", use_container_width=True):
        async def run():
            sem = asyncio.Semaphore(20)
            async with aiohttp.ClientSession() as session:
                tasks = [process_saham_average_async(session, t, lvl_ref, w_lot, w_freq, sem, min_chg, max_chg) for t in active_tickers]
                return await asyncio.gather(*tasks)
        
        raw_res = [r for r in asyncio.run(run()) if r is not None]
        
        if raw_res:
            col_s1, col_s2 = st.columns([1, 2])
            # PRESET DEFAULT TOP (Index 2)
            with col_s1: sort_by = st.selectbox("Urutkan Berdasarkan:", ["Skor Gabungan", "Avg % Freq Off", "TOP"], index=2)
            
            if sort_by == "TOP":
                filtered_res = [x for x in raw_res if x['avg_off_lot'] > 0.51]
                sorted_res = sorted(filtered_res, key=lambda x: x['avg_off_freq_raw'], reverse=True)
            else:
                key = "avg_off_freq_raw" if sort_by == "Avg % Freq Off" else "score"
                sorted_res = sorted(raw_res, key=lambda x: x[key], reverse=True)
            
            tbl_html, new_ranks = render_tabel_avg(sorted_res, st.session_state.get('ranks_auto', {}))
            st.session_state['ranks_auto'] = new_ranks
            st.markdown(tbl_html, unsafe_with_html=True)
        else:
            st.warning("Tidak ada data ditemukan.")

# ==========================================
# 7. HALAMAN RADAR MANUAL (TXT)
# ==========================================
def view_radar_manual():
    st.header("📝 Radar Saham Manual (TXT)")
    txt_input = st.text_area("Masukkan Kode Saham (Pisahkan dengan spasi/koma/enter):", height=150, placeholder="GOTO CDIA PTRO ...")
    
    if txt_input:
        tickers = list(set(re.findall(r'\b[A-Z]{4}\b', txt_input.upper())))
        st.write(f"Siaap memproses {len(tickers)} ticker.")
        
        with st.expander("⚙️ Pengaturan Mesin Scan"):
            ec1, ec2, ec3 = st.columns(3)
            with ec1: lvl_ref = ec1.selectbox("Level Acuan (M):", [1, 2, 3], index=0)
            with ec2: w_lot = ec2.slider("Bobot Lot % (M):", 0.0, 1.0, 0.5)
            with ec3: w_freq = 1.0 - w_lot; st.write(f"Bobot Freq: {w_freq:.1f}")
        
        if st.button("🚀 MULAI SCAN MANUAL", use_container_width=True):
            async def run():
                sem = asyncio.Semaphore(20)
                async with aiohttp.ClientSession() as session:
                    tasks = [process_saham_average_async(session, t, lvl_ref, w_lot, w_freq, sem, -30.0, 30.0) for t in tickers]
                    return await asyncio.gather(*tasks)
            
            raw_res = [r for r in asyncio.run(run()) if r is not None]
            
            if raw_res:
                col_s1, col_s2 = st.columns([1, 2])
                # PRESET DEFAULT TOP (Index 2)
                with col_s1: sort_by = st.selectbox("Urutkan Berdasarkan (M):", ["Skor Gabungan", "Avg % Freq Off", "TOP"], index=2)
                
                if sort_by == "TOP":
                    filtered_res = [x for x in raw_res if x['avg_off_lot'] > 0.51]
                    sorted_res = sorted(filtered_res, key=lambda x: x['avg_off_freq_raw'], reverse=True)
                else:
                    key = "avg_off_freq_raw" if sort_by == "Avg % Freq Off" else "score"
                    sorted_res = sorted(raw_res, key=lambda x: x[key], reverse=True)
                
                tbl_html, new_ranks = render_tabel_avg(sorted_res, st.session_state.get('ranks_manual', {}))
                st.session_state['ranks_manual'] = new_ranks
                st.markdown(tbl_html, unsafe_with_html=True)

# ==========================================
# 8. MAIN NAVIGATION
# ==========================================
menu = st.sidebar.radio("Pilih Radar:", ["Radar Auto (Database Internal)", "Radar Manual (Input Teks)"])

if menu == "Radar Auto (Database Internal)":
    view_radar_auto()
else:
    view_radar_manual()