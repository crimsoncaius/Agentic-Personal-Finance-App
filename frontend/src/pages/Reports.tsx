import { useEffect, useState } from 'react';
import { apiService, FinanceSummary, Transaction, Category } from '../api/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const Reports = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [summary, setSummary] = useState<FinanceSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [transactionsData, categoriesData, summaryData] = await Promise.all([
          apiService.getTransactions(),
          apiService.getCategories(),
          apiService.getFinanceSummary(),
        ]);
        
        setTransactions(transactionsData);
        setCategories(categoriesData);
        setSummary(summaryData);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const prepareExpenseChartData = () => {
    if (!transactions.length || !categories.length) return [];

    const expenseTransactions = transactions.filter(t => t.transaction_type === 'EXPENSE');
    const categoryMap = new Map<number, { name: string; amount: number }>();
    
    expenseTransactions.forEach(transaction => {
      const categoryId = transaction.category_id;
      const category = categories.find(c => c.id === categoryId);
      
      if (category) {
        if (categoryMap.has(categoryId)) {
          const current = categoryMap.get(categoryId)!;
          categoryMap.set(categoryId, {
            name: current.name,
            amount: current.amount + transaction.amount,
          });
        } else {
          categoryMap.set(categoryId, {
            name: category.name,
            amount: transaction.amount,
          });
        }
      }
    });

    return Array.from(categoryMap.values())
      .map(item => ({
        name: item.name,
        value: item.amount,
      }))
      .sort((a, b) => b.value - a.value);
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-500">Loading...</div>
      </div>
    );
  }

  const expenseChartData = prepareExpenseChartData();

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Financial Reports</h1>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <dt className="text-sm font-medium text-gray-500 truncate">Total Income</dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-900">${summary.total_incomes.toFixed(2)}</dd>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <dt className="text-sm font-medium text-gray-500 truncate">Total Expenses</dt>
              <dd className="mt-1 text-3xl font-semibold text-red-600">${summary.total_expenses.toFixed(2)}</dd>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <dt className="text-sm font-medium text-gray-500 truncate">Net Balance</dt>
              <dd className={`mt-1 text-3xl font-semibold ${summary.net >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ${summary.net.toFixed(2)}
              </dd>
            </div>
          </div>
        </div>
      )}

      {/* Expense by Category Chart */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-4 py-5 border-b border-gray-200 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Expenses by Category</h3>
        </div>
        <div className="px-4 py-5 sm:p-6">
          {expenseChartData.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={expenseChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {expenseChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-center text-gray-500 py-10">No expense data available for chart</p>
          )}
        </div>
      </div>

      {/* Expense Breakdown Table */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 border-b border-gray-200 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Expense Breakdown</h3>
        </div>
        <div className="px-4 sm:px-6 py-3">
          {expenseChartData.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Amount
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Percentage
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {expenseChartData.map((item, index) => {
                    const totalExpenses = summary?.total_expenses || 0;
                    const percentage = totalExpenses ? (item.value / totalExpenses) * 100 : 0;
                    
                    return (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-red-600">
                          ${item.value.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {percentage.toFixed(1)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 py-4">No expense data available.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Reports; 