import { Save, Eye, EyeOff, ExternalLink, RefreshCw, CheckCircle, Circle } from "lucide-react";
import { useEffect, useState } from "react";
import {
  exchangeBaiduCode,
  fetchSettings,
  getBaiduAuthUrl,
  updateSettings,
} from "../api/photos";

type Tab = "ai" | "cloud" | "system";

const AI_PROVIDERS = [
  {
    id: "claude",
    label: "Claude (Anthropic)",
    badge: "视觉",
    desc: "最强图像理解，支持直接分析照片内容",
    fields: [
      { key: "anthropic_api_key", label: "API Key", placeholder: "sk-ant-…", secret: true },
      { key: "anthropic_model", label: "模型", placeholder: "claude-sonnet-4-6" },
    ],
  },
  {
    id: "openai",
    label: "OpenAI (GPT-4o)",
    badge: "视觉",
    desc: "支持图像分析，可使用 GPT-4o / gpt-4-vision-preview",
    fields: [
      { key: "openai_api_key", label: "API Key", placeholder: "sk-…", secret: true },
      { key: "openai_model", label: "模型", placeholder: "gpt-4o" },
    ],
  },
  {
    id: "deepseek",
    label: "DeepSeek",
    badge: "元数据",
    desc: "基于 EXIF 元数据推理主题（DeepSeek 暂无视觉 API）",
    fields: [
      { key: "deepseek_api_key", label: "API Key", placeholder: "sk-…", secret: true },
      { key: "deepseek_model", label: "模型", placeholder: "deepseek-chat" },
    ],
  },
];

const CLOUD_PROVIDERS = [
  {
    id: "s3",
    label: "AWS S3",
    fields: [
      { key: "s3_access_key", label: "Access Key ID", placeholder: "AKIA…" },
      { key: "s3_secret_key", label: "Secret Access Key", placeholder: "…", secret: true },
      { key: "s3_bucket", label: "Bucket 名称", placeholder: "my-photos" },
      { key: "s3_region", label: "Region", placeholder: "us-east-1" },
    ],
  },
  {
    id: "oss",
    label: "阿里云 OSS",
    fields: [
      { key: "oss_access_key_id", label: "AccessKey ID", placeholder: "LTAI…" },
      { key: "oss_access_key_secret", label: "AccessKey Secret", placeholder: "…", secret: true },
      { key: "oss_bucket", label: "Bucket 名称", placeholder: "my-photos" },
      { key: "oss_endpoint", label: "Endpoint", placeholder: "oss-cn-hangzhou.aliyuncs.com" },
    ],
  },
  {
    id: "cos",
    label: "腾讯云 COS",
    fields: [
      { key: "cos_secret_id", label: "SecretId", placeholder: "AKIDxx…" },
      { key: "cos_secret_key", label: "SecretKey", placeholder: "…", secret: true },
      { key: "cos_bucket", label: "Bucket（含 AppID）", placeholder: "my-photos-1250000000" },
      { key: "cos_region", label: "Region", placeholder: "ap-beijing" },
    ],
  },
  {
    id: "qiniu",
    label: "七牛云 Kodo",
    fields: [
      { key: "qiniu_access_key", label: "AccessKey", placeholder: "…" },
      { key: "qiniu_secret_key", label: "SecretKey", placeholder: "…", secret: true },
      { key: "qiniu_bucket", label: "Bucket 名称", placeholder: "my-photos" },
      { key: "qiniu_domain", label: "CDN 域名", placeholder: "https://cdn.example.com" },
    ],
  },
  {
    id: "baidu",
    label: "百度网盘",
    isBaidu: true,
    fields: [
      { key: "baidu_app_key", label: "App Key", placeholder: "百度开放平台 App Key" },
      { key: "baidu_secret_key", label: "Secret Key", placeholder: "…", secret: true },
      { key: "baidu_save_dir", label: "保存目录", placeholder: "/PhotoLib" },
    ],
  },
];

export function Settings() {
  const [tab, setTab] = useState<Tab>("ai");
  const [values, setValues] = useState<Record<string, string>>({});
  const [visible, setVisible] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [baiduCode, setBaiduCode] = useState("");
  const [baiduLoading, setBaiduLoading] = useState(false);
  const [baiduMsg, setBaiduMsg] = useState("");

  useEffect(() => {
    fetchSettings().then(setValues);
  }, []);

  const set = (key: string, val: string) => setValues((v) => ({ ...v, [key]: val }));

  async function handleSave() {
    setSaving(true);
    try {
      const updates: Record<string, string> = {};
      for (const [k, v] of Object.entries(values)) {
        if (v && !v.startsWith("••")) updates[k] = v;
      }
      await updateSettings(updates);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e: any) {
      alert("保存失败：" + e.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleBaiduAuth() {
    try {
      const url = await getBaiduAuthUrl();
      window.open(url, "_blank");
    } catch (e: any) {
      alert(e.response?.data?.detail || e.message);
    }
  }

  async function handleBaiduExchange() {
    if (!baiduCode.trim()) return;
    setBaiduLoading(true);
    setBaiduMsg("");
    try {
      await exchangeBaiduCode(baiduCode.trim());
      setBaiduMsg("授权成功 ✓");
      setBaiduCode("");
    } catch (e: any) {
      setBaiduMsg("授权失败：" + (e.response?.data?.detail || e.message));
    } finally {
      setBaiduLoading(false);
    }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "ai", label: "AI 模型" },
    { id: "cloud", label: "云存储" },
    { id: "system", label: "系统" },
  ];

  const inputClass =
    "w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-accent";

  const renderField = (f: { key: string; label: string; placeholder: string; secret?: boolean }) => (
    <div key={f.key}>
      <label className="block text-xs text-gray-400 mb-1">{f.label}</label>
      <div className="relative">
        <input
          type={f.secret && !visible[f.key] ? "password" : "text"}
          value={values[f.key] ?? ""}
          onChange={(e) => set(f.key, e.target.value)}
          placeholder={f.placeholder}
          className={inputClass + (f.secret ? " pr-8" : "")}
        />
        {f.secret && (
          <button
            type="button"
            onClick={() => setVisible((v) => ({ ...v, [f.key]: !v[f.key] }))}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
          >
            {visible[f.key] ? <EyeOff size={13} /> : <Eye size={13} />}
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Tab bar */}
      <div className="flex-shrink-0 px-8 pt-8 border-b border-white/10">
        <div className="flex gap-1 mb-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 text-sm rounded-t-lg transition-colors ${
                tab === t.id
                  ? "bg-white/10 text-white border-b-2 border-accent"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        {/* ── AI Tab ── */}
        {tab === "ai" && (
          <div className="max-w-xl space-y-5">
            <div>
              <p className="text-gray-400 text-sm mb-3">当前使用的 AI 提供商</p>
              <div className="grid grid-cols-3 gap-2">
                {AI_PROVIDERS.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => set("ai_provider", p.id)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-all ${
                      values["ai_provider"] === p.id
                        ? "border-accent bg-accent/10 text-white"
                        : "border-white/10 text-gray-400 hover:border-white/30"
                    }`}
                  >
                    {values["ai_provider"] === p.id ? (
                      <CheckCircle size={13} className="text-accent" />
                    ) : (
                      <Circle size={13} />
                    )}
                    {p.label.split(" ")[0]}
                  </button>
                ))}
              </div>
            </div>

            {AI_PROVIDERS.map((provider) => (
              <div
                key={provider.id}
                className={`border rounded-xl p-4 space-y-3 transition-all ${
                  values["ai_provider"] === provider.id
                    ? "border-accent/50 bg-accent/5"
                    : "border-white/10 opacity-60"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-white text-sm font-medium">{provider.label}</span>
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded-full ${
                      provider.badge === "视觉"
                        ? "bg-purple-500/20 text-purple-300"
                        : "bg-yellow-500/20 text-yellow-300"
                    }`}
                  >
                    {provider.badge}
                  </span>
                </div>
                <p className="text-gray-500 text-xs">{provider.desc}</p>
                {provider.fields.map(renderField)}
              </div>
            ))}
          </div>
        )}

        {/* ── Cloud Tab ── */}
        {tab === "cloud" && (
          <div className="max-w-xl space-y-5">
            <div>
              <p className="text-gray-400 text-sm mb-3">云存储提供商</p>
              <div className="grid grid-cols-3 gap-2 flex-wrap">
                {CLOUD_PROVIDERS.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => set("cloud_provider", p.id)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-all ${
                      values["cloud_provider"] === p.id
                        ? "border-accent bg-accent/10 text-white"
                        : "border-white/10 text-gray-400 hover:border-white/30"
                    }`}
                  >
                    {values["cloud_provider"] === p.id ? (
                      <CheckCircle size={13} className="text-accent" />
                    ) : (
                      <Circle size={13} />
                    )}
                    {p.label}
                  </button>
                ))}
              </div>
              <p className="text-gray-600 text-xs mt-2">
                注：夸克云盘暂无公开第三方开发者 API，无法支持程序化上传。
              </p>
            </div>

            {CLOUD_PROVIDERS.map((provider) => (
              <div
                key={provider.id}
                className={`border rounded-xl p-4 space-y-3 transition-all ${
                  values["cloud_provider"] === provider.id
                    ? "border-accent/50 bg-accent/5"
                    : "border-white/10 opacity-50"
                }`}
              >
                <span className="text-white text-sm font-medium">{provider.label}</span>
                {provider.fields.map(renderField)}

                {/* Baidu OAuth flow */}
                {provider.isBaidu && values["cloud_provider"] === "baidu" && (
                  <div className="border-t border-white/10 pt-3 space-y-2">
                    <p className="text-gray-400 text-xs">
                      填写 App Key 和 Secret Key 后，点击授权按钮完成登录
                    </p>
                    <div className="flex gap-2">
                      <button
                        onClick={handleBaiduAuth}
                        className="btn-secondary flex items-center gap-1.5 text-xs"
                      >
                        <ExternalLink size={12} />
                        打开授权页面
                      </button>
                    </div>
                    <div className="flex gap-2">
                      <input
                        value={baiduCode}
                        onChange={(e) => setBaiduCode(e.target.value)}
                        placeholder="粘贴授权页面返回的 code"
                        className={inputClass + " flex-1"}
                      />
                      <button
                        onClick={handleBaiduExchange}
                        disabled={baiduLoading || !baiduCode}
                        className="btn-primary text-xs flex items-center gap-1 disabled:opacity-40"
                      >
                        {baiduLoading ? <RefreshCw size={12} className="animate-spin" /> : null}
                        确认授权
                      </button>
                    </div>
                    {baiduMsg && (
                      <p className={`text-xs ${baiduMsg.includes("成功") ? "text-green-400" : "text-red-400"}`}>
                        {baiduMsg}
                      </p>
                    )}
                    {values["baidu_access_token"] && (
                      <p className="text-green-400 text-xs flex items-center gap-1">
                        <CheckCircle size={11} /> 已授权
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* ── System Tab ── */}
        {tab === "system" && (
          <div className="max-w-sm space-y-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">缩略图尺寸（px）</label>
              <input
                type="number"
                value={values["thumbnail_size"] ?? 400}
                onChange={(e) => set("thumbnail_size", e.target.value)}
                className={inputClass + " w-32"}
              />
              <p className="text-gray-600 text-xs mt-1">越大越清晰，占用更多磁盘空间。默认 400</p>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">缩略图存储目录</label>
              <input
                value={values["thumbnail_dir"] ?? ""}
                onChange={(e) => set("thumbnail_dir", e.target.value)}
                className={inputClass}
                placeholder="留空使用默认路径"
              />
            </div>
          </div>
        )}

        {/* Save button */}
        <div className="mt-8">
          <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
            <Save size={14} />
            {saved ? "已保存 ✓" : saving ? "保存中…" : "保存设置"}
          </button>
        </div>
      </div>
    </div>
  );
}
