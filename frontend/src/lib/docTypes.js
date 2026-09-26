// Konfigurasi jenis dokumen
export const RPP_TYPE = {
  key: "rpp",
  label: "RPP / Modul Ajar",
  short: "RPP",
  icon: "FileText",
  desc: "Rencana Pelaksanaan Pembelajaran lengkap — buat manual atau unggah PDF/gambar.",
};

export const GENERATORS = [
  { key: "prota", label: "Program Tahunan", short: "Prota", icon: "CalendarRange", desc: "Rencana materi & alokasi waktu satu tahun ajaran." },
  { key: "prosem", label: "Program Semester", short: "Prosem", icon: "CalendarDays", desc: "Distribusi materi per minggu dalam satu semester." },
  { key: "kktp", label: "KKTP", short: "KKTP", icon: "ClipboardCheck", desc: "Kriteria Ketercapaian Tujuan Pembelajaran." },
  { key: "alokasi_waktu", label: "Alokasi Waktu", short: "Alokasi", icon: "Clock", desc: "Analisis pekan efektif & distribusi jam pelajaran." },
  { key: "atp", label: "Alur Tujuan Pembelajaran", short: "ATP", icon: "Waypoints", desc: "Urutan tujuan pembelajaran dari Capaian Pembelajaran." },
  { key: "asesmen", label: "Asesmen", short: "Asesmen", icon: "ListChecks", desc: "Kisi-kisi, soal PG & essay, beserta rubrik penilaian." },
  { key: "lkpd", label: "LKPD", short: "LKPD", icon: "PencilRuler", desc: "Lembar Kerja Peserta Didik siap cetak." },
  { key: "poster", label: "Poster Pembelajaran", short: "Poster", icon: "Image", desc: "Media poster ringkas sesuai capaian pembelajaran." },
];

export const TYPE_LABEL = {
  rpp: "RPP",
  prota: "Program Tahunan",
  prosem: "Program Semester",
  kktp: "KKTP",
  alokasi_waktu: "Alokasi Waktu",
  atp: "ATP",
  asesmen: "Asesmen",
  lkpd: "LKPD",
  poster: "Poster",
};

// Field RPP untuk form manual & hasil ekstraksi
export const RPP_IDENTITAS = [
  { key: "namaGuru", label: "Nama Guru" },
  { key: "nip", label: "NIP" },
  { key: "jabatan", label: "Jabatan" },
  { key: "namaSekolah", label: "Satuan Pendidikan / Sekolah" },
  { key: "mataPelajaran", label: "Mata Pelajaran" },
  { key: "kelas", label: "Kelas" },
  { key: "semester", label: "Semester" },
  { key: "fase", label: "Fase" },
  { key: "materiPokok", label: "Materi Pokok" },
  { key: "alokasiWaktu", label: "Alokasi Waktu" },
  { key: "tahunAjaran", label: "Tahun Ajaran" },
  { key: "namaKepalaSekolah", label: "Nama Kepala Sekolah" },
  { key: "nipKepalaSekolah", label: "NIP Kepala Sekolah" },
];

export const RPP_SECTIONS = [
  { key: "identifikasiPesertaDidik", label: "Identifikasi Peserta Didik" },
  { key: "capaianPembelajaran", label: "Capaian Pembelajaran (CP)" },
  { key: "dimensiProfilLulusan", label: "Dimensi Profil Lulusan" },
  { key: "topikPancaCinta", label: "Topik Panca Cinta" },
  { key: "materiIntegrasiKBC", label: "Materi Integrasi Kurikulum Berbasis Cinta (KBC)" },
  { key: "pemanfaatanDigital", label: "Pemanfaatan Digital" },
  { key: "lintasDisiplin", label: "Lintas Disiplin Ilmu" },
  { key: "tujuanPembelajaran", label: "Tujuan Pembelajaran" },
  { key: "praktikPedagogik", label: "Praktik Pedagogik / Model Pembelajaran" },
  { key: "kemitraan", label: "Kemitraan Pembelajaran" },
  { key: "kegiatanAwal", label: "Langkah Pembelajaran — Kegiatan Awal" },
  { key: "kegiatanInti", label: "Langkah Pembelajaran — Kegiatan Inti" },
  { key: "penutup", label: "Langkah Pembelajaran — Penutup" },
  { key: "asesmenAwal", label: "Asesmen Awal Pembelajaran" },
  { key: "asesmenProses", label: "Asesmen Proses Pembelajaran" },
  { key: "asesmenAkhir", label: "Asesmen Akhir (Sumatif)" },
  { key: "rubrikPenilaian", label: "Rubrik Penilaian" },
];

export function emptyRppFields() {
  const f = {};
  [...RPP_IDENTITAS, ...RPP_SECTIONS].forEach((x) => (f[x.key] = ""));
  return f;
}
