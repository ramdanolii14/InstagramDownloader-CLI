# Instagram Archive — Windows Desktop & CLI

Instagram Archive adalah pengembangan dari **InstagramDownloader-CLI** milik Ramdan Olii. Sekarang proyek menyediakan GUI desktop yang berjalan langsung di Windows, selain skrip Bash lama untuk Linux.

## Fitur

- **Windows native GUI** menggunakan Python Tkinter. Tidak membutuhkan WSL atau Git Bash.
- **Main menu, Download Account, Settings, dan About/GitHub**.
- **Arsip akun**: posts, reels, photos, tagged posts, reposts, stories yang masih aktif, highlights, highlight covers, avatar, dan informasi profil. Pilih **All available categories** untuk meminta semua kategori yang didukung extractor.
- **Carousel dan video** ditangani oleh gallery-dl; yt-dlp dipasang sebagai pendukung video.
- **Resume dan deduplikasi** melalui database download archive. Item yang sudah tercatat tidak perlu diunduh ulang.
- **Activity log**, tombol Stop, pemilihan folder output, dan indikator proses.
- **Personalisasi tampilan**: warna background, warna aksen, dan ukuran teks.
- **About/GitHub** menampilkan tautan profil dan repository pengembang, serta statistik publik GitHub saat koneksi tersedia.
- Skrip Bash ig-cli.sh tetap tersedia untuk pengguna Linux.

## Jalankan di Windows

### Cara mudah

1. Install Python 3.10 atau yang lebih baru dari situs resmi Python. Aktifkan opsi **Add Python to PATH** saat instalasi.
2. Download atau clone repository ini.
3. Jalankan **install_windows.bat** untuk memasang gallery-dl dan yt-dlp.
4. Jalankan **run_windows.bat** untuk membuka GUI.

Atau jalankan manual dari folder repository:

~~~powershell
py -3 -m pip install -r requirements.txt
py -3 app.py
~~~

Tkinter biasanya sudah disertakan pada instalasi resmi Python untuk Windows. Jika jendela GUI tidak dapat dibuka, periksa kembali instalasi Python.

## Cara mengarsipkan akun

1. Buka menu **Download account**.
2. Masukkan username akun sendiri atau URL profil Instagram.
3. Pilih file **cookies.txt** hasil ekspor dari sesi browser yang memang sudah login ke akun tersebut.
4. Pilih folder tujuan.
5. Pilih **All available categories** atau tentukan kategori secara manual.
6. Tekan **Start download** dan pantau Activity log.

Aplikasi menyimpan lokasi cookies di pengaturan lokal. Isi file cookies tidak disalin ke repository atau file pengaturan aplikasi. File cookies tetap merupakan kredensial sesi: jangan mengunggahnya ke GitHub, mengirimkannya ke orang lain, atau membagikannya melalui chat. Bila sesi sudah tidak berlaku, ekspor ulang cookies melalui cara resmi yang kamu gunakan dan pilih file baru di aplikasi.

## Lokasi file

- Pengaturan aplikasi: %APPDATA%\InstagramArchive\settings.json
- Folder unduhan: folder yang kamu pilih, lalu subfolder berdasarkan username.
- Log unduhan: download.log di folder arsip akun.
- Database resume: .gallery-dl-archive.sqlite3 di folder arsip akun.

Database archive membantu melewati item yang sudah berhasil dicatat saat proses diulang. Jika database tersebut dihapus, gallery-dl dapat memproses ulang item lama.

## Linux / CLI lama

Skrip Bash tetap dapat digunakan pada Linux:

~~~bash
chmod +x ig-cli.sh
./ig-cli.sh
~~~

GUI juga dapat dijalankan pada sistem yang memiliki Python dan Tkinter:

~~~bash
python3 -m pip install -r requirements.txt
python3 app.py
~~~

## Batasan dan penggunaan yang bertanggung jawab

- Gunakan aplikasi hanya untuk akun milikmu atau konten yang kamu punya izin untuk arsipkan.
- Aplikasi tidak melewati privasi akun, login, checkpoint, atau kontrol akses Instagram. Konten privat hanya dapat diakses bila sesi yang sah memang memiliki izin melihat konten tersebut.
- Stories yang sudah kedaluwarsa atau konten yang tidak lagi tersedia mungkin tidak dapat diambil. Kategori yang didukung extractor juga dapat berubah mengikuti perubahan Instagram.
- Instagram dapat membatasi permintaan atau mengubah sistemnya. Jika mendapat rate limit atau error autentikasi, hentikan percobaan berulang dan coba lagi setelah beberapa waktu.
- Pastikan penggunaan dan penyimpanan konten sesuai hak pemilik, privasi, serta ketentuan layanan Instagram.

## Teknologi

- Python + Tkinter — aplikasi desktop.
- gallery-dl — ekstraksi dan pengunduhan media.
- yt-dlp — dukungan pengunduhan video.
- GitHub Actions — pemeriksaan sintaks Python pada Windows dan Linux.

## Repository dan pengembang

- Pengembang: **Ramdan Olii** (@ramdanolii14)
- GitHub: https://github.com/ramdanolii14
- Repository: https://github.com/ramdanolii14/InstagramDownloader-CLI
