import { useState, useEffect } from 'react';
import { savedItemsService } from '@/services/savedItemsService';
import type { SavedItem } from '@/types/savedItems';

export function useSavedItems() {
  const [savedItems, setSavedItems] = useState<SavedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSavedItems = async () => {
    try {
      setLoading(true);
      setError(null);
      const items = await savedItemsService.getSavedItems();
      setSavedItems(items || []);
    } catch (err: any) {
      console.error('Failed to fetch saved items:', err);
      // If 401, user not logged in
      if (err?.response?.status === 401) {
        setError('Please login to view saved items');
      } else {
        setError('Failed to load saved items');
      }
      setSavedItems([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSavedItems();
  }, []);

  const removeSavedItem = async (itemId: number) => {
    try {
      // Find the item before removing to get the post ID
      const itemToRemove = savedItems.find(item => item.id === itemId);
      const postId = itemToRemove?.post?.id;
      
      console.log('🗑️ Removing saved item:', { itemId, postId, itemToRemove });
      
      await savedItemsService.removeSavedItem(itemId);
      setSavedItems(prev => prev.filter(item => item.id !== itemId));
      
      // Dispatch custom event with postId to notify other components
      if (postId) {
        console.log('📤 Dispatching savedItemRemoved event with postId:', postId);
        window.dispatchEvent(new CustomEvent('savedItemRemoved', { 
          detail: { postId } 
        }));
      } else {
        console.warn('⚠️ No postId found for itemId:', itemId);
      }
    } catch (err) {
      console.error('Failed to remove saved item:', err);
      throw err;
    }
  };

  return {
    savedItems,
    loading,
    error,
    refetch: fetchSavedItems,
    removeSavedItem,
  };
}
