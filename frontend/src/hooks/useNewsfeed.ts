import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/app/toast';
import { newsfeedService } from '@/services/newsfeedService';
import type { CreateFeedRequest, FeedItem, SaveItemRequest } from '@/services/newsfeedService';

export const useNewsfeed = () => {
  const queryClient = useQueryClient();
  const { notify } = useToast();

  // Create feed mutation
  const createFeedMutation = useMutation({
    mutationFn: (data: CreateFeedRequest) => newsfeedService.createFeed(data),
    onSuccess: (data) => {
      notify({ title: 'Feed created successfully', tone: 'success' });
      // Invalidate feeds list
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
      return data;
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || error.message || 'Failed to create feed';
      notify({ title: 'Failed to create feed', content: message, tone: 'error' });
    },
  });

  // Refresh feed mutation
  const refreshFeedMutation = useMutation({
    mutationFn: (feedId: number) => newsfeedService.refreshFeed(feedId),
    onSuccess: (_data, feedId) => {
      notify({ 
        title: 'Crawl started', 
        content: 'AI is finding posts for you...', 
        tone: 'info' 
      });
      // Invalidate feed items to refetch
      queryClient.invalidateQueries({ queryKey: ['feedItems', feedId] });
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || error.message || 'Failed to refresh feed';
      notify({ title: 'Refresh failed', content: message, tone: 'error' });
    },
  });

  // Refresh video feed mutation
  const refreshVideoFeedMutation = useMutation({
    mutationFn: (feedId: number) => newsfeedService.refreshVideoFeed(feedId),
    onSuccess: (_data, feedId) => {
      notify({ 
        title: 'Video crawl started', 
        content: 'AI is finding videos for you...', 
        tone: 'info' 
      });
      // Invalidate video feed items to refetch
      queryClient.invalidateQueries({ queryKey: ['videoFeedItems', feedId] });
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || error.message || 'Failed to refresh video feed';
      notify({ title: 'Refresh failed', content: message, tone: 'error' });
    },
  });

  return {
    createFeed: createFeedMutation.mutateAsync,
    isCreatingFeed: createFeedMutation.isPending,
    refreshFeed: refreshFeedMutation.mutate,
    isRefreshingFeed: refreshFeedMutation.isPending,
    refreshVideoFeed: refreshVideoFeedMutation.mutate,
    isRefreshingVideoFeed: refreshVideoFeedMutation.isPending,
  };
};

// Hook to save a post
export const useSavePost = () => {
  const { notify } = useToast();

  const savePostMutation = useMutation({
    mutationFn: (data: SaveItemRequest) => newsfeedService.savePost(data),
    onSuccess: (response) => {
      notify({ 
        title: 'Post saved successfully', 
        content: response.message,
        tone: 'success' 
      });
      // You can invalidate saved posts query here if you have one
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || error.message || 'Failed to save post';
      notify({ title: 'Save failed', content: message, tone: 'error' });
    },
  });

  return {
    savePost: savePostMutation.mutateAsync,
    isSaving: savePostMutation.isPending,
  };
};

// Hook to fetch feed items with polling
export const useFeedItems = (feedId: number | null, options?: { 
  enabled?: boolean;
  refetchInterval?: number;
}) => {
  return useQuery<FeedItem[]>({
    queryKey: ['feedItems', feedId],
    queryFn: () => feedId ? newsfeedService.getFeedItems(feedId) : Promise.resolve([]),
    enabled: options?.enabled !== false && feedId !== null,
    refetchInterval: options?.refetchInterval || false, // Default: no polling, user can enable
    staleTime: 30000, // 30 seconds
  });
};

// Hook to fetch video feed items with polling
export const useVideoFeedItems = (feedId: number | null, options?: { 
  enabled?: boolean;
  refetchInterval?: number;
}) => {
  return useQuery<FeedItem[]>({
    queryKey: ['videoFeedItems', feedId],
    queryFn: () => feedId ? newsfeedService.getVideoFeedItems(feedId) : Promise.resolve([]),
    enabled: options?.enabled !== false && feedId !== null,
    refetchInterval: options?.refetchInterval || false,
    staleTime: 30000,
  });
};

// Hook to fetch all feeds
export const useFeeds = () => {
  return useQuery({
    queryKey: ['feeds'],
  queryFn: () => newsfeedService.getFeeds(),
    staleTime: 60000, // 1 minute
  });
};
