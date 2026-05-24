import type { UUID } from "../common";

export type UserCreate = {
  fullName: string;
  email: string;
  password: string;
};

export type UserResponse = {
  id: UUID;
  fullName: string;
  username: string;
  email: string;
  isActive: boolean;
  isVerified: boolean;
  isDeleted: boolean;
};

export type UserLogin = {
  email: string;
  password: string;
};

export type UserUpdate = {
  fullName?: string;
  username?: string;
  email?: string;
};
