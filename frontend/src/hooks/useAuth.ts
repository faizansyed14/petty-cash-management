import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";
import { api, getErrorMessage } from "@/services/api";
import type { LoginResponse, User } from "@/types";

const TOKEN_KEY = "pc_token";
const USER_KEY = "pc_user";

function readStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export function useAuth() {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(() => readStoredUser());

  const meQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const { data } = await api.get<User>("/api/auth/me");
      return data;
    },
    enabled: !!token,
    retry: false,
  });

  useEffect(() => {
    if (meQuery.data) {
      setUser(meQuery.data);
      localStorage.setItem(USER_KEY, JSON.stringify(meQuery.data));
    }
  }, [meQuery.data]);

  const loginMutation = useMutation({
    mutationFn: async (payload: { email: string; password: string }) => {
      const { data } = await api.post<LoginResponse>("/api/auth/login", payload);
      return data;
    },
    onSuccess: (data) => {
      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
      setToken(data.access_token);
      setUser(data.user);
      queryClient.setQueryData(["auth", "me"], data.user);
    },
  });

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  return {
    token,
    user: meQuery.data ?? user,
    isAuthenticated: !!token,
    isLoading: !!token && meQuery.isLoading,
    login: loginMutation.mutateAsync,
    loginError: loginMutation.error ? getErrorMessage(loginMutation.error) : null,
    isLoggingIn: loginMutation.isPending,
    logout,
  };
}
