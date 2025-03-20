import axios from 'axios';

// Define API base URL
const API_URL = '/api';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Type definitions
export interface Category {
  id: number;
  name: string;
  transaction_type: 'INCOME' | 'EXPENSE';
}

export interface Transaction {
  id: number;
  amount: number;
  date: string;
  description?: string;
  is_recurring: boolean;
  recurrence_period: 'NONE' | 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'YEARLY';
  transaction_type: 'INCOME' | 'EXPENSE';
  category_id: number;
  category?: Category;
}

export interface FinanceSummary {
  total_incomes: number;
  total_expenses: number;
  net: number;
}

// API methods
export const apiService = {
  // Categories
  getCategories: async (): Promise<Category[]> => {
    const response = await api.get('/categories');
    return response.data;
  },
  
  createCategory: async (category: Omit<Category, 'id'>): Promise<Category> => {
    const response = await api.post('/categories', category);
    return response.data;
  },
  
  // Transactions
  getTransactions: async (): Promise<Transaction[]> => {
    const response = await api.get('/transactions');
    return response.data;
  },
  
  getTransaction: async (id: number): Promise<Transaction> => {
    const response = await api.get(`/transactions/${id}`);
    return response.data;
  },
  
  createTransaction: async (transaction: Omit<Transaction, 'id'>): Promise<Transaction> => {
    const response = await api.post('/transactions', transaction);
    return response.data;
  },
  
  updateTransaction: async (id: number, transaction: Omit<Transaction, 'id'>): Promise<Transaction> => {
    const response = await api.put(`/transactions/${id}`, transaction);
    return response.data;
  },
  
  deleteTransaction: async (id: number): Promise<void> => {
    await api.delete(`/transactions/${id}`);
  },
  
  // Reports
  getFinanceSummary: async (): Promise<FinanceSummary> => {
    const response = await api.get('/reports/summary');
    return response.data;
  }
};

export default apiService; 