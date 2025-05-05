import axios, { AxiosError } from "axios";

// Define API base URL
const API_URL = "/api";

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor to include token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token && config.headers) {
      // Make sure we're using the correct format: "Bearer <token>"
      config.headers.Authorization = `Bearer ${token}`;
      console.log("Adding token to request:", {
        url: config.url,
        headers: config.headers,
      });
    } else {
      console.log("No token found for request:", config.url);
    }
    return config;
  },
  (error) => {
    console.error("Request interceptor error:", error);
    return Promise.reject(error);
  }
);

// Add response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    console.log("Response received:", {
      url: response.config.url,
      status: response.status,
      data: response.data,
    });
    return response;
  },
  (error: AxiosError) => {
    console.error("API Error:", {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
      headers: error.config?.headers,
    });
    return Promise.reject(error);
  }
);

// Type definitions
export interface Category {
  id: number;
  name: string;
  transaction_type: "INCOME" | "EXPENSE";
}

export interface Transaction {
  id: number;
  amount: number;
  date: string;
  description: string;
  transaction_type: "INCOME" | "EXPENSE";
  category_id: number;
}

export interface PaginationParams {
  page: number;
  pageSize: number;
  start_date?: string;
  end_date?: string;
  sort_by?: string;
  sort_desc?: boolean;
  filter_date?: string;
  filter_description?: string;
  filter_category_id?: number;
  filter_amount?: number;
  filter_transaction_type?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface ChatResponse {
  response: string;
  data?: any;
  success: boolean;
  error?: string;
}

// API service
export const apiService = {
  // Auth
  login: async (data: LoginData): Promise<LoginResponse> => {
    try {
      console.log("Making login request to:", `${API_URL}/auth/login`);
      // Convert the data to URLSearchParams for x-www-form-urlencoded format
      const formData = new URLSearchParams();
      formData.append("username", data.email); // FastAPI OAuth2 expects 'username'
      formData.append("password", data.password);

      const response = await api.post<LoginResponse>("/auth/login", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });
      console.log("Login response received:", response.data);
      return response.data;
    } catch (error) {
      console.error("Login request failed:", error);
      throw error;
    }
  },

  register: async (data: RegisterData): Promise<void> => {
    try {
      await api.post("/auth/register", data);
    } catch (error) {
      console.error("Registration request failed:", error);
      throw error;
    }
  },

  // Categories
  getCategories: async (): Promise<Category[]> => {
    const response = await api.get<Category[]>("/categories");
    return response.data;
  },

  createCategory: async (category: Omit<Category, "id">): Promise<Category> => {
    const response = await api.post<Category>("/categories", category);
    return response.data;
  },

  updateCategory: async (
    id: number,
    category: Omit<Category, "id">
  ): Promise<Category> => {
    const response = await api.put<Category>(`/categories/${id}`, category);
    return response.data;
  },

  deleteCategory: async (id: number): Promise<void> => {
    await api.delete(`/categories/${id}`);
  },

  // Transactions
  getTransactions: async (
    params: PaginationParams & {
      filters?: {
        date?: { startDate?: string; endDate?: string };
        description?: string;
        category_id?: string;
        amount?: number;
        transaction_type?: string;
      };
      sorting?: { id: string; desc: boolean }[];
    }
  ): Promise<PaginatedResponse<Transaction>> => {
    const { filters, sorting, ...paginationParams } = params;

    // Convert filters to API format
    const apiParams: PaginationParams = {
      ...paginationParams,
      start_date: filters?.date?.startDate,
      end_date: filters?.date?.endDate,
      filter_description: filters?.description,
      filter_category_id: filters?.category_id
        ? parseInt(filters.category_id)
        : undefined,
      filter_amount: filters?.amount,
      filter_transaction_type: filters?.transaction_type,
    };

    // Add sorting if present
    if (sorting && sorting.length > 0) {
      apiParams.sort_by = sorting[0].id;
      apiParams.sort_desc = sorting[0].desc;
    }

    const response = await api.get<PaginatedResponse<Transaction>>(
      "/transactions",
      {
        params: apiParams,
      }
    );
    return response.data;
  },

  createTransaction: async (
    transaction: Omit<Transaction, "id">
  ): Promise<Transaction> => {
    const response = await api.post<Transaction>("/transactions/", transaction);
    return response.data;
  },

  updateTransaction: async (
    id: number,
    transaction: Partial<Omit<Transaction, "id">>
  ): Promise<Transaction> => {
    const response = await api.put<Transaction>(
      `/transactions/${id}`,
      transaction
    );
    return response.data;
  },

  deleteTransaction: async (id: number): Promise<void> => {
    await api.delete(`/transactions/${id}`);
  },

  // Assistant
  transcribeAudio: async (audioFile: File): Promise<{ text: string }> => {
    const formData = new FormData();
    formData.append("file", audioFile);
    const response = await api.post<{ text: string }>(
      "/agent/transcribe",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  // Chat
  sendChatMessage: async (content: string): Promise<ChatResponse> => {
    const requestData = { content }; // Send content directly as a string
    console.log("Sending chat message:", {
      url: "/agent/chat",
      data: requestData,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });

    try {
      const response = await api.post<ChatResponse>(
        "/agent/chat",
        requestData,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      console.log("Chat response:", {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data,
      });
      return response.data;
    } catch (error: any) {
      console.error("Chat API error:", {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        headers: error.response?.headers,
        error: error.message,
        stack: error.stack,
      });
      throw error;
    }
  },

  resetChat: async (): Promise<ChatResponse> => {
    console.log("Resetting chat");
    try {
      const response = await api.post<ChatResponse>("/agent/chat/reset");
      console.log("Reset response:", {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data,
      });
      return response.data;
    } catch (error: any) {
      console.error("Reset API error:", {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        headers: error.response?.headers,
        error: error.message,
        stack: error.stack,
      });
      throw error;
    }
  },

  getReportByCategory: async (params: {
    transaction_type: "INCOME" | "EXPENSE";
    start_date?: string;
    end_date?: string;
  }): Promise<{ category: string; total: number }[]> => {
    const response = await api.get("/reports/by-category", { params });
    return response.data;
  },
};

export default apiService;
