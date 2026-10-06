#!/usr/bin/env python3
"""
merge_audio.py
Menggabungkan 2 file audio ke dalam 1 output stereo:
- Lagu 1 dikonversi ke Mono -> Left Channel
- Lagu 2 dikonversi ke Mono -> Right Channel
"""

import os
import sys
import argparse
import numpy as np
import scipy.signal as signal
from pydub import AudioSegment


def get_high_shelf_coeffs(fs: int, f0: float = 4000.0, gain_db: float = -3.5, Q: float = 0.707):
    """
    Menghasilkan koefisien biquad High-Shelf filter (RBJ Audio EQ Cookbook).
    """
    f0 = min(float(f0), fs * 0.45)
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * f0 / fs
    alpha = np.sin(w0) / (2.0 * Q)
    cos_w0 = np.cos(w0)
    sqrt_A = np.sqrt(A)

    b0 = A * ((A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * sqrt_A * alpha)
    b1 = -2.0 * A * ((A - 1.0) + (A + 1.0) * cos_w0)
    b2 = A * ((A + 1.0) + (A - 1.0) * cos_w0 - 2.0 * sqrt_A * alpha)
    a0 = (A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * sqrt_A * alpha
    a1 = 2.0 * ((A - 1.0) - (A + 1.0) * cos_w0)
    a2 = (A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * sqrt_A * alpha

    return np.array([b0/a0, b1/a0, b2/a0], dtype=np.float64), np.array([1.0, a1/a0, a2/a0], dtype=np.float64)


def get_peaking_coeffs(fs: int, f0: float = 3500.0, gain_db: float = -2.5, Q: float = 1.2):
    """
    Menghasilkan koefisien biquad Peaking EQ filter di area frekuensi menusuk (3.5 kHz).
    """
    f0 = min(float(f0), fs * 0.42)
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * f0 / fs
    alpha = np.sin(w0) / (2.0 * Q)
    cos_w0 = np.cos(w0)

    b0 = 1.0 + alpha * A
    b1 = -2.0 * cos_w0
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * cos_w0
    a2 = 1.0 - alpha / A

    return np.array([b0/a0, b1/a0, b2/a0], dtype=np.float64), np.array([1.0, a1/a0, a2/a0], dtype=np.float64)


def apply_deharsh(segment: AudioSegment, level: str = "medium") -> AudioSegment:
    """
    Meredam frekuensi tajam / menusuk (3.5 kHz - 6 kHz) menggunakan kombinasi
    Peaking cut dan High-Shelf filter tanpa membuat audio menjadi mendam (muffled).

    :param segment: Objek AudioSegment (mono atau stereo).
    :param level: Tingkat peredaman ('light', 'medium', 'strong').
    :return: Objek AudioSegment yang sudah dihaluskan.
    """
    gain_map = {
        "light": (-2.0, -1.5),
        "medium": (-3.5, -2.5),
        "strong": (-5.5, -4.0)
    }
    shelf_db, peak_db = gain_map.get(str(level).lower(), (-3.5, -2.5))

    fs = segment.frame_rate
    b_hs, a_hs = get_high_shelf_coeffs(fs, f0=4000.0, gain_db=shelf_db)
    b_pk, a_pk = get_peaking_coeffs(fs, f0=3500.0, gain_db=peak_db)

    b = np.convolve(b_hs, b_pk)
    a = np.convolve(a_hs, a_pk)

    sw = segment.sample_width
    if sw == 1:
        raw = np.frombuffer(segment.raw_data, dtype=np.uint8).astype(np.float64) - 128.0
        max_val = 127.0
    elif sw == 2:
        raw = np.frombuffer(segment.raw_data, dtype=np.int16).astype(np.float64)
        max_val = 32767.0
    elif sw == 4:
        raw = np.frombuffer(segment.raw_data, dtype=np.int32).astype(np.float64)
        max_val = 2147483647.0
    else:
        segment = segment.set_sample_width(2)
        sw = 2
        raw = np.frombuffer(segment.raw_data, dtype=np.int16).astype(np.float64)
        max_val = 32767.0

    ch = segment.channels
    if ch > 1:
        raw = raw.reshape(-1, ch)
        filtered = signal.lfilter(b, a, raw, axis=0)
    else:
        filtered = signal.lfilter(b, a, raw)

    # Soft peak limiting untuk mencegah digital clipping
    peak = np.max(np.abs(filtered))
    if peak > max_val:
        filtered = filtered * (max_val / peak)

    filtered = np.clip(filtered, -max_val, max_val)

    if sw == 1:
        out_bytes = (filtered + 128.0).astype(np.uint8).tobytes()
    elif sw == 2:
        out_bytes = filtered.astype(np.int16).tobytes()
    elif sw == 4:
        out_bytes = filtered.astype(np.int32).tobytes()

    return segment._spawn(out_bytes)


def merge_left_right(
    left_path: str,
    right_path: str,
    output_path: str,
    mode: str = "pad",
    normalize_volume: bool = False,
    deharsh: bool = True,
    deharsh_level: str = "medium"
) -> None:
    """
    Menggabungkan dua audio ke stereo (left & right).

    :param left_path: Path file audio untuk channel kiri.
    :param right_path: Path file audio untuk channel kanan.
    :param output_path: Path file output stereo yang dihasilkan.
    :param mode: 'pad' untuk menambah hening pada audio yang lebih pendek,
                 'trim' untuk memotong audio yang lebih panjang.
    :param normalize_volume: Apakah perlu menormalkan dBFS kedua audio agar seimbang.
    :param deharsh: Redam frekuensi tajam/menusuk (3.5 kHz - 6 kHz).
    :param deharsh_level: Intensitas filter ('light', 'medium', 'strong').
    """
    if not os.path.isfile(left_path):
        raise FileNotFoundError(f"File audio kiri tidak ditemukan: {left_path}")
    if not os.path.isfile(right_path):
        raise FileNotFoundError(f"File audio kanan tidak ditemukan: {right_path}")

    print(f" Membaca audio kiri : {left_path}")
    left = AudioSegment.from_file(left_path)

    print(f" Membaca audio kanan: {right_path}")
    right = AudioSegment.from_file(right_path)

    # 1. Ubah kedua audio menjadi Mono
    print(" Mengonversi kedua audio ke Mono (1 channel)...")
    left = left.set_channels(1)
    right = right.set_channels(1)

    # 2. Redam frekuensi tajam (De-Harsh) jika diaktifkan
    if deharsh:
        print(f" Meredam frekuensi menusuk (De-Harsh EQ, intensitas: {deharsh_level})...")
        left = apply_deharsh(left, level=deharsh_level)
        right = apply_deharsh(right, level=deharsh_level)

    # 3. Opsional: Seimbangkan volume jika diminta
    if normalize_volume:
        print(" Menyeimbangkan volume (dBFS)...")
        target_dbfs = max(left.dBFS, right.dBFS)
        left = left.apply_gain(target_dbfs - left.dBFS)
        right = right.apply_gain(target_dbfs - right.dBFS)

    # 4. Samakan sample rate dan sample width agar kompatibel saat digabung
    target_rate = max(left.frame_rate, right.frame_rate)
    target_width = max(left.sample_width, right.sample_width)

    left = left.set_frame_rate(target_rate).set_sample_width(target_width)
    right = right.set_frame_rate(target_rate).set_sample_width(target_width)

    # 5. Tangani perbedaan durasi
    bytes_left = len(left.raw_data)
    bytes_right = len(right.raw_data)
    diff = bytes_left - bytes_right

    if mode == "pad":
        if diff > 0:
            print(f" Menambahkan silence pada channel kanan (+{diff // (target_rate * target_width)} detik)...")
            right = right._spawn(right.raw_data + b"\x00" * diff)
        elif diff < 0:
            print(f" Menambahkan silence pada channel kiri (+{(-diff) // (target_rate * target_width)} detik)...")
            left = left._spawn(left.raw_data + b"\x00" * (-diff))
    elif mode == "trim":
        min_bytes = min(bytes_left, bytes_right)
        print(" Memotong audio agar panjangnya sama persis...")
        left = left._spawn(left.raw_data[:min_bytes])
        right = right._spawn(right.raw_data[:min_bytes])
    else:
        raise ValueError(f"Mode tidak dikenal: {mode}. Gunakan 'pad' atau 'trim'.")

    # 6. Gabungkan mono left dan mono right menjadi stereo
    print(" Menggabungkan ke Stereo (Left & Right)...")
    stereo = AudioSegment.from_mono_audiosegments(left, right)

    # 7. Export ke file output
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    out_format = os.path.splitext(output_path)[1].lstrip(".").lower() or "mp3"
    print(f" Menyimpan hasil ke: {output_path} (Format: {out_format})...")
    stereo.export(output_path, format=out_format)
    print(" Selesai! File berhasil dibuat.")


def main():
    parser = argparse.ArgumentParser(
        description="Gabungkan 2 lagu: Lagu 1 (Left Channel) & Lagu 2 (Right Channel)."
    )
    parser.add_argument("left", nargs="?", help="Path file lagu untuk channel kiri (Left)")
    parser.add_argument("right", nargs="?", help="Path file lagu untuk channel kanan (Right)")
    parser.add_argument("-o", "--output", default="merged_stereo.mp3", help="Nama file output (default: merged_stereo.mp3)")
    parser.add_argument(
        "-m", "--mode",
        choices=["pad", "trim"],
        default="pad",
        help="Penanganan durasi beda: 'pad' (tambah hening) atau 'trim' (potong durasi terpanjang). Default: pad"
    )
    parser.add_argument(
        "-n", "--normalize",
        action="store_true",
        help="Samakan level volume kedua lagu agar seimbang"
    )
    parser.add_argument(
        "--deharsh",
        action="store_true",
        default=True,
        help="Aktifkan peredam frekuensi tajam / menusuk (default: aktif)"
    )
    parser.add_argument(
        "--no-deharsh",
        dest="deharsh",
        action="store_false",
        help="Matikan peredam frekuensi tajam"
    )
    parser.add_argument(
        "--deharsh-level",
        choices=["light", "medium", "strong"],
        default="medium",
        help="Intensitas peredam frekuensi tajam (light, medium, strong). Default: medium"
    )

    args = parser.parse_args()

    left_file = args.left
    right_file = args.right

    # Jika tidak menyertakan argumen di terminal, minta input interaktif
    if not left_file:
        left_file = input("Masukkan path file lagu KIRI (Left): ").strip().strip('"')
    if not right_file:
        right_file = input("Masukkan path file lagu KANAN (Right): ").strip().strip('"')

    output_file = args.output
    if not args.left and not args.right:
        custom_out = input(f"Masukkan path output [{output_file}]: ").strip().strip('"')
        if custom_out:
            output_file = custom_out

    try:
        merge_left_right(
            left_path=left_file,
            right_path=right_file,
            output_path=output_file,
            mode=args.mode,
            normalize_volume=args.normalize,
            deharsh=args.deharsh,
            deharsh_level=args.deharsh_level
        )
    except Exception as e:
        print(f" Terjadi error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
