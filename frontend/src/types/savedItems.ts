export interface SavedItem {
  id: number;
  post: SocialPost;
  is_favorite: boolean;
  tags: string[];
  user_notes: string | null;
  is_rag_indexed: boolean;
  saved_at: string;
}

export interface SocialPost {
  id: number;
  platform: 'bluesky' | 'tiktok';
  author: string;
  content: string;
  media_url: string | null;
  thumbnail_url: string | null;
  like_count: number;
  repost_count: number;
  reply_count: number;
  source_link: string | null;
  created_at_source: string | null;
  fetched_at: string;
}

export interface SaveItemRequest {
  social_post_id: number;
  tags?: string[];
  notes?: string;
}
