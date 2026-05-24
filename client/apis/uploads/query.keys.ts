import type { QueryKey } from "@tanstack/react-query";

export type QueryDef<TKey extends QueryKey = QueryKey> = {
  key: TKey;
  url: string;
};

export const uploadQueryKeys = {
  presign: {
    key: ["uploads", "presign"] as const,
    url: "/uploads/presign",
  },
  complete: (documentId: string): QueryDef<readonly ["uploads", "complete", string]> => ({
    key: ["uploads", "complete", documentId] as const,
    url: `/uploads/${documentId}/complete`,
  }),
  imageUrl: (key: string): QueryDef<readonly ["uploads", "image-url", string]> => ({
    key: ["uploads", "image-url", key] as const,
    url: `/uploads/image-url?key=${encodeURIComponent(key)}`,
  }),
  imageSummary: (key: string): QueryDef<readonly ["uploads", "image-summary", string]> => ({
    key: ["uploads", "image-summary", key] as const,
    url: `/uploads/image-summary?key=${encodeURIComponent(key)}`,
  }),
  imageSummaryStream: (key: string): QueryDef<readonly ["uploads", "image-summary-stream", string]> => ({
    key: ["uploads", "image-summary-stream", key] as const,
    url: `/uploads/image-summary/stream?key=${encodeURIComponent(key)}`,
  }),
  documentSummary: (key: string): QueryDef<readonly ["uploads", "document-summary", string]> => ({
    key: ["uploads", "document-summary", key] as const,
    url: `/uploads/document-summary?key=${encodeURIComponent(key)}`,
  }),
  documentSummaryStream: (key: string): QueryDef<readonly ["uploads", "document-summary-stream", string]> => ({
    key: ["uploads", "document-summary-stream", key] as const,
    url: `/uploads/document-summary/stream?key=${encodeURIComponent(key)}`,
  }),
  documentQaStream: (key: string): QueryDef<readonly ["uploads", "document-qa-stream", string]> => ({
    key: ["uploads", "document-qa-stream", key] as const,
    url: `/uploads/document-qa/stream?key=${encodeURIComponent(key)}`,
  }),
} as const;
