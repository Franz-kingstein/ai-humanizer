import axios, { AxiosInstance, InternalAxiosRequestConfig } from "axios"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      headers: {
        "Content-Type": "application/json",
      },
      timeout: 120000,
    })

    this.client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
      const requestId = crypto.randomUUID().slice(0, 8)
      config.headers["X-Request-ID"] = requestId
      return config
    })
  }

  async health() {
    const res = await this.client.get("/health")
    return res.data
  }

  async analyze(text: string, includeDetails = true) {
    const res = await this.client.post("/api/analyze", { text, include_details: includeDetails })
    return res.data
  }

  async humanize(text: string, style: string, strength: string, preserveFormatting = true) {
    const res = await this.client.post("/api/humanize", {
      text,
      style,
      strength,
      preserve_formatting: preserveFormatting,
    })
    return res.data
  }

  async compare(text: string, style: string, strength: string) {
    const res = await this.client.post("/api/compare", { text, style, strength })
    return res.data
  }

  async models() {
    const res = await this.client.get("/api/models")
    return res.data
  }
}

export const api = new ApiClient()