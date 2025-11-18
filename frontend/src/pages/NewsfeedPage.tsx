import { useState, useRef, useEffect } from "react";
import styled from "styled-components";
import { useI18n } from "@/app/i18n";

// Mock data
const MOCK_POSTS = [
  {
    id: "1",
    platform: "tiktok",
    user: {
      avatar: "https://i.pravatar.cc/150?img=1",
      username: "@cutecats.bsky.social",
      displayName: "Cute Cats",
    },
    content: "Every day I get closer and closer to get a cat for my cat. 🐱💕",
    timestamp: "35s",
    stats: { likes: 88, comments: 16, shares: 70 },
    thumbnail: null,
  },
  {
    id: "2",
    platform: "facebook",
    user: {
      avatar: "https://i.pravatar.cc/150?img=2",
      username: "@mochidog.bsky.social",
      displayName: "Mochi Dog",
    },
    content: "Good morning from the fluffiest boy! 🌞🐕",
    timestamp: "5m",
    stats: { likes: 3000, comments: 70000, shares: 3000 },
    thumbnail: "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400",
  },
  {
    id: "3",
    platform: "tiktok",
    user: {
      avatar: "https://i.pravatar.cc/150?img=3",
      username: "@dannycat.bsky.social",
      displayName: "Danny Cat",
    },
    content: "Miau! Look what I just did!! 😹",
    timestamp: "1h",
    stats: { likes: 1250, comments: 89, shares: 234 },
    thumbnail: "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400",
  },
  {
    id: "4",
    platform: "facebook",
    user: {
      avatar: "https://i.pravatar.cc/150?img=4",
      username: "@foodlover.social",
      displayName: "Food Lover",
    },
    content: "Just made the perfect pasta carbonara! Recipe in comments 🍝✨",
    timestamp: "2h",
    stats: { likes: 5420, comments: 312, shares: 891 },
    thumbnail: "https://images.unsplash.com/photo-1612874742237-6526221588e3?w=400",
  },
  {
    id: "5",
    platform: "tiktok",
    user: {
      avatar: "https://i.pravatar.cc/150?img=5",
      username: "@travelbug.world",
      displayName: "Travel Bug",
    },
    content: "Sunset in Santorini never gets old 🌅💙 #travel #greece",
    timestamp: "3h",
    stats: { likes: 12500, comments: 456, shares: 2100 },
    thumbnail: "https://images.unsplash.com/photo-1613395877344-13d4a8e0d49e?w=400",
  },
  {
    id: "6",
    platform: "facebook",
    user: {
      avatar: "https://i.pravatar.cc/150?img=6",
      username: "@techguru.dev",
      displayName: "Tech Guru",
    },
    content: "New AI model just dropped! This changes everything in computer vision 🤖💻",
    timestamp: "5h",
    stats: { likes: 8900, comments: 1200, shares: 3400 },
    thumbnail: null,
  },
];

export default function NewsfeedPage() {
  const { t } = useI18n();
  const [promptValue, setPromptValue] = useState("");
  const [activeFilter, setActiveFilter] = useState("");
  const [posts] = useState(MOCK_POSTS);
  const [savedPosts, setSavedPosts] = useState<string[]>(() => {
    const saved = localStorage.getItem('saved-posts');
    return saved ? JSON.parse(saved) : [];
  });
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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

  const handleSavePost = (postId: string) => {
    setSavedPosts(prev => {
      const newSaved = prev.includes(postId)
        ? prev.filter(id => id !== postId)
        : [...prev, postId];
      localStorage.setItem('saved-posts', JSON.stringify(newSaved));
      return newSaved;
    });
  };

  const handleSubmitPrompt = () => {
    if (!promptValue.trim()) return;
    setActiveFilter(promptValue);
    console.log("Filter newsfeed by:", promptValue);
    // TODO: Filter posts based on prompt when backend ready
  };

  const handleClearFilter = () => {
    setActiveFilter("");
    setPromptValue("");
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
            <ApplyButton onClick={handleSubmitPrompt} disabled={!promptValue.trim()}>
              Apply 
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
            placeholder="Describe the content you want to see"
            value={promptValue}
            onChange={(e) => setPromptValue(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
        )}
      </FloatingFilter>

      <FeedColumn>
        {posts.map((post) => (
          <PostCard key={post.id}>
            <CardHeader>
              <UserInfo>
                <Avatar src={post.user.avatar} alt={post.user.displayName} />
                <UserDetails>
                  <DisplayName>{post.user.displayName}</DisplayName>
                  <MetaRow>
                    <Username>{post.user.username}</Username>
                    <Dot>•</Dot>
                    <Timestamp>{post.timestamp}</Timestamp>
                  </MetaRow>
                </UserDetails>
              </UserInfo>
              <PlatformBadge platform={post.platform}>
                {post.platform === "tiktok" ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
                  </svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                  </svg>
                )}
              </PlatformBadge>
            </CardHeader>

            <Content>{post.content}</Content>

            {post.thumbnail && (
              <Thumbnail src={post.thumbnail} alt="Post thumbnail" />
            )}

            <StatsBar>
              <StatItem>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                </svg>
                <span>{formatNumber(post.stats.likes)}</span>
              </StatItem>
              <StatItem>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                <span>{formatNumber(post.stats.comments)}</span>
              </StatItem>
              <StatItem>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                  <polyline points="17 6 23 6 23 12" />
                </svg>
                <span>{formatNumber(post.stats.shares)}</span>
              </StatItem>
              <SaveButton 
                onClick={() => handleSavePost(post.id)}
                $saved={savedPosts.includes(post.id)}
                title={savedPosts.includes(post.id) ? "Remove from saved" : "Save to knowledge graph"}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill={savedPosts.includes(post.id) ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
                  <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
                </svg>
                <span>{savedPosts.includes(post.id) ? "Saved" : "Save"}</span>
              </SaveButton>
            </StatsBar>
          </PostCard>
        ))}
      </FeedColumn>
    </Container>
  );
}

function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
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
  left: 300px;
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

  @media (max-width: 768px) {
    top: 16px;
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

const FilterLabel = styled.span`
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: ${({ theme }) => theme.colors.accent};
  flex-shrink: 0;
  padding-top: 2px;
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

  @media (max-width: 768px) {
    max-width: 100%;
    padding: 16px 12px 32px;
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
      : "linear-gradient(135deg, #1877f2 0%, #0a66c2 100%)"
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

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);
  }

  &:active {
    transform: translateY(0);
  }
`;
