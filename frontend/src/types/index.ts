export interface Photo {
  id: number;
  file_path: string;
  file_name: string;
  file_size: number | null;
  width: number | null;
  height: number | null;
  shot_at: string | null;
  camera_make: string | null;
  camera_model: string | null;
  lens_model: string | null;
  focal_length: string | null;
  aperture: string | null;
  shutter_speed: string | null;
  iso: number | null;
  gps_lat: number | null;
  gps_lon: number | null;
  ai_theme: string | null;
  ai_subjects: string | null;
  ai_description: string | null;
  ai_tags: string | null;
  ai_analyzed_at: string | null;
  cloud_synced: boolean;
  cloud_url: string | null;
  thumbnail_path: string | null;
  imported_at: string;
}

export interface Stats {
  total: number;
  analyzed: number;
  synced: number;
  themes: Record<string, number>;
  cameras: Record<string, number>;
}

export interface ScanResult {
  added: number;
  skipped: number;
}

export interface FilterState {
  theme: string;
  search: string;
  dateFrom: string;
  dateTo: string;
}
