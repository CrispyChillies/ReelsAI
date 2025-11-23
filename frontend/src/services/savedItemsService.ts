import axiosInstance from '@/lib/axios';
import type { SavedItem, SaveItemRequest } from '@/types/savedItems';

export const savedItemsService = {
  // Get all saved items
  async getSavedItems(): Promise<SavedItem[]> {
    const response = await axiosInstance.get<{ success: boolean; count: number; results: SavedItem[] }>('/list/');
    return response.data.results || [];
  },

  // Save a new item
  async saveItem(data: SaveItemRequest): Promise<{ status: string; message: string; saved_id: number }> {
    const response = await axiosInstance.post('/save/', data);
    return response.data;
  },

  // Remove saved item (if backend supports DELETE)
  async removeSavedItem(itemId: number): Promise<void> {
    await axiosInstance.delete(`/delete/${itemId}/`);
  },
};
