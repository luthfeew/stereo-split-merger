#!/usr/bin/env python3
"""
gui.py
Antarmuka Grafis (GUI) modern menggunakan CustomTkinter
untuk menggabungkan dua lagu ke channel Kiri (Left) dan Kanan (Right).
"""

import os
import sys
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pydub import AudioSegment
from merge_audio import apply_deharsh

# Setup tema CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class AudioMergerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Stereo Split Merger - Left & Right Channel")
        self.geometry("640x760")
        self.minsize(580, 700)

        # State Variables
        self.left_file_path = ctk.StringVar(value="")
        self.right_file_path = ctk.StringVar(value="")
        self.output_file_path = ctk.StringVar(value="")
        self.mode_var = ctk.StringVar(value="pad")
        self.normalize_var = ctk.BooleanVar(value=True)
        self.format_var = ctk.StringVar(value="mp3")
        self.deharsh_var = ctk.BooleanVar(value=True)
        self.deharsh_level_var = ctk.StringVar(value="Sedang (-4 dB)")

        self.is_processing = False
        self._build_ui()

    def _build_ui(self):
        # Header Frame
        header_frame = ctk.CTkFrame(self, corner_radius=10)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🎧 Stereo Split Merger",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(12, 2))

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Jadikan 2 lagu menjadi mono, lalu gabungkan ke channel Kiri (L) & Kanan (R)",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        subtitle_label.pack(pady=(0, 12))

        # Main Scrollable Frame (biar responsive di layar kecil)
        content_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. Left Channel Section
        left_box = ctk.CTkFrame(content_frame, corner_radius=8, fg_color=("gray85", "gray17"))
        left_box.pack(fill="x", pady=8, padx=5)

        left_header = ctk.CTkLabel(
            left_box,
            text="◀ CHANNEL KIRI (LEFT)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B8ED0"
        )
        left_header.pack(anchor="w", padx=15, pady=(10, 4))

        left_input_frame = ctk.CTkFrame(left_box, fg_color="transparent")
        left_input_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.left_entry = ctk.CTkEntry(
            left_input_frame,
            textvariable=self.left_file_path,
            placeholder_text="Pilih file lagu untuk telinga kiri..."
        )
        self.left_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        left_btn = ctk.CTkButton(
            left_input_frame,
            text="Pilih File",
            width=90,
            command=self._browse_left
        )
        left_btn.pack(side="right")

        # 2. Right Channel Section
        right_box = ctk.CTkFrame(content_frame, corner_radius=8, fg_color=("gray85", "gray17"))
        right_box.pack(fill="x", pady=8, padx=5)

        right_header = ctk.CTkLabel(
            right_box,
            text="▶ CHANNEL KANAN (RIGHT)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#E07A5F"
        )
        right_header.pack(anchor="w", padx=15, pady=(10, 4))

        right_input_frame = ctk.CTkFrame(right_box, fg_color="transparent")
        right_input_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.right_entry = ctk.CTkEntry(
            right_input_frame,
            textvariable=self.right_file_path,
            placeholder_text="Pilih file lagu untuk telinga kanan..."
        )
        self.right_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        right_btn = ctk.CTkButton(
            right_input_frame,
            text="Pilih File",
            width=90,
            fg_color="#D97706",
            hover_color="#B45309",
            command=self._browse_right
        )
        right_btn.pack(side="right")

        # 3. Settings Section
        settings_box = ctk.CTkFrame(content_frame, corner_radius=8, fg_color=("gray85", "gray17"))
        settings_box.pack(fill="x", pady=8, padx=5)

        settings_header = ctk.CTkLabel(
            settings_box,
            text="⚙ PENGATURAN",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        settings_header.pack(anchor="w", padx=15, pady=(10, 8))

        # Mode Durasi
        mode_label = ctk.CTkLabel(settings_box, text="Jika durasi kedua lagu berbeda:", font=ctk.CTkFont(size=13))
        mode_label.pack(anchor="w", padx=15)

        mode_radio_frame = ctk.CTkFrame(settings_box, fg_color="transparent")
        mode_radio_frame.pack(anchor="w", padx=15, pady=(4, 10))

        radio_pad = ctk.CTkRadioButton(
            mode_radio_frame,
            text="Tambah Keheningan / Silence (Lagu tetap selesai)",
            variable=self.mode_var,
            value="pad"
        )
        radio_pad.pack(anchor="w", pady=2)

        radio_trim = ctk.CTkRadioButton(
            mode_radio_frame,
            text="Potong / Trim (Mengikuti lagu yang lebih pendek)",
            variable=self.mode_var,
            value="trim"
        )
        radio_trim.pack(anchor="w", pady=2)

        # Checkbox Normalisasi Volume
        norm_cb = ctk.CTkCheckBox(
            settings_box,
            text="Seimbangkan Volume Kedua Lagu (Auto Normalization)",
            variable=self.normalize_var
        )
        norm_cb.pack(anchor="w", padx=15, pady=(0, 10))

        # Separator De-Harsh
        deharsh_sep = ctk.CTkFrame(settings_box, height=1, fg_color=("gray75", "gray28"))
        deharsh_sep.pack(fill="x", padx=15, pady=(0, 10))

        # Checkbox De-Harsh / Peredam Frekuensi Tajam
        deharsh_cb = ctk.CTkCheckBox(
            settings_box,
            text="Peredam Frekuensi Tajam (De-Harsh / Tame Piercing Highs)",
            variable=self.deharsh_var,
            command=self._on_deharsh_toggle
        )
        deharsh_cb.pack(anchor="w", padx=15, pady=(0, 3))

        deharsh_desc = ctk.CTkLabel(
            settings_box,
            text="Meredam frekuensi 3.5 kHz - 6 kHz agar instrumen tidak menusuk telinga saat vokal kosong",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            wraplength=480,
            justify="left"
        )
        deharsh_desc.pack(anchor="w", padx=43, pady=(0, 8))

        self.deharsh_options_frame = ctk.CTkFrame(settings_box, fg_color="transparent")
        self.deharsh_options_frame.pack(fill="x", padx=43, pady=(0, 12))

        deharsh_level_label = ctk.CTkLabel(
            self.deharsh_options_frame,
            text="Intensitas Peredaman:",
            font=ctk.CTkFont(size=12)
        )
        deharsh_level_label.pack(side="left", padx=(0, 10))

        self.deharsh_menu = ctk.CTkOptionMenu(
            self.deharsh_options_frame,
            values=["Ringan (-2 dB)", "Sedang (-4 dB)", "Kuat (-6 dB)"],
            variable=self.deharsh_level_var,
            width=150
        )
        self.deharsh_menu.pack(side="left")

        # 4. Output Section
        output_box = ctk.CTkFrame(content_frame, corner_radius=8, fg_color=("gray85", "gray17"))
        output_box.pack(fill="x", pady=8, padx=5)

        out_header = ctk.CTkLabel(
            output_box,
            text="💾 OUTPUT",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        out_header.pack(anchor="w", padx=15, pady=(10, 4))

        out_input_frame = ctk.CTkFrame(output_box, fg_color="transparent")
        out_input_frame.pack(fill="x", padx=15, pady=(0, 6))

        self.out_entry = ctk.CTkEntry(
            out_input_frame,
            textvariable=self.output_file_path,
            placeholder_text="Pilih lokasi simpan hasil gabungan..."
        )
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        out_btn = ctk.CTkButton(
            out_input_frame,
            text="Simpan Ke",
            width=90,
            command=self._browse_output
        )
        out_btn.pack(side="right")

        # Format option row
        format_frame = ctk.CTkFrame(output_box, fg_color="transparent")
        format_frame.pack(fill="x", padx=15, pady=(0, 10))

        format_label = ctk.CTkLabel(format_frame, text="Format Audio:", font=ctk.CTkFont(size=12))
        format_label.pack(side="left", padx=(0, 8))

        self.format_menu = ctk.CTkOptionMenu(
            format_frame,
            values=["mp3", "wav", "flac", "ogg", "m4a"],
            variable=self.format_var,
            width=90,
            command=self._on_format_changed
        )
        self.format_menu.pack(side="left")

        # Bottom Frame (Status & Action Button)
        bottom_frame = ctk.CTkFrame(self, corner_radius=10)
        bottom_frame.pack(fill="x", padx=20, pady=(10, 20))

        self.status_label = ctk.CTkLabel(
            bottom_frame,
            text="Siap menggabungkan lagu.",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.status_label.pack(pady=(10, 4))

        self.progress_bar = ctk.CTkProgressBar(bottom_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.merge_btn = ctk.CTkButton(
            bottom_frame,
            text="⚡ Gabungkan Audio Sekarang",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=42,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._start_merge_thread
        )
        self.merge_btn.pack(fill="x", padx=20, pady=(0, 12))

    def _on_deharsh_toggle(self):
        state = "normal" if self.deharsh_var.get() else "disabled"
        self.deharsh_menu.configure(state=state)

    def _browse_left(self):
        file_path = filedialog.askopenfilename(
            title="Pilih Lagu Kiri (Left Channel)",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.wma *.opus"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.left_file_path.set(file_path)
            self._suggest_output_name()

    def _browse_right(self):
        file_path = filedialog.askopenfilename(
            title="Pilih Lagu Kanan (Right Channel)",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.wma *.opus"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.right_file_path.set(file_path)
            self._suggest_output_name()

    def _suggest_output_name(self):
        if not self.output_file_path.get() and self.left_file_path.get():
            left_dir = os.path.dirname(self.left_file_path.get())
            ext = self.format_var.get()
            suggested = os.path.join(left_dir, f"merged_stereo.{ext}")
            self.output_file_path.set(suggested)

    def _on_format_changed(self, choice):
        current_out = self.output_file_path.get()
        if current_out:
            base, _ = os.path.splitext(current_out)
            self.output_file_path.set(f"{base}.{choice}")

    def _browse_output(self):
        ext = self.format_var.get()
        file_path = filedialog.asksaveasfilename(
            title="Simpan File Stereo Hasil Gabungan",
            defaultextension=f".{ext}",
            filetypes=[(f"{ext.upper()} Audio", f"*.{ext}"), ("All Files", "*.*")]
        )
        if file_path:
            self.output_file_path.set(file_path)

    def _set_ui_processing(self, processing: bool):
        self.is_processing = processing
        if processing:
            self.merge_btn.configure(state="disabled", text="⏳ Sedang Memproses...")
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
        else:
            self.merge_btn.configure(state="normal", text="⚡ Gabungkan Audio Sekarang")
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(1.0)

    def _update_status(self, text: str, is_error: bool = False):
        color = "#EF4444" if is_error else ("#10B981" if "Berhasil" in text else "gray70")
        self.status_label.configure(text=text, text_color=color)

    def _start_merge_thread(self):
        left = self.left_file_path.get().strip()
        right = self.right_file_path.get().strip()
        out = self.output_file_path.get().strip()

        if not left or not os.path.isfile(left):
            messagebox.showwarning("Peringatan", "Silakan pilih file lagu KIRI yang valid.")
            return
        if not right or not os.path.isfile(right):
            messagebox.showwarning("Peringatan", "Silakan pilih file lagu KANAN yang valid.")
            return
        if not out:
            messagebox.showwarning("Peringatan", "Tentukan lokasi file output terlebih dahulu.")
            return

        self._set_ui_processing(True)
        self._update_status("Memuat dan mengonversi audio ke mono...")

        # Mapping intensitas peredam
        level_map = {
            "Ringan (-2 dB)": "light",
            "Sedang (-4 dB)": "medium",
            "Kuat (-6 dB)": "strong"
        }
        chosen_level = level_map.get(self.deharsh_level_var.get(), "medium")

        thread = threading.Thread(
            target=self._run_merge,
            args=(
                left,
                right,
                out,
                self.mode_var.get(),
                self.normalize_var.get(),
                self.deharsh_var.get(),
                chosen_level
            ),
            daemon=True
        )
        thread.start()

    def _run_merge(self, left_path, right_path, output_path, mode, normalize, deharsh, deharsh_level):
        try:
            # 1. Load audio
            self.after(0, lambda: self._update_status("Membaca file audio..."))
            left = AudioSegment.from_file(left_path)
            right = AudioSegment.from_file(right_path)

            # 2. Convert to mono
            self.after(0, lambda: self._update_status("Mengonversi ke 1 channel mono..."))
            left = left.set_channels(1)
            right = right.set_channels(1)

            # 3. De-harsh filtering jika diaktifkan
            if deharsh:
                self.after(0, lambda: self._update_status(f"Meredam frekuensi menusuk (Level: {deharsh_level})..."))
                left = apply_deharsh(left, level=deharsh_level)
                right = apply_deharsh(right, level=deharsh_level)

            # 4. Normalize volume jika diminta
            if normalize:
                self.after(0, lambda: self._update_status("Menyeimbangkan volume dBFS..."))
                target_dbfs = max(left.dBFS, right.dBFS)
                left = left.apply_gain(target_dbfs - left.dBFS)
                right = right.apply_gain(target_dbfs - right.dBFS)

            # 5. Harmonize frame rate & width
            target_rate = max(left.frame_rate, right.frame_rate)
            target_width = max(left.sample_width, right.sample_width)
            left = left.set_frame_rate(target_rate).set_sample_width(target_width)
            right = right.set_frame_rate(target_rate).set_sample_width(target_width)

            # 6. Handle length differences
            bytes_left = len(left.raw_data)
            bytes_right = len(right.raw_data)
            diff = bytes_left - bytes_right

            if mode == "pad":
                if diff > 0:
                    right = right._spawn(right.raw_data + b"\x00" * diff)
                elif diff < 0:
                    left = left._spawn(left.raw_data + b"\x00" * (-diff))
            elif mode == "trim":
                min_bytes = min(bytes_left, bytes_right)
                left = left._spawn(left.raw_data[:min_bytes])
                right = right._spawn(right.raw_data[:min_bytes])

            # 6. Combine to stereo
            self.after(0, lambda: self._update_status("Menggabungkan stereo (L & R)..."))
            stereo = AudioSegment.from_mono_audiosegments(left, right)

            # 7. Export
            self.after(0, lambda: self._update_status("Mengekspor file audio..."))
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            out_format = os.path.splitext(output_path)[1].lstrip(".").lower() or "mp3"
            stereo.export(output_path, format=out_format)

            # Sukses
            self.after(0, lambda: self._on_success(output_path))
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: self._on_error(err_msg))

    def _on_success(self, output_path):
        self._set_ui_processing(False)
        self._update_status(f"Berhasil disimpan: {os.path.basename(output_path)}")
        res = messagebox.askyesno(
            "Berhasil!",
            f"File berhasil dibuat:\n{output_path}\n\nApakah ingin membuka foldernya sekarang?"
        )
        if res:
            out_dir = os.path.dirname(output_path) or "."
            os.startfile(out_dir)

    def _on_error(self, error_message):
        self._set_ui_processing(False)
        self._update_status(f"Error: {error_message}", is_error=True)
        messagebox.showerror("Terjadi Kesalahan", f"Gagal memproses audio:\n{error_message}")


if __name__ == "__main__":
    app = AudioMergerApp()
    app.mainloop()
