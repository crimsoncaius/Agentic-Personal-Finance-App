import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { apiService, Transaction, Category } from '../api/api';

const Transactions = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);

  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<Omit<Transaction, 'id'>>();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [transactionsData, categoriesData] = await Promise.all([
          apiService.getTransactions(),
          apiService.getCategories(),
        ]);
        
        setTransactions(transactionsData);
        setCategories(categoriesData);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const openModal = (transaction?: Transaction) => {
    if (transaction) {
      setSelectedTransaction(transaction);
      setValue('amount', transaction.amount);
      setValue('date', transaction.date);
      setValue('description', transaction.description || '');
      setValue('is_recurring', transaction.is_recurring);
      setValue('recurrence_period', transaction.recurrence_period);
      setValue('transaction_type', transaction.transaction_type);
      setValue('category_id', transaction.category_id);
    } else {
      setSelectedTransaction(null);
      reset({
        amount: 0,
        date: new Date().toISOString().split('T')[0],
        description: '',
        is_recurring: false,
        recurrence_period: 'NONE',
        transaction_type: 'EXPENSE',
        category_id: categories.length > 0 ? categories[0].id : 1,
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedTransaction(null);
    reset();
  };

  const onSubmit = async (data: Omit<Transaction, 'id'>) => {
    try {
      if (selectedTransaction) {
        // Update existing transaction
        const updatedTransaction = await apiService.updateTransaction(selectedTransaction.id, data);
        setTransactions(transactions.map(t => t.id === updatedTransaction.id ? updatedTransaction : t));
      } else {
        // Create new transaction
        const newTransaction = await apiService.createTransaction(data);
        setTransactions([...transactions, newTransaction]);
      }
      closeModal();
    } catch (error) {
      console.error('Error saving transaction:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this transaction?')) {
      try {
        await apiService.deleteTransaction(id);
        setTransactions(transactions.filter(t => t.id !== id));
      } catch (error) {
        console.error('Error deleting transaction:', error);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-5 flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">Transactions</h1>
        <button
          onClick={() => openModal()}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Add Transaction
        </button>
      </div>

      {/* Transactions Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {transactions.length > 0 ? (
                transactions.map((transaction) => (
                  <tr key={transaction.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(transaction.date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transaction.description || 'No description'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {categories.find(c => c.id === transaction.category_id)?.name || 'Unknown'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <span className={transaction.transaction_type === 'EXPENSE' ? 'text-red-600' : 'text-green-600'}>
                        ${transaction.amount.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transaction.transaction_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => openModal(transaction)}
                        className="text-indigo-600 hover:text-indigo-900 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(transaction.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-sm text-gray-500 text-center">
                    No transactions found. Add one to get started!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transaction Modal */}
      {isModalOpen && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>

            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div className="sm:flex sm:items-start">
                <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    {selectedTransaction ? 'Edit Transaction' : 'Add Transaction'}
                  </h3>
                  <div className="mt-4">
                    <form onSubmit={handleSubmit(onSubmit)}>
                      <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                        <div className="sm:col-span-3">
                          <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
                            Amount
                          </label>
                          <div className="mt-1">
                            <input
                              type="number"
                              step="0.01"
                              id="amount"
                              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              {...register('amount', { required: true, min: 0.01 })}
                            />
                            {errors.amount && (
                              <p className="mt-1 text-sm text-red-600">Amount is required and must be positive</p>
                            )}
                          </div>
                        </div>

                        <div className="sm:col-span-3">
                          <label htmlFor="date" className="block text-sm font-medium text-gray-700">
                            Date
                          </label>
                          <div className="mt-1">
                            <input
                              type="date"
                              id="date"
                              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              {...register('date', { required: true })}
                            />
                            {errors.date && (
                              <p className="mt-1 text-sm text-red-600">Date is required</p>
                            )}
                          </div>
                        </div>

                        <div className="sm:col-span-6">
                          <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                            Description
                          </label>
                          <div className="mt-1">
                            <input
                              type="text"
                              id="description"
                              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              {...register('description')}
                            />
                          </div>
                        </div>

                        <div className="sm:col-span-3">
                          <label htmlFor="transaction_type" className="block text-sm font-medium text-gray-700">
                            Type
                          </label>
                          <div className="mt-1">
                            <select
                              id="transaction_type"
                              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              {...register('transaction_type', { required: true })}
                            >
                              <option value="EXPENSE">Expense</option>
                              <option value="INCOME">Income</option>
                            </select>
                          </div>
                        </div>

                        <div className="sm:col-span-3">
                          <label htmlFor="category_id" className="block text-sm font-medium text-gray-700">
                            Category
                          </label>
                          <div className="mt-1">
                            <select
                              id="category_id"
                              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              {...register('category_id', { required: true })}
                            >
                              {categories.map((category) => (
                                <option key={category.id} value={category.id}>
                                  {category.name}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>

                        <div className="sm:col-span-3">
                          <div className="flex items-center h-5 mt-5">
                            <input
                              id="is_recurring"
                              type="checkbox"
                              className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                              {...register('is_recurring')}
                            />
                            <label htmlFor="is_recurring" className="ml-2 block text-sm text-gray-700">
                              Recurring Transaction
                            </label>
                          </div>
                        </div>

                        <div className="sm:col-span-3">
                          <label htmlFor="recurrence_period" className="block text-sm font-medium text-gray-700">
                            Recurrence Period
                          </label>
                          <div className="mt-1">
                            <select
                              id="recurrence_period"
                              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              {...register('recurrence_period')}
                            >
                              <option value="NONE">None</option>
                              <option value="DAILY">Daily</option>
                              <option value="WEEKLY">Weekly</option>
                              <option value="MONTHLY">Monthly</option>
                              <option value="YEARLY">Yearly</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                        <button
                          type="submit"
                          className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm"
                        >
                          {selectedTransaction ? 'Save Changes' : 'Add Transaction'}
                        </button>
                        <button
                          type="button"
                          onClick={closeModal}
                          className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Transactions; 