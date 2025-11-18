import { api } from "@/utils/http";

export type Profile = {
  id: string;
  email: string;
  name?: string | null;
  age?: number | null;
  city?: string | null;
  phone?: string | null;
  dob?: string | null; // ISO YYYY-MM-DD hoặc null
};

export type UpdateProfilePayload = Partial<{
  name: string | null;
  age: number | null;
  city: string | null;
  phone: string | null;
  dob: string | null; // ISO
}>;

export async function getProfile(): Promise<Profile> {
  const { data } = await api.get("/api/profile");
  return data;
}

export async function updateProfile(
  patch: UpdateProfilePayload
): Promise<Profile> {
  const { data } = await api.put("/api/profile", patch);
  return data;
}

export async function changePassword(
  current_password: string,
  next_password: string
) {
  await api.put("/api/profile/password", { current_password, next_password });
}
