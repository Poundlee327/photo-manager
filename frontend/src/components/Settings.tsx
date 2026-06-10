import { Save, Eye, EyeOff } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchSettings, updateSettings } from "../api/photos";

interface FieldDef {
  key: string;
  label: string;
  placeholder: string;
  secret?: boolean;
}

const FIELDS: FieldDef[] = [
  { key: "anthropic_api_key", label: "Anthropic API Key", placeholder: "sk-ant-…", secret: true },
  { key: "aws_access_key", label: "AWS Access Key ID", placeholder: "AKIA…" },
  { key: "aws_secret_key", label: "AWS Secret Access Key", placeholder: "…", secret: true },
  { key: "aws_bucket", label: "S3 Bucket 名称", placeholder: "my-photo-bucket" },
  { key: "aws_region", label: "S3 Region", placeholder: "us-east-1" },
];

export function Settings() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [visible, setVisible] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchSettings().then(setValues);
  }, []);

  async function handleSave() {
    setSaving(true);
    try {
      // Only send non-masked values
      const updates: Record<string, string> = {};
      for (const [k, v] of Object.entries(values)) {
        if (v && !v.startsWith("••")) updates[k] = v;
      }
      await updateSettings(updates);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e: any) {
      alert("保存失败：" + e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="p-8 max-w-xl">
      <h2 className="text-white font-semibold text-xl mb-6">设置</h2>

      <div className="space-y-5">
        {FIELDS.map(({ key, label, placeholder, secret }) => (
          <div key={key}>
            <label className="block text-sm text-gray-400 mb-1.5">{label}</label>
            <div className="relative">
              <input
                type={secret && !visible[key] ? "password" : "text"}
                value={values[key] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [key]: e.target.value }))}
                placeholder={placeholder}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-accent pr-10"
              />
              {secret && (
                <button
                  type="button"
                  onClick={() => setVisible((v) => ({ ...v, [key]: !v[key] }))}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {visible[key] ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              )}
            </div>
          </div>
        ))}

        <div>
          <label className="block text-sm text-gray-400 mb-1.5">缩略图尺寸 (px)</label>
          <input
            type="number"
            value={values["thumbnail_size"] ?? 400}
            onChange={(e) => setValues((v) => ({ ...v, thumbnail_size: e.target.value }))}
            className="w-32 bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
          />
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary flex items-center gap-2 mt-2"
        >
          <Save size={15} />
          {saved ? "已保存 ✓" : saving ? "保存中…" : "保存设置"}
        </button>
      </div>
    </div>
  );
}
