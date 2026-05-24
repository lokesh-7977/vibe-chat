export type UUID = string;
export type DateTimeString = string;

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | { [key: string]: JsonValue }
  | JsonValue[];

export type ApiResponse<T> = {
  success: boolean;
  message: string;
  data: T | null;
};

