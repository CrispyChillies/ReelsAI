import styled from "styled-components";
import { useI18n } from "@/app/i18n";
import { useSavedItems } from "@/hooks/useSavedItems";
import ConfirmModal from "@/components/common/ConfirmModal";
import { useState } from "react";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

dayjs.extend(relativeTime);

export default function SavedContent() {
  const { t } = useI18n();
  const { savedItems = [], loading, error, removeSavedItem } = useSavedItems();
  const [itemToDelete, setItemToDelete] = useState<number | null>(null);

  console.log('SavedContent render:', { 
    savedItems, 
    isArray: Array.isArray(savedItems),
    length: savedItems?.length,
    type: typeof savedItems,
    keys: savedItems ? Object.keys(savedItems) : 'null',
    loading, 
    error 
  });

  const handleRemoveClick = (itemId: number) => {
    setItemToDelete(itemId);
  };

  const handleConfirmRemove = async () => {
    if (itemToDelete === null) return;
    
    try {
      await removeSavedItem(itemToDelete);
      setItemToDelete(null);
    } catch (err) {
      console.error('Failed to remove item:', err);
      alert('Failed to remove item');
    }
  };

  const handleCancelRemove = () => {
    setItemToDelete(null);
  };

  function formatNumber(num: number): string {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toString();
  }

  if (loading) {
    return (
      <Container>
        <Header>
          <Title>{t("contentStorageTitle")}</Title>
          <Subtitle>{t("loading") || "Loading"}...</Subtitle>
        </Header>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Header>
          <Title>{t("contentStorageTitle")}</Title>
          <Subtitle style={{ color: '#ef4444' }}>{error}</Subtitle>
        </Header>
      </Container>
    );
  }

  console.log('Rendering table with items:', savedItems.length);

  return (
    <>
      <ConfirmModal
        isOpen={itemToDelete !== null}
        title={t("confirmRemoveTitle")}
        message={t("confirmRemoveMessage")}
        confirmText={t("confirmRemoveBtn")}
        cancelText={t("cancel")}
        onConfirm={handleConfirmRemove}
        onCancel={handleCancelRemove}
        type="danger"
      />
      
      <Container>
      <Header>
        <Title>{t("contentStorageTitle")}</Title>
        <Subtitle>{t("contentStorageSubtitle")} • {savedItems.length} {t("savedItems")}</Subtitle>
      </Header>

      {savedItems.length === 0 ? (
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
              {Array.isArray(savedItems) && savedItems.map((item) => {
                console.log('Rendering item:', item);
                const post = item?.post;
                if (!post) {
                  console.error('Item missing post data:', item);
                  return null;
                }
                
                return (
                <Tr key={item.id}>
                  <Td>
                    <PlatformBadge $platform={post.platform}>
                      {post.platform === "tiktok" ? (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
                        </svg>
                      ) : (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M6.29 18.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0020 3.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.073 4.073 0 01.8 7.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 010 16.407a11.616 11.616 0 006.29 1.84"/>
                        </svg>
                      )}
                      <span>{post.platform === "tiktok" ? "TikTok" : "Bluesky"}</span>
                    </PlatformBadge>
                  </Td>
                  <Td>
                    <AuthorCell>
                      <Avatar src={`https://i.pravatar.cc/150?u=${post.author}`} alt={post.author} />
                      <AuthorInfo>
                        <AuthorName>{post.author}</AuthorName>
                        {item.is_rag_indexed && <RAGBadge>🔍 Indexed</RAGBadge>}
                      </AuthorInfo>
                    </AuthorCell>
                  </Td>
                  <Td>
                    <ContentCell>
                      {post.content}
                      {post.media_url && <ThumbnailIndicator>📷 {t("hasMedia")}</ThumbnailIndicator>}
                      {item.user_notes && <UserNotes>💭 {item.user_notes}</UserNotes>}
                    </ContentCell>
                  </Td>
                  <Td>
                    <EngagementCell>
                      <EngagementItem>
                        <span>❤️</span> {formatNumber(post.like_count || 0)}
                      </EngagementItem>
                      <EngagementItem>
                        <span>💬</span> {formatNumber(post.reply_count || 0)}
                      </EngagementItem>
                      <EngagementItem>
                        <span>🔁</span> {formatNumber(post.repost_count || 0)}
                      </EngagementItem>
                    </EngagementCell>
                  </Td>
                  <Td>
                    <TimeCell>{dayjs(item.saved_at).fromNow()}</TimeCell>
                  </Td>
                  <Td>
                    <ActionsCell>
                      {post.source_link && (
                        <ViewButton 
                          onClick={() => window.open(post.source_link!, '_blank')} 
                          title={t("viewPost") || "View post"}
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                            <polyline points="15 3 21 3 21 9" />
                            <line x1="10" y1="14" x2="21" y2="3" />
                          </svg>
                        </ViewButton>
                      )}
                      <ActionButton onClick={() => handleRemoveClick(item.id)} title={t("remove")}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="3 6 5 6 21 6" />
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                        </svg>
                      </ActionButton>
                    </ActionsCell>
                  </Td>
                </Tr>
                );
              })}
            </tbody>
          </Table>
        </TableWrapper>
      )}
    </Container>
    </>
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

const PlatformBadge = styled.div<{ $platform: string }>`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  background: ${({ $platform }) => 
    $platform === "tiktok" 
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

const RAGBadge = styled.div`
  font-size: 0.75rem;
  color: ${({ theme }) => theme.colors.accent};
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 4px;
`;

const UserNotes = styled.div`
  margin-top: 8px;
  padding: 8px;
  background: rgba(13, 148, 136, 0.05);
  border-left: 3px solid ${({ theme }) => theme.colors.accent};
  border-radius: 4px;
  font-size: 0.85rem;
  color: ${({ theme }) => theme.colors.secondary};
  font-style: italic;
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

const ActionsCell = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ViewButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  background: rgba(13, 148, 136, 0.1);
  color: ${({ theme }) => theme.colors.accent};
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;

  svg {
    stroke: ${({ theme }) => theme.colors.accent};
  }

  &:hover {
    background: ${({ theme }) => theme.colors.accent};
    transform: scale(1.1);
    
    svg {
      stroke: white;
    }
  }

  &:active {
    transform: scale(0.95);
  }
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
