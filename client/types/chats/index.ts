export type Room = {
  id: string;
  name: string;
  description: string;
  time: string;
  unread: number;
  avatar: string;
  online?: boolean;
};

export type Message = {
  id: string;
  userId?: string | null;
  author: string;
  role: "member" | "me";
  content: string;
  time: string;
  replyTo?: {
    author: string;
    content: string;
  };
  isAi?: boolean;
  isPrivate?: boolean;
  isStreaming?: boolean;
};
