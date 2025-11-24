import { useState, useRef, useEffect, memo } from "react"; // Thêm memo vào import
import styled from "styled-components";
import { useI18n } from "@/app/i18n";
import { useNewsfeed, useFeedItems, useVideoFeedItems, useSavePost } from "@/hooks/useNewsfeed";
import { newsfeedService, type PersonalFeed, type FeedItem } from "@/services/newsfeedService";


// 1. Tạo component Memoized để ngăn React reset DOM
const TikTokContent = memo(({ html }: { html: string }) => {
  return <TikTokEmbed dangerouslySetInnerHTML={{ __html: html }} />;
}, (prev, next) => prev.html === next.html);

export default function NewsfeedPage() {
  useI18n();
  
  // State for Content Type
  const [contentType, setContentType] = useState<'posts' | 'reels'>(() => {
    try {
      return (sessionStorage.getItem('newsfeed_contentType') as 'posts' | 'reels') || 'posts';
    } catch {
      return 'posts';
    }
  });

  // Separate state for prompts
  const [prompts, setPrompts] = useState({
    posts: "",
    reels: ""
  });

  // Separate state for active filters (display text)
  const [filters, setFilters] = useState({
    posts: (() => {
      try { return sessionStorage.getItem('newsfeed_activeFilter') || ''; } catch { return ''; }
    })(),
    reels: (() => {
      try { return sessionStorage.getItem('newsfeed_reelsFilter') || ''; } catch { return ''; }
    })()
  });

  // Separate state for feed IDs
  const [feedIds, setFeedIds] = useState<{posts: number | null, reels: number | null}>(() => {
    try {
      const storedPosts = sessionStorage.getItem('newsfeed_currentFeedId');
      const storedReels = sessionStorage.getItem('newsfeed_reelsFeedId');
      return {
        posts: storedPosts ? parseInt(storedPosts, 10) : null,
        reels: storedReels ? parseInt(storedReels, 10) : null
      };
    } catch {
      return { posts: null, reels: null };
    }
  });

  // Derived state based on current content type
  const promptValue = prompts[contentType];
  const activeFilter = filters[contentType];
  const currentFeedId = feedIds[contentType];

  const setPromptValue = (val: string) => setPrompts(prev => ({ ...prev, [contentType]: val }));
  const setActiveFilter = (val: string) => setFilters(prev => ({ ...prev, [contentType]: val }));
  const setCurrentFeedId = (id: number | null) => setFeedIds(prev => ({ ...prev, [contentType]: id }));
  
  const [savedPostIds, setSavedPostIds] = useState<Set<number>>(() => {
    try {
      const stored = sessionStorage.getItem('newsfeed_savedPostIds');
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  });
  
  const [isPolling, setIsPolling] = useState(() => {
    try {
      return sessionStorage.getItem('newsfeed_isPolling') === 'true';
    } catch {
      return false;
    }
  });

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { createFeed, isCreatingFeed, refreshFeed, refreshVideoFeed } = useNewsfeed();
  const { savePost, isSaving } = useSavePost();
  
  // Persist state to sessionStorage
  useEffect(() => {
    try {
      if (filters.posts) sessionStorage.setItem('newsfeed_activeFilter', filters.posts);
      else sessionStorage.removeItem('newsfeed_activeFilter');
      
      if (filters.reels) sessionStorage.setItem('newsfeed_reelsFilter', filters.reels);
      else sessionStorage.removeItem('newsfeed_reelsFilter');
    } catch (e) {
      console.error('Failed to save filters:', e);
    }
  }, [filters]);

  useEffect(() => {
    try {
      if (feedIds.posts !== null) sessionStorage.setItem('newsfeed_currentFeedId', feedIds.posts.toString());
      else sessionStorage.removeItem('newsfeed_currentFeedId');

      if (feedIds.reels !== null) sessionStorage.setItem('newsfeed_reelsFeedId', feedIds.reels.toString());
      else sessionStorage.removeItem('newsfeed_reelsFeedId');
    } catch (e) {
      console.error('Failed to save feedIds:', e);
    }
  }, [feedIds]);

  useEffect(() => {
    try {
      sessionStorage.setItem('newsfeed_savedPostIds', JSON.stringify(Array.from(savedPostIds)));
    } catch (e) {
      console.error('Failed to save savedPostIds:', e);
    }
  }, [savedPostIds]);

  useEffect(() => {
    try {
      sessionStorage.setItem('newsfeed_isPolling', isPolling.toString());
    } catch (e) {
      console.error('Failed to save isPolling:', e);
    }
  }, [isPolling]);

  // Persist content type
  useEffect(() => {
    try {
      sessionStorage.setItem('newsfeed_contentType', contentType);
    } catch (e) {
      console.error('Failed to save contentType:', e);
    }
  }, [contentType]);
  
  // Fetch feed items with polling every 5 seconds when we have a feed
  const { data: postItems = [], isLoading: isLoadingPosts, isFetching: isFetchingPosts } = useFeedItems(
    feedIds.posts,
    { 
      enabled: feedIds.posts !== null && contentType === 'posts' && isPolling,
      refetchInterval: feedIds.posts !== null && contentType === 'posts' && isPolling ? 5000 : undefined
    }
  );

  // Reels Fetching Logic - REPLACED with React Query Hook
  const { data: reelsItems = [], isLoading: isLoadingReels, isFetching: isFetchingReels } = useVideoFeedItems(
    feedIds.reels,
    { 
      enabled: feedIds.reels !== null && contentType === 'reels' && isPolling,
      refetchInterval: feedIds.reels !== null && contentType === 'reels' && isPolling ? 5000 : undefined
    }
  );

  // Determine which items to show
  const posts = contentType === 'posts' ? postItems : reelsItems;
  const isLoadingItems = contentType === 'posts' ? isLoadingPosts : isLoadingReels;
  const isFetching = contentType === 'posts' ? isFetchingPosts : isFetchingReels;

  // Load TikTok Embed Script
  useEffect(() => {
    if (contentType === 'reels' && posts.length > 0) {
      const timer = setTimeout(() => {
        const existingScript = document.getElementById('tiktok-embed-script');
        if (existingScript) {
          existingScript.remove();
        }

        const script = document.createElement('script');
        script.id = 'tiktok-embed-script';
        script.src = "https://www.tiktok.com/embed.js";
        script.async = true;
        document.body.appendChild(script);
      }, 100); // Giảm delay xuống 100ms cho mượt hơn

      return () => clearTimeout(timer);
    }
  }, [contentType, posts.length]); // Chạy lại khi đổi mode hoặc có bài viết mới

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      const maxHeight = 400;
      if (textarea.scrollHeight > maxHeight) {
        textarea.style.height = maxHeight + 'px';
        textarea.style.overflowY = 'auto';
      } else {
        textarea.style.height = 'auto';
        textarea.style.overflowY = 'hidden';
      }
    }
  }, [promptValue]);

  const handleSavePost = async (postId: number) => {
    if (savedPostIds.has(postId)) {
      // Already saved, remove from local state (no unsave API yet)
      setSavedPostIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(postId);
        return newSet;
      });
      return;
    }

    try {
      await savePost({ social_post_id: postId });
      setSavedPostIds(prev => new Set(prev).add(postId));
    } catch (error) {
      console.error('Failed to save post:', error);
    }
  };

  // Listen for saved item removed events from other pages
  useEffect(() => {
    const handleItemRemoved = ((event: CustomEvent) => {
      const { postId } = event.detail;
      console.log('🔔 Event received: savedItemRemoved', postId);
      // Remove the post ID from saved items
      setSavedPostIds(prev => {
        const newSet = new Set(prev);
        const hadItem = newSet.has(postId);
        newSet.delete(postId);
        console.log('🗑️ Removing postId from savedPostIds:', { postId, hadItem, newSize: newSet.size });
        return newSet;
      });
    }) as EventListener;

    window.addEventListener('savedItemRemoved', handleItemRemoved);
    return () => window.removeEventListener('savedItemRemoved', handleItemRemoved);
  }, []);

  const handleManualRefresh = async () => {
    if (currentFeedId) {
      setIsPolling(true);
      if (contentType === 'posts') {
        refreshFeed(currentFeedId);
      } else {
        // Use the mutation from hook instead of direct service call
        refreshVideoFeed(currentFeedId);
      }
    }
  };

  const handleStopPolling = () => {
    setIsPolling(false);
  };

  const handleSubmitPrompt = async () => {
    if (!promptValue.trim()) return;
    
    try {
      let feed: PersonalFeed;

      if (contentType === 'posts') {
        feed = await createFeed({
          title: promptValue.slice(0, 50),
          user_intent: promptValue,
          ranking_style: 'balanced',
          platform: 'bluesky',
        }) as PersonalFeed;
        
        refreshFeed(feed.id);
      } else {
        // Call Video Service
        feed = await newsfeedService.createVideoFeed({
          title: promptValue.slice(0, 50),
          user_intent: promptValue,
          ranking_style: 'balanced',
          platform: 'tiktok',
        });

        // Trigger refresh using mutation
        refreshVideoFeed(feed.id);
      }

      setCurrentFeedId(feed.id);
      setActiveFilter(promptValue);
      setIsPolling(true);
      
    } catch (error) {
      console.error('Failed to submit prompt:', error);
    }
  };

  const handleClearFilter = () => {
    setActiveFilter("");
    setPromptValue("");
    setCurrentFeedId(null);
    // No need to manually clear items, React Query handles cache based on feedId
    setIsPolling(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmitPrompt();
    }
  };

  return (
    <Container>
      <FloatingFilter>
        <HeaderRow>
          <Title>Your Newsfeed</Title>
          {!activeFilter && (
            <ApplyButton onClick={handleSubmitPrompt} disabled={!promptValue.trim() || isCreatingFeed}>
              {isCreatingFeed ? 'Creating...' : 'Apply'}
            </ApplyButton>
          )}
        </HeaderRow>
        {activeFilter ? (
          <ActiveFilterBox>
            <FilterText>{activeFilter}</FilterText>
            <ClearButton onClick={handleClearFilter} title="Clear filter">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </ClearButton>
          </ActiveFilterBox>
        ) : (
          <PromptTextarea
            ref={textareaRef}
            placeholder={contentType === 'reels' ? "Describe the videos you want to see" : "Describe the posts you want to see"}
            value={promptValue}
            onChange={(e) => setPromptValue(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
        )}
        
        {/* Polling indicator inside filter box */}
        {isPolling && currentFeedId && (
          <PollingIndicator>
            <PollingDot $isActive={isFetching} />
            <PollingText>
              {isFetching ? 'Checking for new posts...' : `Auto-refresh enabled • ${posts.length} posts`}
            </PollingText>
            <RefreshButton onClick={handleManualRefresh} title="Refresh now">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
              </svg>
            </RefreshButton>
            <StopPollingButton onClick={handleStopPolling} title="Stop auto-refresh">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="6" y="6" width="12" height="12" />
              </svg>
            </StopPollingButton>
          </PollingIndicator>
        )}

        <ContentTypeSelector>
          <TypeButton 
            $isActive={contentType === 'reels'} 
            onClick={() => setContentType('reels')}
          >
            Reels
          </TypeButton>
          <TypeButton 
            $isActive={contentType === 'posts'} 
            onClick={() => setContentType('posts')}
          >
            Posts
          </TypeButton>
        </ContentTypeSelector>
      </FloatingFilter>

      <FeedColumn>

        {isLoadingItems && currentFeedId && (
          <LoadingState>
            <LoadingSpinner />
            <LoadingText>AI is finding the best {contentType} for you...</LoadingText>
          </LoadingState>
        )}
        
        {!isLoadingItems && posts.length === 0 && currentFeedId && (
          <EmptyState>
            <EmptyIcon>
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 0 1-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
            </EmptyIcon>
            <EmptyText>No {contentType} found yet</EmptyText>
            <EmptySubtext>AI is still searching. New {contentType} will appear automatically.</EmptySubtext>
          </EmptyState>
        )}

        {posts.map((item) => {
          const post = item.post; // FeedItem contains a post object
          
          return (
            <PostCard key={item.id}>
              <CardHeader>
                <UserInfo>
                  <Avatar 
                    src={`https://i.pravatar.cc/150?u=${post.author}`} 
                    alt={post.author} 
                  />
                  <UserDetails>
                    <DisplayName>
                      {post.author}
                    </DisplayName>
                    <MetaRow>
                      <Username>
                        {`@${post.author.split('.')[0]}`}
                      </Username>
                      <Dot>•</Dot>
                      <Timestamp>
                        {formatTimestamp(post.fetched_at)}
                      </Timestamp>
                    </MetaRow>
                  </UserDetails>
                </UserInfo>
                <PlatformBadge platform={post.platform}>
                  {post.platform === "tiktok" ? (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
                    </svg>
                  ) : post.platform === "bluesky" ? (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 10.8c-1.087-2.114-4.046-6.053-6.798-7.995C2.566.944 1.561 1.266.902 1.565.139 1.908 0 3.08 0 3.768c0 .69.378 5.65.624 6.479.815 2.736 3.713 3.66 6.383 3.364.136-.02.275-.039.415-.056-.138.022-.276.04-.415.056-3.912.58-7.387 2.005-2.83 7.078 5.013 5.19 6.87-1.113 7.823-4.308.953 3.195 2.05 9.271 7.733 4.308 4.267-4.308 1.172-6.498-2.74-7.078a8.741 8.741 0 0 1-.415-.056c.14.017.279.036.415.056 2.67.297 5.568-.628 6.383-3.364.246-.828.624-5.79.624-6.478 0-.69-.139-1.861-.902-2.206-.659-.298-1.664-.62-4.3 1.24C16.046 4.748 13.087 8.687 12 10.8Z"/>
                    </svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <circle cx="12" cy="12" r="10"/>
                    </svg>
                  )}
                </PlatformBadge>
              </CardHeader>

              {item.ai_summary && (
                <AISummary>
                  <AILabel>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 8v8m0 0V8m0 8h8M4 12h8"/>
                      <circle cx="12" cy="12" r="10"/>
                    </svg>
                    AI Summary
                  </AILabel>
                  <AISummaryText>{item.ai_summary}</AISummaryText>
                </AISummary>
              )}

              <Content>{post.content}</Content>

              {/* TikTok Embed - Sử dụng component đã memo */}
              {post.embed_quote && post.platform === 'tiktok' && (
                <TikTokContent html={post.embed_quote} />
              )}

              {/* Regular thumbnail/media */}
              {!post.embed_quote && (post.thumbnail_url || post.media_url) && (
                <Thumbnail 
                  src={post.thumbnail_url || post.media_url || ''} 
                  alt="Post media" 
                />
              )}

              <StatsBar>
                <StatItem>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                  </svg>
                  <span>{formatNumber(post.like_count || 0)}</span>
                </StatItem>
                <StatItem>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                    <polyline points="17 6 23 6 23 12" />
                  </svg>
                  <span>{formatNumber(post.repost_count || 0)}</span>
                </StatItem>
                
                {/* Source link button */}
                {post.source_link && (
                  <SourceLinkButton 
                    href={post.source_link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    title="View original post"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                      <polyline points="15 3 21 3 21 9"/>
                      <line x1="10" y1="14" x2="21" y2="3"/>
                    </svg>
                    <span>View</span>
                  </SourceLinkButton>
                )}

                <SaveButton 
                  onClick={() => handleSavePost(post.id)}
                  $saved={savedPostIds.has(post.id)}
                  disabled={isSaving}
                  title={savedPostIds.has(post.id) ? "Remove from saved" : "Save to knowledge graph"}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill={savedPostIds.has(post.id) ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
                  </svg>
                  <span>{savedPostIds.has(post.id) ? "Saved" : "Save"}</span>
                </SaveButton>
              </StatsBar>

              {item.ai_reasoning && (
                <AIReasoning>
                  <AILabel>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/>
                      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                      <line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                    Why this post?
                  </AILabel>
                  <AIReasoningText>{item.ai_reasoning}</AIReasoningText>
                </AIReasoning>
              )}
            </PostCard>
          );
        })}
      </FeedColumn>
    </Container>
  );
}

function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
}

function formatTimestamp(isoDate: string): string {
  const now = new Date();
  const date = new Date(isoDate);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d`;
  return date.toLocaleDateString();
}

const Container = styled.div`
  position: relative;
  min-height: 100vh;
  background: #ffffff;
  overflow-y: auto;
  overflow-x: hidden;

  /* Grid Pattern with Radial Fade */
  &::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: 0;
    background-image: 
      linear-gradient(to right, rgba(13, 148, 136, 0.15) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(13, 148, 136, 0.15) 1px, transparent 1px);
    background-size: 40px 40px;
    mask-image: radial-gradient(ellipse 100% 100% at 50% 0%, rgba(0,0,0,0.6) 0%, transparent 85%);
    -webkit-mask-image: radial-gradient(ellipse 100% 100% at 50% 0%, rgba(0,0,0,0.6) 0%, transparent 85%);
    pointer-events: none;
  }
  
  /* Subtle teal glow at top */
  &::after {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 200px;
    background: radial-gradient(ellipse 80% 50% at 50% 0%, rgba(13, 148, 136, 0.03), transparent 70%);
    pointer-events: none;
    z-index: 0;
  }

  /* Ensure content is above background */
  > * {
    position: relative;
    z-index: 1;
  }

  @media (max-width: 768px) {
    padding: 0;
  }
`;

const FloatingFilter = styled.div`
  position: fixed;
  top: 24px;
  left: calc(var(--sidebar-width, 280px) + 20px);
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  padding: 20px 24px;
  border-radius: 20px;
  box-shadow: 
    0 8px 32px rgba(13, 148, 136, 0.08),
    0 1px 4px rgba(0, 0, 0, 0.04),
    inset 0 0 0 1px rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(13, 148, 136, 0.12);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 380px;
  max-width: 480px;

  &:hover {
    box-shadow: 
      0 12px 40px rgba(13, 148, 136, 0.12),
      0 2px 8px rgba(0, 0, 0, 0.06),
      inset 0 0 0 1px rgba(255, 255, 255, 0.5);
  }

  @media (max-width: 1024px) {
    left: 20px;
    right: 20px;
    min-width: auto;
    max-width: none;
  }

  @media (max-width: 980px) {
    top: 72px; /* Below hamburger button (64px + 8px gap) */
    left: 16px;
    right: 16px;
    padding: 16px 18px;
    border-radius: 16px;
  }
`;

const Title = styled.h2`
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, ${({ theme }) => theme.colors.accent} 0%, ${({ theme }) => theme.colors.primary} 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  line-height: 1.2;
  letter-spacing: -0.02em;

  @media (max-width: 768px) {
    font-size: 1.1rem;
  }
`;

const HeaderRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;

  @media (max-width: 768px) {
    gap: 12px;
  }
`;

const ActiveFilterBox = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: linear-gradient(135deg, rgba(13, 148, 136, 0.08) 0%, rgba(13, 148, 136, 0.04) 100%);
  padding: 12px 16px;
  border-radius: 12px;
  border: 1.5px solid rgba(13, 148, 136, 0.2);
  transition: all 0.2s ease;
  min-height: 44px;
  width: 100%;
  overflow: hidden;

  &:hover {
    border-color: rgba(13, 148, 136, 0.3);
    background: linear-gradient(135deg, rgba(13, 148, 136, 0.1) 0%, rgba(13, 148, 136, 0.05) 100%);
  }
`;


const FilterText = styled.span`
  flex: 1;
  font-size: 0.9rem;
  font-weight: 500;
  color: ${({ theme }) => theme.colors.primary};
  line-height: 1.5;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  min-width: 0;
`;

const ClearButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;

  &:hover {
    background: #ef4444;
    color: white;
    transform: scale(1.15) rotate(90deg);
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
  }

  &:active {
    transform: scale(1.05) rotate(90deg);
  }
`;

const PromptTextarea = styled.textarea`
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.9rem;
  font-family: inherit;
  line-height: 1.5;
  color: ${({ theme }) => theme.colors.primary};
  background: rgba(248, 250, 252, 0.8);
  padding: 12px 16px;
  border-radius: 12px;
  border: 1.5px solid rgba(13, 148, 136, 0.12);
  transition: border-color 0.2s cubic-bezier(0.4, 0, 0.2, 1), background 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 0;
  width: 100%;
  resize: none;
  box-sizing: border-box;
  field-sizing: content;
  height: auto;
  min-height: 44px;
  max-height: 400px;

  &::placeholder {
    color: ${({ theme }) => theme.colors.secondary};
    opacity: 0.5;
    white-space: pre-line;
  }

  &:hover {
    border-color: rgba(13, 148, 136, 0.2);
    background: rgba(255, 255, 255, 0.9);
  }

  &:focus {
    background: white;
    border-color: ${({ theme }) => theme.colors.accent};
    box-shadow: 0 0 0 4px rgba(13, 148, 136, 0.08);
  }

  /* Custom scrollbar */
  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(13, 148, 136, 0.05);
    border-radius: 4px;
    margin: 4px 0;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(13, 148, 136, 0.25);
    border-radius: 4px;
    border: 2px solid transparent;
    background-clip: padding-box;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: rgba(13, 148, 136, 0.4);
    background-clip: padding-box;
  }

  @media (max-width: 768px) {
    width: 100%;
    font-size: 0.85rem;
  }
`;

const ApplyButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  background: linear-gradient(135deg, ${({ theme }) => theme.colors.accent} 0%, ${({ theme }) => theme.colors.accent2} 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(13, 148, 136, 0.2);

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(13, 148, 136, 0.35);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(13, 148, 136, 0.2);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    box-shadow: none;
  }
`;

const FeedColumn = styled.div`
  max-width: 680px;
  margin: 0 auto;
  padding: 24px 20px 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  position: relative;
  z-index: 1;

  @media (max-width: 980px) {
    padding-top: 180px; /* Space for hamburger + FloatingFilter (72px + ~100px filter height + margin) */
  }

  @media (max-width: 768px) {
    max-width: 100%;
    padding: 180px 12px 32px;
    gap: 16px;
  }
`;

const PostCard = styled.div`
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid ${({ theme }) => theme.colors.border};
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  width: 100%;

  &:hover {
    box-shadow: 0 8px 24px rgba(13, 148, 136, 0.12);
    border-color: rgba(13, 148, 136, 0.3);
  }

  @media (max-width: 768px) {
    padding: 20px;
    border-radius: 12px;
  }
`;

const CardHeader = styled.div`
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
`;

const Avatar = styled.img`
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid ${({ theme }) => theme.colors.border};
`;

const UserDetails = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2px;
`;

const DisplayName = styled.div`
  font-weight: 700;
  font-size: 0.95rem;
  color: ${({ theme }) => theme.colors.primary};
`;

const MetaRow = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: ${({ theme }) => theme.colors.secondary};
`;

const Username = styled.span``;

const Dot = styled.span`
  opacity: 0.5;
`;

const Timestamp = styled.span``;

const PlatformBadge = styled.div<{ platform: string }>`
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${({ platform }) => 
    platform === "tiktok" 
      ? "linear-gradient(135deg, #00f2ea 0%, #ff0050 100%)" 
      : platform === "bluesky"
      ? "linear-gradient(135deg, #0085ff 0%, #00a6ff 100%)"
      : "linear-gradient(135deg, #6b7280 0%, #4b5563 100%)"
  };
  color: white;
  flex-shrink: 0;
`;

const Content = styled.p`
  font-size: 0.95rem;
  line-height: 1.6;
  color: ${({ theme }) => theme.colors.primary};
  margin-bottom: 12px;
`;

const Thumbnail = styled.img`
  width: 100%;
  height: auto;
  max-height: 500px;
  object-fit: cover;
  border-radius: 12px;
  margin-bottom: 16px;

  @media (max-width: 768px) {
    max-height: 400px;
    border-radius: 8px;
  }
`;

const StatsBar = styled.div`
  display: flex;
  align-items: center;
  gap: 20px;
  padding-top: 12px;
  border-top: 1px solid ${({ theme }) => theme.colors.border};
`;

const StatItem = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  color: ${({ theme }) => theme.colors.secondary};
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s ease;
  cursor: pointer;

  svg {
    stroke: ${({ theme }) => theme.colors.secondary};
    transition: all 0.2s ease;
  }

  &:hover {
    color: ${({ theme }) => theme.colors.accent};
    
    svg {
      stroke: ${({ theme }) => theme.colors.accent};
      transform: scale(1.1);
    }
  }
`;

const SaveButton = styled.button<{ $saved: boolean }>`
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  padding: 8px 16px;
  background: ${({ $saved, theme }) => 
    $saved 
      ? `linear-gradient(135deg, ${theme.colors.accent} 0%, ${theme.colors.accent2} 100%)`
      : 'rgba(13, 148, 136, 0.1)'
  };
  color: ${({ $saved }) => $saved ? 'white' : '#0d9488'};
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;

  svg {
    stroke: ${({ $saved }) => $saved ? 'white' : '#0d9488'};
    transition: all 0.2s ease;
  }

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const SourceLinkButton = styled.a`
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  text-decoration: none;

  svg {
    stroke: #3b82f6;
    transition: all 0.2s ease;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
    background: rgba(59, 130, 246, 0.15);
  }

  &:active {
    transform: translateY(0);
  }
`;

const PollingIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: linear-gradient(135deg, rgba(13, 148, 136, 0.06) 0%, rgba(13, 148, 136, 0.03) 100%);
  border: 1px solid rgba(13, 148, 136, 0.15);
  border-radius: 10px;
  margin-top: 12px;
`;

const PollingDot = styled.div<{ $isActive: boolean }>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${({ $isActive }) => $isActive ? '#10b981' : '#0d9488'};
  animation: ${({ $isActive }) => $isActive ? 'pulse 1.5s ease-in-out infinite' : 'none'};

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.6;
      transform: scale(1.2);
    }
  }
`;

const PollingText = styled.span`
  flex: 1;
  font-size: 0.85rem;
  font-weight: 500;
  color: ${({ theme }) => theme.colors.primary};
`;

const RefreshButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  background: rgba(13, 148, 136, 0.1);
  color: #0d9488;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;

  svg {
    transition: transform 0.3s ease;
  }

  &:hover {
    background: rgba(13, 148, 136, 0.15);New
    
    svg {
      transform: rotate(180deg);
    }
  }

  &:active {
    transform: scale(0.95);
  }
`;

const StopPollingButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(239, 68, 68, 0.15);
  }

  &:active {
    transform: scale(0.95);
  }
`;

const TikTokEmbed = styled.div`
  margin: 16px 0;
  border-radius: 12px;
  overflow: hidden;
  width: 100%;
  display: flex;
  justify-content: center;
  background: #f9fafb; /* Màu nền nhẹ trong khi chờ load */
  min-height: 300px; /* Chiều cao tối thiểu để tránh giật layout */
  
  /* Style cho iframe khi đã load xong */
  iframe {
    width: 100% !important;
    max-width: 100% !important;
    border-radius: 12px;
    display: block;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  }

  /* Style cho blockquote fallback (text hiển thị trước khi video load) */
  blockquote {
    width: 100%;
    margin: 0;
    padding: 0;
    border: none;
    background: transparent;
  }
`;

const LoadingState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 60px 20px;
  text-align: center;
`;

const LoadingSpinner = styled.div`
  width: 48px;
  height: 48px;
  border: 4px solid rgba(13, 148, 136, 0.1);
  border-top-color: ${({ theme }) => theme.colors.accent};
  border-radius: 50%;
  animation: spin 0.8s linear infinite;

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const LoadingText = styled.p`
  font-size: 1rem;
  font-weight: 600;
  color: ${({ theme }) => theme.colors.primary};
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 80px 20px;
  text-align: center;
`;

const EmptyIcon = styled.div`
  font-size: 4rem;
  opacity: 0.5;
  color: ${({ theme }) => theme.colors.accent};
  
  svg {
    stroke: ${({ theme }) => theme.colors.accent};
  }
`;

const EmptyText = styled.p`
  font-size: 1.1rem;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.primary};
`;

const EmptySubtext = styled.p`
  font-size: 0.9rem;
  color: ${({ theme }) => theme.colors.secondary};
  max-width: 400px;
`;

const AISummary = styled.div`
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(59, 130, 246, 0.08) 100%);
  border: 1.5px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 12px;
`;

const AILabel = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  font-weight: 700;
  color: #8b5cf6;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;

  svg {
    flex-shrink: 0;
  }
`;

const AISummaryText = styled.p`
  font-size: 0.9rem;
  line-height: 1.5;
  color: ${({ theme }) => theme.colors.primary};
  margin: 0;
`;

const AIReasoning = styled.div`
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid ${({ theme }) => theme.colors.border};
`;

const AIReasoningText = styled.p`
  font-size: 0.85rem;
  line-height: 1.6;
  color: ${({ theme }) => theme.colors.secondary};
  font-style: italic;
  margin: 6px 0;
`;

const ContentTypeSelector = styled.div`
  display: flex;
  gap: 12px;
  margin-top: 8px;
`;

const TypeButton = styled.button<{ $isActive: boolean }>`
  flex: 1;
  padding: 10px;
  border-radius: 10px;
  border: none;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  background: ${({ $isActive }) => 
    $isActive 
      ? 'linear-gradient(135deg, #0d9488 0%, #0d9488 100%)' 
      : 'rgba(0, 0, 0, 0.05)'
  };
  color: ${({ $isActive }) => $isActive ? 'white' : '#64748b'};
  box-shadow: ${({ $isActive }) => 
    $isActive 
      ? '0 4px 12px rgba(127, 29, 29, 0.25)' 
      : 'none'
  };

  &:hover {
    transform: translateY(-1px);
    background: ${({ $isActive }) => 
      $isActive 
        ? 'linear-gradient(135deg, #0d9488 0%, #0d9488 100%)' 
        : 'rgba(0, 0, 0, 0.08)'
    };
  }

  &:active {
    transform: translateY(0);
  }
`;
