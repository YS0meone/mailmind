import useSWR from 'swr';

interface User {
  email: string;
  name?: string;
  id?: string;
}

const fetcher = (url: string) =>
  fetch(url, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  }).then((res) => {
    if (!res.ok) {
      throw new Error('Failed to fetch user');
    }
    return res.json();
  });

export function useCurrentUser() {
  const { data, error, isLoading } = useSWR<User>(
    'http://localhost:8000/auth/me',
    fetcher,
    {
      revalidateOnFocus: false,
      shouldRetryOnError: false,
    }
  );

  // Fallback to mock user if API fails (for development)
  const mockUser: User = {
    email: "user@example.com",
    name: "John Doe",
    id: "1"
  };

  return {
    user: data || (error ? mockUser : undefined),
    isLoading,
    error
  };
}
