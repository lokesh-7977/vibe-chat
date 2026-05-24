import type { DateTimeString } from "../common";

export type HealthResponse = {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: DateTimeString;
};

