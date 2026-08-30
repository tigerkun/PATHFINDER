import type { components } from "./api-types";

export type PredictRequest = components["schemas"]["PredictRequest"];
export type PredictSuccessResponse = components["schemas"]["PredictSuccessResponse"];
export type ProfileResponse = components["schemas"]["ProfileResponse"];
export type JobCreateResponse = components["schemas"]["JobCreateResponse"];
export type JobStatusResponse = components["schemas"]["JobStatusResponse"];
export type OptionsResponse = components["schemas"]["OptionsResponse"];
export type FormSchemaResponse = components["schemas"]["FormSchemaResponse"];
export type ExamplesResponse = components["schemas"]["ExamplesResponse"];
export type ApiErrorResponse = components["schemas"]["ApiErrorResponse"];

type ApiClientConfig = {
  baseUrl: string;
  apiKey: string;
};

export class PathfinderApiClient {
  private readonly baseUrl: string;
  private readonly apiKey: string;

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/+$/, "");
    this.apiKey = config.apiKey;
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": this.apiKey,
        ...(init?.headers ?? {}),
      },
    });

    const body = (await response.json()) as T | ApiErrorResponse;
    if (!response.ok) {
      throw body;
    }
    return body as T;
  }

  predict(payload: PredictRequest): Promise<PredictSuccessResponse> {
    return this.request<PredictSuccessResponse>("/api/v1/predict", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  profile(username: string): Promise<ProfileResponse> {
    return this.request<ProfileResponse>(`/api/v1/profile/${encodeURIComponent(username)}`);
  }

  createPredictJob(payload: PredictRequest): Promise<JobCreateResponse> {
    return this.request<JobCreateResponse>("/api/v1/predict/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  getPredictJob(jobId: string): Promise<JobStatusResponse> {
    return this.request<JobStatusResponse>(`/api/v1/predict/jobs/${encodeURIComponent(jobId)}`);
  }

  cancelPredictJob(jobId: string): Promise<{ status: string; data: Record<string, unknown> }> {
    return this.request<{ status: string; data: Record<string, unknown> }>(
      `/api/v1/predict/jobs/${encodeURIComponent(jobId)}`,
      { method: "DELETE" },
    );
  }

  options(): Promise<OptionsResponse> {
    return this.request<OptionsResponse>("/api/v1/options");
  }

  formSchema(): Promise<FormSchemaResponse> {
    return this.request<FormSchemaResponse>("/api/v1/schema/form");
  }

  examples(): Promise<ExamplesResponse> {
    return this.request<ExamplesResponse>("/api/v1/examples");
  }

  streamPredictJobEvents(jobId: string): string {
    const path = `/api/v1/predict/jobs/${encodeURIComponent(jobId)}/events`;
    const params = new URLSearchParams({ api_key: this.apiKey });
    return `${this.baseUrl}${path}?${params.toString()}`;
  }
}
