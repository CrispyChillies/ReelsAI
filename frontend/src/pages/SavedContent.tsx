import { useState, useEffect } from "react";
import styled from "styled-components";
import { useI18n } from "@/app/i18n";

// Import MOCK_POSTS from NewsfeedPage (in real app, this would be from a shared file)
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

export default function SavedContent() {
  const { t } = useI18n();
  const [savedPostIds, setSavedPostIds] = useState<string[]>([]);
  const [savedPosts, setSavedPosts] = useState<typeof MOCK_POSTS>([]);

  useEffect(() => {
    const saved = localStorage.getItem('saved-posts');
    const ids = saved ? JSON.parse(saved) : [];
    setSavedPostIds(ids);
    setSavedPosts(MOCK_POSTS.filter(post => ids.includes(post.id)));
  }, []);

  const handleRemove = (postId: string) => {
    const newIds = savedPostIds.filter(id => id !== postId);
    setSavedPostIds(newIds);
    setSavedPosts(MOCK_POSTS.filter(post => newIds.includes(post.id)));
    localStorage.setItem('saved-posts', JSON.stringify(newIds));
  };

  function formatNumber(num: number): string {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toString();
  }

  return (
    <Container>
      <Header>
        <Title>{t("contentStorageTitle")}</Title>
        <Subtitle>{t("contentStorageSubtitle")} • {savedPosts.length} {t("savedItems")}</Subtitle>
      </Header>

      {savedPosts.length === 0 ? (
        <EmptyState>
          <EmptyIcon>
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
            </svg>
          </EmptyIcon>
          <EmptyTitle>{t("noSavedContent")}</EmptyTitle>
          <EmptyText>{t("noSavedDesc")}</EmptyText>
        </EmptyState>
      ) : (
        <TableWrapper>
          <Table>
            <thead>
              <tr>
                <Th>{t("platform")}</Th>
                <Th>{t("author")}</Th>
                <Th style={{ width: '40%' }}>{t("content")}</Th>
                <Th>{t("engagement")}</Th>
                <Th>{t("savedTime")}</Th>
                <Th>{t("actions")}</Th>
              </tr>
            </thead>
            <tbody>
              {savedPosts.map((post) => (
                <Tr key={post.id}>
                  <Td>
                    <PlatformBadge platform={post.platform}>
                      {post.platform === "tiktok" ? (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
                        </svg>
                      ) : (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                        </svg>
                      )}
                      <span>{post.platform === "tiktok" ? "TikTok" : "Facebook"}</span>
                    </PlatformBadge>
                  </Td>
                  <Td>
                    <AuthorCell>
                      <Avatar src={post.user.avatar} alt={post.user.displayName} />
                      <AuthorInfo>
                        <AuthorName>{post.user.displayName}</AuthorName>
                        <AuthorUsername>{post.user.username}</AuthorUsername>
                      </AuthorInfo>
                    </AuthorCell>
                  </Td>
                  <Td>
                    <ContentCell>
                      {post.content}
                      {post.thumbnail && <ThumbnailIndicator>📷 {t("hasMedia")}</ThumbnailIndicator>}
                    </ContentCell>
                  </Td>
                  <Td>
                    <EngagementCell>
                      <EngagementItem>
                        <span>❤️</span> {formatNumber(post.stats.likes)}
                      </EngagementItem>
                      <EngagementItem>
                        <span>💬</span> {formatNumber(post.stats.comments)}
                      </EngagementItem>
                      <EngagementItem>
                        <span>📤</span> {formatNumber(post.stats.shares)}
                      </EngagementItem>
                    </EngagementCell>
                  </Td>
                  <Td>
                    <TimeCell>{post.timestamp}</TimeCell>
                  </Td>
                  <Td>
                    <ActionButton onClick={() => handleRemove(post.id)} title={t("remove")}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </ActionButton>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </TableWrapper>
      )}
    </Container>
  );
}

const Container = styled.div`
  position: relative;
  min-height: 100vh;
  background: #ffffff;
  padding: 24px;

  /* Grid Pattern */
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

  > * {
    position: relative;
    z-index: 1;
  }
`;

const Header = styled.div`
  margin-bottom: 32px;
`;

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, ${({ theme }) => theme.colors.accent} 0%, ${({ theme }) => theme.colors.primary} 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px 0;
`;

const Subtitle = styled.p`
  color: ${({ theme }) => theme.colors.secondary};
  font-size: 0.95rem;
  margin: 0;
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
`;

const EmptyIcon = styled.div`
  margin-bottom: 24px;
  color: rgba(13, 148, 136, 0.3);
`;

const EmptyTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.primary};
  margin: 0 0 12px 0;
`;

const EmptyText = styled.p`
  font-size: 1rem;
  color: ${({ theme }) => theme.colors.secondary};
  max-width: 400px;
  margin: 0;
`;

const TableWrapper = styled.div`
  background: white;
  border-radius: 16px;
  border: 1px solid rgba(13, 148, 136, 0.12);
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(13, 148, 136, 0.08);
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const Th = styled.th`
  background: linear-gradient(135deg, rgba(13, 148, 136, 0.08) 0%, rgba(13, 148, 136, 0.04) 100%);
  padding: 16px 20px;
  text-align: left;
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: ${({ theme }) => theme.colors.accent};
  border-bottom: 2px solid rgba(13, 148, 136, 0.2);
`;

const Tr = styled.tr`
  border-bottom: 1px solid rgba(13, 148, 136, 0.08);
  transition: background 0.2s ease;

  &:hover {
    background: rgba(13, 148, 136, 0.02);
  }

  &:last-child {
    border-bottom: none;
  }
`;

const Td = styled.td`
  padding: 16px 20px;
  font-size: 0.9rem;
  color: ${({ theme }) => theme.colors.primary};
  vertical-align: top;
`;

const PlatformBadge = styled.div<{ platform: string }>`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  background: ${({ platform }) => 
    platform === "tiktok" 
      ? "linear-gradient(135deg, #00f2ea 0%, #ff0050 100%)" 
      : "linear-gradient(135deg, #1877f2 0%, #0a66c2 100%)"
  };
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
`;

const AuthorCell = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const Avatar = styled.img`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
`;

const AuthorInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2px;
`;

const AuthorName = styled.div`
  font-weight: 600;
  font-size: 0.9rem;
`;

const AuthorUsername = styled.div`
  font-size: 0.8rem;
  color: ${({ theme }) => theme.colors.secondary};
`;

const ContentCell = styled.div`
  line-height: 1.5;
`;

const ThumbnailIndicator = styled.div`
  margin-top: 8px;
  font-size: 0.8rem;
  color: ${({ theme }) => theme.colors.secondary};
  font-style: italic;
`;

const EngagementCell = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
`;

const EngagementItem = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: ${({ theme }) => theme.colors.secondary};
  
  span {
    font-size: 0.9rem;
  }
`;

const TimeCell = styled.div`
  font-size: 0.85rem;
  color: ${({ theme }) => theme.colors.secondary};
  white-space: nowrap;
`;

const ActionButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;

  svg {
    stroke: #ef4444;
  }

  &:hover {
    background: #ef4444;
    transform: scale(1.1);
    
    svg {
      stroke: white;
    }
  }

  &:active {
    transform: scale(0.95);
  }
`;
