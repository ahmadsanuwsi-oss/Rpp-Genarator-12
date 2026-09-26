from dotenv import load_dotenv
from pathlib import Path
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import logging
import uuid
import json
import re
import tempfile
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta

from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType

# ---------------- DB ----------------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.1-pro-preview')

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------- Auth helpers ----------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


def create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Tidak terautentikasi")
    token = auth[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User tidak ditemukan")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesi berakhir, silakan login kembali")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token tidak valid")


# ---------------- Models ----------------
class RegisterInput(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class ProfileInput(BaseModel):
    name: Optional[str] = None
    nip: Optional[str] = None
    jabatan: Optional[str] = None
    namaSekolah: Optional[str] = None
    namaKepalaSekolah: Optional[str] = None
    nipKepalaSekolah: Optional[str] = None


class DocumentInput(BaseModel):
    type: str
    title: str
    meta: Dict[str, Any] = Field(default_factory=dict)
    fields: Dict[str, Any] = Field(default_factory=dict)
    content_html: Optional[str] = None


class GenerateInput(BaseModel):
    type: str
    inputs: Dict[str, Any] = Field(default_factory=dict)


def public_user(u: dict) -> dict:
    u.pop("password_hash", None)
    u.pop("_id", None)
    return u


# ---------------- Auth routes ----------------
@api_router.post("/auth/register")
async def register(data: RegisterInput):
    email = data.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    user = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "email": email,
        "password_hash": hash_password(data.password),
        "role": "guru",
        "nip": "",
        "jabatan": "Guru",
        "namaSekolah": "",
        "namaKepalaSekolah": "",
        "nipKepalaSekolah": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user)
    token = create_token(user["id"], email)
    return {"token": token, "user": public_user(dict(user))}


@api_router.post("/auth/login")
async def login(data: LoginInput):
    email = data.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email atau kata sandi salah")
    token = create_token(user["id"], email)
    return {"token": token, "user": public_user(dict(user))}


@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@api_router.put("/auth/profile")
async def update_profile(data: ProfileInput, user: dict = Depends(get_current_user)):
    update = {k: v for k, v in data.model_dump().items() if v is not None}
    if update:
        await db.users.update_one({"id": user["id"]}, {"$set": update})
    fresh = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    return fresh


# ---------------- Document routes ----------------
@api_router.get("/documents/stats")
async def stats(user: dict = Depends(get_current_user)):
    pipeline = [
        {"$match": {"owner_id": user["id"]}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
    ]
    rows = await db.documents.aggregate(pipeline).to_list(100)
    counts = {r["_id"]: r["count"] for r in rows}
    total = sum(counts.values())
    return {"total": total, "by_type": counts}


@api_router.get("/documents")
async def list_documents(type: Optional[str] = None, user: dict = Depends(get_current_user)):
    q = {"owner_id": user["id"]}
    if type:
        q["type"] = type
    docs = await db.documents.find(q, {"_id": 0, "content_html": 0}).sort("updated_at", -1).to_list(500)
    return docs


@api_router.get("/documents/{doc_id}")
async def get_document(doc_id: str, user: dict = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id, "owner_id": user["id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    return doc


@api_router.post("/documents")
async def create_document(data: DocumentInput, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "owner_id": user["id"],
        "type": data.type,
        "title": data.title,
        "meta": data.meta,
        "fields": data.fields,
        "content_html": data.content_html,
        "created_at": now,
        "updated_at": now,
    }
    await db.documents.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.put("/documents/{doc_id}")
async def update_document(doc_id: str, data: DocumentInput, user: dict = Depends(get_current_user)):
    existing = await db.documents.find_one({"id": doc_id, "owner_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    update = {
        "title": data.title,
        "meta": data.meta,
        "fields": data.fields,
        "content_html": data.content_html,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.documents.update_one({"id": doc_id}, {"$set": update})
    fresh = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    return fresh


@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    res = await db.documents.delete_one({"id": doc_id, "owner_id": user["id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    return {"success": True}


# ---------------- AI helpers ----------------
RPP_FIELDS = [
    "namaGuru", "nip", "jabatan", "namaSekolah", "mataPelajaran", "kelas",
    "semester", "fase", "materiPokok", "alokasiWaktu", "tahunAjaran",
    "namaKepalaSekolah", "nipKepalaSekolah",
    "identifikasiPesertaDidik", "capaianPembelajaran", "dimensiProfilLulusan",
    "topikPancaCinta", "materiIntegrasiKBC", "pemanfaatanDigital",
    "lintasDisiplin", "tujuanPembelajaran", "praktikPedagogik", "kemitraan",
    "kegiatanAwal", "kegiatanInti", "penutup",
    "asesmenAwal", "asesmenProses", "asesmenAkhir", "rubrikPenilaian",
]


def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return m.group(0) if m else text


def _clean_html(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(html)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def new_chat(system_message: str) -> LlmChat:
    return LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=str(uuid.uuid4()),
        system_message=system_message,
    ).with_model("gemini", GEMINI_MODEL)


@api_router.post("/ai/extract-rpp")
async def extract_rpp(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key belum dikonfigurasi")
    filename = (file.filename or "upload").lower()
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    mime_map = {
        "pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg",
        "jpeg": "image/jpeg", "webp": "image/webp", "heic": "image/heic",
    }
    if ext not in mime_map:
        raise HTTPException(status_code=400, detail="Format tidak didukung. Gunakan PDF atau gambar (PNG/JPG).")
    data = await file.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    tmp.write(data)
    tmp.close()

    system = (
        "Anda asisten ahli kurikulum pendidikan Indonesia (Kurikulum Merdeka & Kurikulum Berbasis Cinta). "
        "Anda membaca dokumen RPP/Modul Ajar yang diunggah lalu mengekstrak isinya menjadi JSON terstruktur."
    )
    keys_desc = ", ".join(RPP_FIELDS)
    prompt = (
        "Baca dokumen terlampir (RPP/Modul Ajar). Ekstrak dan susun kembali isinya menjadi JSON. "
        f"Gunakan PERSIS kunci berikut (semua string, kosongkan '' jika tidak ada): {keys_desc}. "
        "Untuk bagian naratif (identifikasi, kegiatan, asesmen, dll) tuliskan isi lengkap yang rapi. "
        "Jika dokumen berupa format/kerangka kosong, isi dengan konten pembelajaran yang relevan dan lengkap "
        "sesuai mata pelajaran/materi yang terdeteksi. "
        "Balas HANYA dengan objek JSON valid tanpa penjelasan, tanpa ```."
    )
    file_content = FileContentWithMimeType(file_path=tmp.name, mime_type=mime_map[ext])
    try:
        resp = await new_chat(system).send_message(
            UserMessage(text=prompt, file_contents=[file_content])
        )
    except Exception as e:
        logger.exception("extract-rpp failed")
        raise HTTPException(status_code=500, detail=f"Gagal membaca file: {e}")
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

    try:
        parsed = json.loads(_clean_json(resp))
    except Exception:
        raise HTTPException(status_code=500, detail="AI tidak mengembalikan data yang valid, coba lagi.")
    fields = {k: str(parsed.get(k, "") or "") for k in RPP_FIELDS}
    # prefill identitas guru dari profil jika kosong
    fields["namaGuru"] = fields["namaGuru"] or user.get("name", "")
    fields["nip"] = fields["nip"] or user.get("nip", "")
    fields["namaSekolah"] = fields["namaSekolah"] or user.get("namaSekolah", "")
    fields["namaKepalaSekolah"] = fields["namaKepalaSekolah"] or user.get("namaKepalaSekolah", "")
    fields["nipKepalaSekolah"] = fields["nipKepalaSekolah"] or user.get("nipKepalaSekolah", "")
    return {"fields": fields}


GEN_INSTRUCTIONS = {
    "prota": "Buat PROGRAM TAHUNAN (PROTA). Sajikan tabel berisi: No, Semester, Materi/Lingkup Materi & Capaian Pembelajaran, Alokasi Waktu (JP), Keterangan. Bagi untuk semester Ganjil dan Genap dalam satu tahun ajaran.",
    "prosem": "Buat PROGRAM SEMESTER (PROSEM). Sajikan tabel: No, Tujuan Pembelajaran/Materi, Alokasi Waktu (JP), lalu kolom bulan (Juli–Desember untuk ganjil / Januari–Juni untuk genap) yang dibagi per minggu (1-4) dengan tanda jumlah JP tiap minggu.",
    "kktp": "Buat KRITERIA KETERCAPAIAN TUJUAN PEMBELAJARAN (KKTP). Sajikan tabel: No, Tujuan Pembelajaran, Kriteria Ketercapaian, dan Interval Nilai/Deskripsi (Perlu Bimbingan, Cukup, Baik, Sangat Baik).",
    "alokasi_waktu": "Buat ANALISIS ALOKASI WAKTU. Sajikan tabel perhitungan pekan efektif per bulan dalam satu semester, jumlah pekan tidak efektif, pekan efektif, dan distribusi Jam Pelajaran (JP) untuk tiap materi/Tujuan Pembelajaran.",
    "atp": "Buat ALUR TUJUAN PEMBELAJARAN (ATP). Uraikan dari Capaian Pembelajaran menjadi urutan Tujuan Pembelajaran yang runtut. Sajikan tabel: No, Elemen/CP, Tujuan Pembelajaran, Materi, Alokasi Waktu, Profil Pelajar Pancasila.",
    "asesmen": "Buat INSTRUMEN ASESMEN lengkap: kisi-kisi, 10 soal pilihan ganda (dengan opsi & kunci jawaban), 5 soal essay (dengan kunci/rubrik), serta rubrik penilaian (Sangat Baik/Baik/Cukup/Perlu Bimbingan). Gunakan tabel untuk kisi-kisi dan rubrik.",
    "lkpd": "Buat LEMBAR KERJA PESERTA DIDIK (LKPD). Sertakan: Judul, Identitas (Nama/Kelas), Tujuan Pembelajaran, Petunjuk Pengerjaan, Ringkasan materi singkat, Kegiatan/Langkah kerja, dan soal/pertanyaan latihan untuk siswa. Sediakan garis/kolom isian jawaban.",
    "poster": "Buat KONTEN POSTER MEDIA PEMBELAJARAN yang menarik dan siap cetak A4. Sertakan judul besar, sub-judul, poin-poin kunci materi yang ringkas dan mudah diingat, ajakan/pesan motivasi, serta deskripsi ilustrasi yang disarankan. Gunakan gaya visual (heading besar, daftar berpoin, penekanan).",
}

GEN_LABELS = {
    "prota": "Program Tahunan", "prosem": "Program Semester", "kktp": "KKTP",
    "alokasi_waktu": "Alokasi Waktu", "atp": "ATP", "asesmen": "Asesmen",
    "lkpd": "LKPD", "poster": "Poster",
}


@api_router.post("/ai/generate")
async def generate_document(data: GenerateInput, user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key belum dikonfigurasi")
    if data.type not in GEN_INSTRUCTIONS:
        raise HTTPException(status_code=400, detail="Jenis dokumen tidak dikenal")

    inp = data.inputs
    ctx_lines = []
    label_map = {
        "mataPelajaran": "Mata Pelajaran", "kelas": "Kelas", "fase": "Fase",
        "semester": "Semester", "tahunAjaran": "Tahun Ajaran",
        "capaianPembelajaran": "Capaian Pembelajaran (CP)",
        "alurTujuanPembelajaran": "Alur Tujuan Pembelajaran (ATP)",
        "materi": "Materi / Lingkup Materi", "alokasiWaktu": "Alokasi Waktu",
        "jumlahMinggu": "Jumlah Minggu Efektif", "catatan": "Catatan Tambahan",
    }
    for k, lbl in label_map.items():
        v = str(inp.get(k, "") or "").strip()
        if v:
            ctx_lines.append(f"- {lbl}: {v}")
    context = "\n".join(ctx_lines) if ctx_lines else "(tidak ada detail tambahan)"

    system = (
        "Anda asisten ahli kurikulum pendidikan Indonesia (Kurikulum Merdeka & Kurikulum Berbasis Cinta) "
        "yang membantu guru menyusun dokumen administrasi pembelajaran. Tulis dalam Bahasa Indonesia yang baku dan lengkap."
    )
    prompt = (
        f"{GEN_INSTRUCTIONS[data.type]}\n\n"
        f"Data acuan dari guru:\n{context}\n\n"
        "Ketentuan output:\n"
        "- Balas HANYA potongan HTML (bukan markdown), TANPA ```html, TANPA tag <html>/<head>/<body>.\n"
        "- Gunakan <h2>, <h3>, <p>, <ul>, <ol>, dan <table> bila perlu.\n"
        "- Untuk tabel gunakan <table><thead><tr><th>...</th></tr></thead><tbody>...</tbody></table> yang rapi.\n"
        "- Konten harus konkret, lengkap, dan langsung bisa dipakai guru.\n"
    )
    try:
        resp = await new_chat(system).send_message(UserMessage(text=prompt))
    except Exception as e:
        logger.exception("generate failed")
        raise HTTPException(status_code=500, detail=f"Gagal membuat dokumen: {e}")

    html = _clean_html(resp)
    return {"content_html": html}


# ---------------- App wiring ----------------
@api_router.get("/")
async def root():
    return {"message": "RPP Studio API"}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id")
    await db.documents.create_index("owner_id")
    # seed demo guru
    demo_email = "guru@demo.com"
    if not await db.users.find_one({"email": demo_email}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "name": "Ibu Eka Novita Sari",
            "email": demo_email,
            "password_hash": hash_password("guru123"),
            "role": "guru",
            "nip": "199001012020122001",
            "jabatan": "Guru Kelas",
            "namaSekolah": "MI Miftahul Jannah",
            "namaKepalaSekolah": "H. Zainur Ridho, S.Pd.I",
            "nipKepalaSekolah": "197505052005011003",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
