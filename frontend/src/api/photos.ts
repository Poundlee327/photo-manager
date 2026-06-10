import axios from "axios";
import type { FilterState, Photo, ScanResult, Stats } from "../types";

const api = axios.create({ baseURL: "/api" });

export async function fetchPhotos(filters: FilterState, offset = 0, limit = 100): Promise<Photo[]> {
  const params: Record<string, string> = { offset: String(offset), limit: String(limit) };
  if (filters.theme) params.theme = filters.theme;
  if (filters.search) params.search = filters.search;
  if (filters.dateFrom) params.date_from = filters.dateFrom;
  if (filters.dateTo) params.date_to = filters.dateTo;
  const { data } = await api.get<Photo[]>("/photos", { params });
  return data;
}

export async function fetchPhoto(id: number): Promise<Photo> {
  const { data } = await api.get<Photo>(`/photos/${id}`);
  return data;
}

export async function scanDirectory(directory: string, recursive: boolean): Promise<ScanResult> {
  const { data } = await api.post<ScanResult>("/scan", { directory, recursive });
  return data;
}

export async function analyzePhotos(ids: number[]): Promise<void> {
  await api.post("/analyze", { photo_ids: ids });
}

export async function syncPhotos(ids: number[]): Promise<void> {
  await api.post("/sync", { photo_ids: ids });
}

export async function fetchStats(): Promise<Stats> {
  const { data } = await api.get<Stats>("/stats");
  return data;
}

export async function fetchSettings(): Promise<Record<string, string>> {
  const { data } = await api.get("/settings");
  return data;
}

export async function updateSettings(updates: Record<string, string>): Promise<void> {
  await api.put("/settings", updates);
}

export async function fetchProviders(): Promise<any> {
  const { data } = await api.get("/settings/providers");
  return data;
}

export async function getBaiduAuthUrl(): Promise<string> {
  const { data } = await api.get("/auth/baidu/url");
  return data.url;
}

export async function exchangeBaiduCode(code: string): Promise<void> {
  await api.post("/auth/baidu/exchange", { code });
}

export function thumbnailUrl(id: number): string {
  return `/api/photos/${id}/thumbnail`;
}

export function imageUrl(id: number): string {
  return `/api/photos/${id}/image`;
}
