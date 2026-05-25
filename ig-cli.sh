#!/bin/bash
export PATH="/home/ramdan/.local/bin:$PATH"

# ─── warna ───────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
MAGENTA='\033[0;35m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/.igdownload_config"
COOKIES_FILE="$SCRIPT_DIR/cookies.txt"

# ─── fungsi ──────────────────────────────────────────────
format_bytes() {
  local b=$1
  if [ "$b" -ge 1073741824 ]; then
    echo "$(( b / 1073741824 )).$(( (b % 1073741824) * 10 / 1073741824 )) GB"
  elif [ "$b" -ge 1048576 ]; then
    echo "$(( b / 1048576 )).$(( (b % 1048576) * 10 / 1048576 )) MB"
  elif [ "$b" -ge 1024 ]; then
    echo "$(( b / 1024 )).$(( (b % 1024) * 10 / 1024 )) KB"
  else
    echo "${b} B"
  fi
}

format_durasi() {
  local s=$1
  printf "%02d:%02d:%02d" $((s/3600)) $(( (s%3600)/60 )) $((s%60))
}

# ─── status 1 baris, overwrite di tempat ─────────────────
# \r overwrite baris yang sama — tidak scroll, tidak bug cursor.
print_status() {
  local sukses="$1" gagal="$2" total_bytes="$3"
  local now; now=$(date +%s)
  local elapsed=$(( now - START_TIME ))
  local speed=0
  [ "$elapsed" -gt 0 ] && speed=$(( total_bytes / elapsed ))

  printf "\r\033[K  ${GREEN}✅ %s${NC}  ${RED}❌ %s${NC}  💾 %s  ⚡ %s/s  ⏱ %s" \
    "$sukses" "$gagal" \
    "$(format_bytes "$total_bytes")" \
    "$(format_bytes "$speed")" \
    "$(format_durasi "$elapsed")"
}

tampil_stats() {
  IFS='|' read -r sukses gagal total_bytes _speed last_file < "$STATS_FILE"
  sukses=${sukses:-0}; gagal=${gagal:-0}
  total_bytes=${total_bytes:-0}

  local now; now=$(date +%s)
  local elapsed=$(( now - START_TIME ))
  local speed=0
  [ "$elapsed" -gt 0 ] && speed=$(( total_bytes / elapsed ))

  echo ""
  echo -e "${BOLD}${CYAN}══════════════════════════════════════════${NC}"
  echo -e " ${BOLD}📊 STATISTIK DOWNLOAD${NC}"
  echo -e "${CYAN}══════════════════════════════════════════${NC}"
  printf " %-20s %s\n"               "🎯 Target:"    "$USER_IG"
  printf " %-20s %s\n"               "📁 Output:"    "$OUT_DIR"
  printf " %-20s %s\n"               "🕐 Mulai:"     "$START_DATE"
  printf " %-20s %s\n"               "🕑 Selesai:"   "$(date "+%Y-%m-%d %H:%M:%S")"
  printf " %-20s %s\n"               "⏱  Durasi:"    "$(format_durasi "$elapsed")"
  printf " %-20s ${GREEN}%s${NC}\n"  "✅ Sukses:"    "$sukses file"
  printf " %-20s ${RED}%s${NC}\n"    "❌ Gagal:"     "$gagal file"
  printf " %-20s %s\n"               "📦 Total:"     "$((sukses + gagal)) file"
  printf " %-20s %s\n"               "💾 Ukuran:"    "$(format_bytes "$total_bytes")"
  printf " %-20s %s\n"               "⚡ Avg Speed:" "$(format_bytes "$speed")/s"
  echo -e "${CYAN}══════════════════════════════════════════${NC}"
  echo -e "  ${BLUE}📄 log: $LOG_FILE${NC}"
  echo ""
  rm -f "$STATS_FILE"
}

cek_command() {
  command -v "$1" &>/dev/null
}

# ═══════════════════════════════════════════
# SETUP PERTAMA KALI
# ═══════════════════════════════════════════
if [ ! -f "$CONFIG_FILE" ]; then
  clear
  echo -e "${BOLD}${CYAN}"
  echo "  ╔══════════════════════════════════════╗"
  echo "  ║     🚀 IGDOWNLOAD - SETUP AWAL       ║"
  echo "  ║   proses ini hanya terjadi sekali!   ║"
  echo "  ╚══════════════════════════════════════╝"
  echo -e "${NC}"
  echo -e "${YELLOW}Halo! Sebelum mulai, kita perlu install beberapa dependencies.${NC}"
  echo -e "${YELLOW}Tenang, ini cuma dilakukan SATU KALI aja. Selanjutnya langsung jalan.${NC}\n"
  read -p "$(echo -e ${BOLD}"Siap? Tekan Enter untuk mulai setup..."${NC})"

  echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}📦 CEK & INSTALL DEPENDENCIES${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

  if ! cek_command pipx; then
    echo -e "${YELLOW}⏳ menginstall pipx...${NC}"
    sudo pacman -S --noconfirm python-pipx 2>/dev/null || pip install pipx --break-system-packages 2>/dev/null
    pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
  fi
  echo -e "${GREEN}✅ pipx OK${NC}"

  if ! cek_command gallery-dl; then
    echo -e "${YELLOW}⏳ menginstall gallery-dl...${NC}"
    pipx install gallery-dl
    export PATH="$HOME/.local/bin:$PATH"
  fi
  echo -e "${GREEN}✅ gallery-dl OK${NC}"

  if ! cek_command yt-dlp; then
    echo -e "${YELLOW}⏳ menginstall yt-dlp (untuk download video)...${NC}"
    pipx install yt-dlp
    pipx inject gallery-dl yt-dlp 2>/dev/null || true
  fi
  echo -e "${GREEN}✅ yt-dlp OK${NC}"

  echo -e "\n${GREEN}✔ semua dependencies berhasil diinstall!${NC}\n"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

  echo -e "\n${BOLD}🍪 SETUP COOKIES INSTAGRAM${NC}"
  echo -e "${CYAN}Cookies dibutuhkan agar bisa download konten Instagram.${NC}\n"
  echo -e "Pilih cara setup cookies:"
  echo -e "  ${BOLD}1${NC}) Saya punya file cookies.txt"
  echo -e "  ${BOLD}2${NC}) Saya mau paste sessionid dari browser\n"
  read -p "$(echo -e ${BOLD}"Pilih [1/2]: "${NC})" COOKIES_CHOICE

  if [ "$COOKIES_CHOICE" = "1" ]; then
    echo -e "\n${CYAN}ℹ  Cara export cookies.txt dari Brave/Chrome:${NC}"
    echo -e "   1. Install extension ${BOLD}'Get cookies.txt LOCALLY'${NC} di browser"
    echo -e "   2. Buka instagram.com & pastikan sudah login"
    echo -e "   3. Klik extension → Export → simpan filenya\n"
    read -p "$(echo -e ${BOLD}"Path file cookies.txt: "${NC})" INPUT_COOKIES
    INPUT_COOKIES="${INPUT_COOKIES/#\~/$HOME}"
    if [ ! -f "$INPUT_COOKIES" ]; then
      echo -e "${RED}❌ file tidak ditemukan: $INPUT_COOKIES${NC}"
      exit 1
    fi
    cp "$INPUT_COOKIES" "$COOKIES_FILE"
    echo -e "${GREEN}✅ cookies disalin ke $COOKIES_FILE${NC}"

  elif [ "$COOKIES_CHOICE" = "2" ]; then
    echo -e "\n${CYAN}ℹ  Cara ambil sessionid dari browser:${NC}"
    echo -e "   1. Buka instagram.com di browser, pastikan sudah login"
    echo -e "   2. Tekan ${BOLD}F12${NC} → tab ${BOLD}Application${NC} → ${BOLD}Cookies${NC} → ${BOLD}instagram.com${NC}"
    echo -e "   3. Cari cookie bernama ${BOLD}sessionid${NC}, copy nilainya\n"
    read -p "$(echo -e ${BOLD}"Paste sessionid kamu: "${NC})" SESSION_ID
    [ -z "$SESSION_ID" ] && echo -e "${RED}❌ session ID tidak boleh kosong${NC}" && exit 1
    read -p "$(echo -e ${BOLD}"Username Instagram kamu: "${NC})" MY_IG
    [ -z "$MY_IG" ] && echo -e "${RED}❌ username tidak boleh kosong${NC}" && exit 1

    cat > "$COOKIES_FILE" << COOKEOF
# Netscape HTTP Cookie File
.instagram.com	TRUE	/	TRUE	1999999999	sessionid	$SESSION_ID
COOKEOF
    echo -e "${GREEN}✅ cookies tersimpan!${NC}"
  else
    echo -e "${RED}❌ pilihan tidak valid${NC}"
    exit 1
  fi

  echo -e "\n${YELLOW}⏳ memvalidasi cookies...${NC}"
  VALIDATE=$(gallery-dl --cookies "$COOKIES_FILE" --get-urls "https://www.instagram.com/instagram/" 2>&1 | head -3)
  if echo "$VALIDATE" | grep -qiE "login|checkpoint|error|403"; then
    echo -e "${RED}❌ cookies tidak valid atau expired. Coba export ulang.${NC}"
    rm -f "$COOKIES_FILE"
    exit 1
  fi
  echo -e "${GREEN}✅ cookies valid!${NC}"

  echo "SETUP_DONE=1" > "$CONFIG_FILE"
  echo "COOKIES_FILE=$COOKIES_FILE" >> "$CONFIG_FILE"

  echo -e "\n${GREEN}${BOLD}✔ Setup selesai! Selanjutnya script langsung jalan tanpa setup lagi.${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
  sleep 1
fi

# load config
source "$CONFIG_FILE"
export PATH="$HOME/.local/bin:$PATH"

if [ ! -f "$COOKIES_FILE" ]; then
  echo -e "${RED}❌ cookies.txt tidak ditemukan!${NC}"
  echo -e "${YELLOW}Hapus file .igdownload_config lalu jalankan script lagi untuk setup ulang.${NC}"
  exit 1
fi

# ═══════════════════════════════════════════
# MAIN - INPUT USER
# ═══════════════════════════════════════════
clear
echo -e "${BOLD}${MAGENTA}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║        📸 IGDOWNLOAD v1.0            ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

read -p "$(echo -e ${BOLD}"🎯 Username IG target: "${NC})" USER_IG
[ -z "$USER_IG" ] && echo -e "${RED}❌ username tidak boleh kosong${NC}" && exit 1

echo -e "${CYAN}ℹ  Kosongkan untuk default: ~/Pictures/$USER_IG${NC}"
read -p "$(echo -e ${BOLD}"📁 Folder output: "${NC})" OUT_DIR
[ -z "$OUT_DIR" ] && OUT_DIR="$HOME/Pictures/$USER_IG"
OUT_DIR="${OUT_DIR/#\~/$HOME}"

mkdir -p "$OUT_DIR"
echo -e "${GREEN}✅ output: $OUT_DIR${NC}\n"

# ─── variabel tracking ───────────────────────────────────
START_TIME=$(date +%s)
START_DATE=$(date "+%Y-%m-%d %H:%M:%S")
LOG_FILE="$OUT_DIR/download.log"
STATS_FILE=$(mktemp)
echo "0|0|0|0|-" > "$STATS_FILE"

trap 'printf "\n"; echo -e "${YELLOW}⚠  dihentikan manual${NC}"; tampil_stats; exit 130' INT

DELAY=$((RANDOM % 4 + 2))
echo -e "${YELLOW}⏳ mulai dalam $DELAY detik...${NC}"
sleep "$DELAY"

# ─── header download ─────────────────────────────────────
echo ""
echo -e "${BOLD}${MAGENTA}  📸 IGDOWNLOAD  ${CYAN}@${USER_IG}${NC}"
echo -e "${BLUE}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${CYAN}output: $OUT_DIR${NC}"
echo -e "${BLUE}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Baris status awal — akan di-overwrite tiap event oleh \r
printf "  Memulai download...\n"

export -f format_bytes format_durasi print_status
export START_TIME STATS_FILE
export RED GREEN YELLOW BLUE CYAN BOLD NC MAGENTA LOG_FILE OUT_DIR USER_IG START_DATE

# ─── jalankan gallery-dl & parse output ──────────────────
gallery-dl \
  --cookies "$COOKIES_FILE" \
  --directory "$OUT_DIR" \
  --filename "{filename}.{extension}" \
  --sleep-request 2.0 \
  --retries 3 \
  "https://www.instagram.com/$USER_IG/" 2>&1 | tee "$LOG_FILE" | while IFS= read -r line; do

  IFS='|' read -r SUKSES GAGAL TOTAL_BYTES _SPEED LAST_FILE < "$STATS_FILE"
  SUKSES=${SUKSES:-0}; GAGAL=${GAGAL:-0}; TOTAL_BYTES=${TOTAL_BYTES:-0}

  # ── abaikan noise yt-dlp ─────────────────────────────
  if echo "$line" | grep -q "Cannot import yt-dlp"; then
    :

  # ── file berhasil didownload ──────────────────────────
  elif echo "$line" | grep -qE "^\./|^/home/|^$OUT_DIR"; then
    SUKSES=$(( SUKSES + 1 ))
    FILEPATH=$(echo "$line" | awk '{print $1}')
    if [ -f "$FILEPATH" ]; then
      FILE_SIZE=$(stat -c%s "$FILEPATH" 2>/dev/null || echo 0)
      TOTAL_BYTES=$(( TOTAL_BYTES + FILE_SIZE ))
    fi
    LAST_FILE=$(basename "$FILEPATH")
    echo "${SUKSES}|${GAGAL}|${TOTAL_BYTES}|0|${LAST_FILE}" > "$STATS_FILE"
    print_status "$SUKSES" "$GAGAL" "$TOTAL_BYTES"

  # ── file di-skip (sudah ada) ──────────────────────────
  elif echo "$line" | grep -q "^# "; then
    SUKSES=$(( SUKSES + 1 ))
    LAST_FILE=$(basename "$(echo "$line" | sed 's/^# //')")
    echo "${SUKSES}|${GAGAL}|${TOTAL_BYTES}|0|${LAST_FILE}" > "$STATS_FILE"
    print_status "$SUKSES" "$GAGAL" "$TOTAL_BYTES"

  # ── error ────────────────────────────────────────────
  elif echo "$line" | grep -q "\[error\]"; then
    GAGAL=$(( GAGAL + 1 ))
    echo "${SUKSES}|${GAGAL}|${TOTAL_BYTES}|0|${LAST_FILE}" > "$STATS_FILE"
    printf "\n  ${RED}❌ ${line}${NC}\n"
    print_status "$SUKSES" "$GAGAL" "$TOTAL_BYTES"

  # ── warning ──────────────────────────────────────────
  elif echo "$line" | grep -q "\[warning\]"; then
    printf "\n  ${YELLOW}⚠  ${line}${NC}\n"
    print_status "$SUKSES" "$GAGAL" "$TOTAL_BYTES"

  # ── rate limit ───────────────────────────────────────
  elif echo "$line" | grep -qiE "429|Too Many|rate.limit"; then
    WAIT=$(( RANDOM % 20 + 10 ))
    printf "\n  ${YELLOW}⚠  rate limit — nunggu ${WAIT}s...${NC}\n"
    sleep "$WAIT"
    print_status "$SUKSES" "$GAGAL" "$TOTAL_BYTES"

  # ── cookies expired ──────────────────────────────────
  elif echo "$line" | grep -qiE "login.*required|Not logged in|checkpoint"; then
    printf "\n"
    echo -e "${RED}❌ cookies expired! hapus .igdownload_config lalu jalankan ulang.${NC}"
    rm -f "$CONFIG_FILE"
    break
  fi

done

# newline bersih setelah status line terakhir
printf "\n"

tampil_stats
