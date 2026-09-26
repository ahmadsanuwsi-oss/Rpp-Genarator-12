import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { apiErr } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft, UserPlus, Loader2, Trash2, ShieldCheck, GraduationCap, FileText, Mail,
} from "lucide-react";
import { toast } from "sonner";

export default function UserManagement() {
  const { user } = useAuth();
  const isSuper = user?.role === "superadmin";
  const roleLabel = isSuper ? "Admin" : "Guru";

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/admin/users");
      setUsers(data);
    } catch {
      toast.error("Gagal memuat pengguna");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const create = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/admin/users", form);
      toast.success(`Akun ${roleLabel} berhasil dibuat`);
      setForm({ name: "", email: "", password: "" });
      load();
    } catch (err) {
      toast.error(apiErr(err.response?.data?.detail) || "Gagal membuat akun");
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm(`Hapus akun ${roleLabel} ini?`)) return;
    try {
      await api.delete(`/admin/users/${id}`);
      toast.success("Akun dihapus");
      load();
    } catch (err) {
      toast.error(apiErr(err.response?.data?.detail) || "Gagal menghapus");
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-emerald-800 mb-4">
        <ArrowLeft className="w-4 h-4" /> Kembali ke Dashboard
      </Link>
      <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
        {isSuper ? <ShieldCheck className="w-6 h-6 text-emerald-800" /> : <GraduationCap className="w-6 h-6 text-emerald-800" />}
        Kelola {roleLabel}
      </h1>
      <p className="text-slate-500 mt-1 mb-6">
        {isSuper ? "Buat & kelola akun Admin sekolah." : "Buat & kelola akun Guru. Dokumen mereka otomatis muncul di dashboard Anda."}
      </p>

      <div className="grid md:grid-cols-5 gap-6">
        <form onSubmit={create} className="md:col-span-2 bg-white rounded-xl border border-slate-200 p-5 h-fit" data-testid="create-user-form">
          <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2"><UserPlus className="w-4 h-4 text-emerald-800" /> Tambah {roleLabel}</h3>
          <label className="block text-xs font-semibold uppercase tracking-wider text-emerald-800 mb-1">Nama</label>
          <input data-testid="cu-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required
            className="w-full mb-3 px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-700 outline-none text-sm" />
          <label className="block text-xs font-semibold uppercase tracking-wider text-emerald-800 mb-1">Email</label>
          <input data-testid="cu-email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required
            className="w-full mb-3 px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-700 outline-none text-sm" />
          <label className="block text-xs font-semibold uppercase tracking-wider text-emerald-800 mb-1">Kata Sandi</label>
          <input data-testid="cu-password" type="text" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={6}
            className="w-full mb-4 px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-700 outline-none text-sm" />
          <button data-testid="btn-create-user" type="submit" disabled={saving}
            className="w-full flex items-center justify-center gap-2 bg-emerald-800 hover:bg-emerald-900 text-white font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-60">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />} Buat Akun
          </button>
        </form>

        <div className="md:col-span-3">
          <h3 className="font-bold text-slate-900 mb-3">Daftar {roleLabel} ({users.length})</h3>
          {loading ? (
            <div className="py-10 text-center text-slate-400"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
          ) : users.length === 0 ? (
            <div className="py-10 text-center text-slate-400 bg-white rounded-xl border border-dashed border-slate-300">Belum ada akun {roleLabel}.</div>
          ) : (
            <div className="space-y-2" data-testid="users-list">
              {users.map((u) => (
                <div key={u.id} data-testid={`user-item-${u.id}`} className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-700 flex items-center justify-center text-white font-bold shrink-0">
                    {(u.name || "?").charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold text-slate-800 truncate">{u.name}</div>
                    <div className="text-xs text-slate-400 flex items-center gap-1"><Mail className="w-3 h-3" />{u.email}</div>
                  </div>
                  {!isSuper && (
                    <div className="text-xs text-slate-500 flex items-center gap-1 shrink-0">
                      <FileText className="w-3.5 h-3.5" /> {u.doc_count} dok
                    </div>
                  )}
                  <button data-testid={`btn-del-user-${u.id}`} onClick={() => remove(u.id)} className="p-2 rounded-lg text-slate-400 hover:bg-red-50 hover:text-red-600">
                    <Trash2 className="w-[18px] h-[18px]" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
