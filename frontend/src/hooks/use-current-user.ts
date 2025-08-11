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
    `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/auth/me`,
    fetcher,
    {
      revalidateOnFocus: false,
      shouldRetryOnError: false,
    }
  );

  return {
    user: data,
    isLoading,
    error
  };
}
