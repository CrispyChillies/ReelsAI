import axiosInstance from '@/lib/axios';

export type RankingStyle = 'balanced' | 'focused' | 'fresh' | 'trending';
export type Platform = 'bluesky' | 'tiktok';

export interface CreateFeedRequest {
  title: string;
  user_intent: string;
  ranking_style: RankingStyle;
  platform?: Platform;
}

export interface PersonalFeed {
  id: number;
  title: string;
  user_intent: string;
  search_queries: string[];
  include_criteria: string;
  exclude_criteria: string;
  platform: Platform;
  ranking_style: RankingStyle;
  items_count: number;
  created_at: string;
}

export interface SocialPost {
  id: number;
  platform_id: string;
  platform: Platform;
  author: string;
  content: string;
  media_url: string | null;
  thumbnail_url: string | null;
  source_link: string | null;
  embed_quote: string | null;
  like_count: number;
  repost_count: number;
  fetched_at: string;
}

export interface FeedItem {
  id: number;
  post: SocialPost;
  ai_score: number;
  ai_reasoning: string;
  ai_summary: string | null;
  created_at: string;
}

export interface RefreshResponse {
  task_id?: string;
  message: string;
}

export interface SaveItemRequest {
  social_post_id: number;
  tags?: string[];
  notes?: string;
}

export interface SaveItemResponse {
  status: string;
  message: string;
  saved_id: number;
}

export const newsfeedService = {
  // Create a new feed configuration
  async createFeed(data: CreateFeedRequest): Promise<PersonalFeed> {
    const response = await axiosInstance.post<PersonalFeed>('/posts/', {
      ...data,
      platform: data.platform || 'bluesky',
    });
    return response.data;
  },

  // Trigger crawl/refresh for a feed
  async refreshFeed(feedId: number): Promise<RefreshResponse> {
    const response = await axiosInstance.post<RefreshResponse>(`/posts/${feedId}/refresh/`);
    return response.data;
  },

  // Get feed items (posts)
  async getFeedItems(feedId: number): Promise<FeedItem[]> {
    const response = await axiosInstance.get<FeedItem[]>(`/posts/${feedId}/items/`);
    return response.data;
  },

  // Get all feeds
  async getFeeds(): Promise<PersonalFeed[]> {
    const response = await axiosInstance.get<PersonalFeed[]>('/posts/');
    return response.data;
  },

  // Get single feed
  async getFeed(feedId: number): Promise<PersonalFeed> {
    const response = await axiosInstance.get<PersonalFeed>(`/posts/${feedId}/`);
    return response.data;
  },

  // Delete feed
  async deleteFeed(feedId: number): Promise<void> {
    await axiosInstance.delete(`/posts/${feedId}/`);
  },

  // Save a post to knowledge graph
  async savePost(data: SaveItemRequest): Promise<SaveItemResponse> {
    const response = await axiosInstance.post<SaveItemResponse>('/save/', data);
    return response.data;
  },
  async createVideoFeed(data: CreateFeedRequest): Promise<PersonalFeed> {
    const response = await axiosInstance.post<PersonalFeed>('/videos/', {
      ...data,
      platform: 'tiktok',
    });
    return response.data;
  },

  // Trigger crawl/refresh for a video feed
  async refreshVideoFeed(feedId: number): Promise<RefreshResponse> {
    const response = await axiosInstance.post<RefreshResponse>(`/videos/${feedId}/refresh/`);
    return response.data;
  },

  // Get video feed items
  async getVideoFeedItems(feedId: number): Promise<FeedItem[]> {
    const response = await axiosInstance.get<FeedItem[]>(`/videos/${feedId}/items/`);
    return response.data;
  },

  // Get all video feeds
  async getVideoFeeds(): Promise<PersonalFeed[]> {
    const response = await axiosInstance.get<PersonalFeed[]>('/videos/');
    return response.data;
  },

  // Get single video feed
  async getVideoFeed(feedId: number): Promise<PersonalFeed> {
    const response = await axiosInstance.get<PersonalFeed>(`/videos/${feedId}/`);
    return response.data;
  },

  // Delete video feed
  async deleteVideoFeed(feedId: number): Promise<void> {
    await axiosInstance.delete(`/videos/${feedId}/`);
  },
};


