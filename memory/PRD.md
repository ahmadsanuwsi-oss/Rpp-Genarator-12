# PRD — RPP Studio (Perangkat Ajar Guru)

## Problem Statement (original, Bahasa Indonesia)
"buatkan rpp dengan 2 metode 1 manual 2 input file pdf/gambar alur seperti di file upload pdf baik saat manual atu upload file file otomatis tersimpan dan bisa di print baik ke prin atau pdf bisa print semua halaman menggunakan kertas a4 setiap bikin rpp file di simpan dan di print kapan saja"

Plus tambahan: tombol/generator untuk Prota, Prosem, KKTP, Alokasi Waktu, ATP, Asesmen, LKPD, Poster — berbasis Capaian Pembelajaran, Alur Tujuan Pembelajaran, dan materi/lingkup materi.

## User Choices
- Model AI: Gemini 3.1 Pro (gemini-3.1-pro-preview)
- Autentikasi: Login per guru (JWT, Bearer token)
- Alur upload: hasil ekstraksi AI ditampilkan di form untuk diedit dulu sebelum disimpan
- Tema: profesional & rapi (Organic Earthy Academic — Deep Emerald + Warm Sand + Gold)

## Architecture
- Frontend: React (CRA) + Tailwind + shadcn, react-router, sonner toasts. Fonts: Plus Jakarta Sans (UI), Times New Roman (dokumen cetak).
- Backend: FastAPI + Motor (MongoDB), JWT auth (bcrypt + PyJWT), emergentintegrations LlmChat (Gemini) for extraction & generation.
- Print: CSS @media print + @page A4; Viewer renders an A4 sheet with Kop Sekolah + signature block.

## User Persona
Guru MI/SD/SMP/SMA di Indonesia yang menyusun administrasi pembelajaran (Kurikulum Merdeka / Berbasis Cinta) dan butuh membuat, menyimpan, serta mencetak dokumen dengan cepat.

## Core Requirements (static)
1. Buat RPP manual via form multi-bagian.
2. Buat RPP dari unggah PDF/gambar → AI (Gemini) ekstrak & isi form → edit → simpan.
3. Semua dokumen tersimpan otomatis dan bisa dibuka/cetak (printer atau PDF) kapan saja pada kertas A4.
4. Generator AI: Prota, Prosem, KKTP, Alokasi Waktu, ATP, Asesmen, LKPD, Poster.
5. Login per guru + profil (NIP, sekolah, kepala sekolah) yang mengisi identitas otomatis.

## Implemented (2026-06)
- [x] Auth JWT (register/login/me/profile) + akun demo guru@demo.com / guru123.
- [x] Dashboard: statistik, aksi buat RPP (manual & upload), 8 tombol generator, pustaka dokumen (cari/filter, lihat/cetak/hapus).
- [x] RPP Editor: tab Manual & Upload; ekstraksi Gemini dari PDF/PNG/JPG; edit sebelum simpan.
- [x] Generator generik untuk 8 jenis dokumen (HTML editable A4, contentEditable) via Gemini.
- [x] Viewer A4 dengan Kop Sekolah + blok tanda tangan; cetak/PDF; edit.
- [x] Profil guru; identitas prefill.
- [x] Diverifikasi testing agent: backend 100%, frontend 100%.

## Backlog / Remaining
- P1: Ekspor DOCX; template Kurikulum Merdeka vs K13 terpisah; kop sekolah dengan logo/alamat.
- P2: Poster dengan gambar (image generation); duplikasi dokumen; tag/kategori; multi-halaman page-break halus untuk tabel panjang.
- P2: CORS explicit origin (saat ini '*'; aman untuk Bearer, rapikan untuk produksi).

## Next Tasks
- Tunggu feedback pengguna; tambahkan ekspor DOCX / logo kop sekolah bila diminta.
