# 🎧 Stereo Split Merger (Dual Audio L/R Mixer)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-darkblue.svg)](https://customtkinter.tomschimansky.com/)
[![Audio Engine](https://img.shields.io/badge/Audio-Pydub%20%7C%20SciPy-orange.svg)](https://scipy.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Stereo Split Merger** adalah aplikasi desktop modern dan alat baris perintah (CLI) untuk menggabungkan dua file audio menjadi satu file audio stereo dengan pembagian channel:
- **Lagu 1 (Track Kiri / Left Channel)**
- **Lagu 2 (Track Kanan / Right Channel)**

Aplikasi ini dirancang khusus untuk kasus penggabungan dua lagu (misal: versi duet, cover mashup, vocal comparison, atau instrumen identik dengan vokal berbeda), dilengkapi dengan filter **De-Harsh DSP** untuk mencegah suara instrumen menusuk telinga saat bagian vokal kosong.

---

## ✨ Fitur Utama

- 🎧 **Stereo Channel Split**: Mengonversi kedua file ke mono dan memetakannya secara presisi ke telinga kiri (L) dan telinga kanan (R).
- 🎚 **Peredam Frekuensi Tajam (De-Harsh DSP Filter)**: 
  - Menggunakan kombinasi filter biquad IIR (*Peaking Cut 3.5 kHz* + *High-Shelf 4.0 kHz*) untuk menjinakkan frekuensi *cymbal/hi-hat/snare* yang menusuk saat vokal kosong.
  - Pilihan intensitas: **Ringan (-2 dB)**, **Sedang (-4 dB)**, dan **Kuat (-6 dB)**.
- ⏱ **Penanganan Durasi Fleksibel**:
  - `Pad`: Menambahkan keheningan (*silence*) pada lagu yang lebih pendek agar kedua lagu selesai utuh.
  - `Trim`: Memotong durasi mengikuti lagu yang paling pendek.
- 🔊 **Auto Volume Normalization**: Menyeimbangkan tingkat kenyaringan (dBFS) kedua track secara otomatis.
- 🎨 **Antarmuka Grafis Modern (GUI)**: Berbasis [CustomTkinter](https://customtkinter.tomschimansky.com/) dengan tampilan *Dark Mode*, indikator progres visual, dan pemilih file interaktif.
- ⌨️ **Dukungan Terminal / CLI Penuh**: Cocok untuk pemrosesan *batch* atau integrasi ke skrip lain.
- 💾 **Dukungan Multi-Format**: Ekspor ke MP3, WAV, FLAC, OGG, atau M4A.

---

## 🛠 Persyaratan Sistem

- **Python 3.8+**
- **FFmpeg**: Diperlukan oleh `pydub` untuk membaca dan mengekspor berbagai format audio (MP3, M4A, FLAC, dll).
  - *Windows*: Unduh via [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) atau instal via winget:
    ```powershell
    winget install Gyan.FFmpeg
    ```
  - *macOS*: `brew install ffmpeg`
  - *Linux*: `sudo apt install ffmpeg`

---

## 📦 Instalasi

1. Clone repositori ini:
   ```bash
   git clone https://github.com/luthfeew/stereo-split-merger.git
   cd stereo-split-merger
   ```

2. Instal dependensi Python:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Penggunaan

### 1. Menggunakan GUI (Antarmuka Grafis)
Jalankan perintah berikut:
```bash
python gui.py
```
- Pilih file untuk **Channel Kiri** dan **Channel Kanan**.
- Atur preferensi penanganan durasi (`Pad` atau `Trim`).
- Aktifkan fitur **Normalisasi Volume** dan **Peredam Frekuensi Tajam (De-Harsh)** sesuai kebutuhan.
- Tentukan lokasi output & format audio.
- Klik tombol **⚡ Gabungkan Audio Sekarang**.

---

### 2. Menggunakan CLI (Terminal)
Jalankan skrip [merge_audio.py](merge_audio.py) dengan parameter:

```bash
python merge_audio.py <file_kiri> <file_kanan> [opsi]
```

#### Contoh Perintah CLI:
```bash
# Penggabungan dasar dengan De-Harsh aktif (default: medium)
python merge_audio.py lagu_kiri.mp3 lagu_kanan.mp3 -o hasil_duet.mp3

# Menyeimbangkan volume dan menggunakan filter De-Harsh kuat
python merge_audio.py vocal_a.wav vocal_b.wav -o output.wav -n --deharsh-level strong

# Memotong lagu yang lebih panjang (trim)
python merge_audio.py lagu1.mp3 lagu2.mp3 -m trim -o hasil_cut.mp3

# Mematikan filter De-Harsh
python merge_audio.py lagu1.mp3 lagu2.mp3 --no-deharsh
```

#### Parameter CLI:
| Argumen | Keterangan |
| :--- | :--- |
| `left` | Path file audio untuk channel kiri (Left). |
| `right` | Path file audio untuk channel kanan (Right). |
| `-o, --output` | Nama dan path file hasil gabungan (default: `merged_stereo.mp3`). |
| `-m, --mode` | Mode durasi: `pad` (tambah hening) atau `trim` (potong). Default: `pad`. |
| `-n, --normalize` | Samakan tingkat volume (dBFS) kedua lagu. |
| `--deharsh` | Aktifkan peredam frekuensi menusuk (default: aktif). |
| `--no-deharsh` | Nonaktifkan peredam frekuensi menusuk. |
| `--deharsh-level` | Intensitas filter: `light`, `medium`, atau `strong` (default: `medium`). |

---

## 🔬 Penjelasan Teknis Filter De-Harsh DSP

Saat dua lagu dengan instrumen identik digabungkan, ketiadaan vokal pada bagian tertentu (*intro, interlude, solo*) membuat frekuensi tinggi pada instrumen (seperti *hi-hat, cymbals, dan synth*) menghantam telinga secara langsung tanpa penyeimbang vokal. Ditambah lagi dengan potensi perbedaan fase (*phase cancellation / comb filtering*) antar file, hal ini memicu suara tajam yang menusuk telinga.

Filter De-Harsh mengatasi masalah ini secara matematis:
1. **Peaking Cut Filter (3.5 kHz, Q=1.2)**: Mengurangi resonansi pada area kanal telinga manusia yang paling peka terhadap kelelahan pendengaran (*ear fatigue*).
2. **High-Shelf Filter (4.0 kHz, Q=0.707)**: Menurunkan frekuensi atas secara melandai dan halus tanpa memotong frekuensi secara ekstrem, sehingga instrumen tetap renyah tanpa terdengar teredam (*muffled*).
3. **Soft Peak Limiter**: Mencegah *digital clipping* setelah pemrosesan biquad.

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah lisensi [MIT](LICENSE). Silakan gunakan, modifikasi, dan kembangkan sesuai kebutuhan Anda.
