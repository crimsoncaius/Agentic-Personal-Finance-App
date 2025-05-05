import { useEffect, useState, useMemo } from "react";
import { useForm } from "react-hook-form";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
  Row,
  Header,
  HeaderGroup,
  SortingState,
  ColumnFiltersState,
  CellContext,
} from "@tanstack/react-table";
import {
  apiService,
  Transaction,
  Category,
  PaginatedResponse,
  PaginationParams,
} from "../api/api";
import { DayPicker, DateRange } from "react-day-picker";
import { format } from "date-fns";
import * as Popover from "@radix-ui/react-popover";
import "react-day-picker/dist/style.css";

const columnHelper = createColumnHelper<Transaction>();

// Helper functions for localStorage
const loadFiltersFromStorage = (): ColumnFiltersState => {
  const savedFilters = localStorage.getItem("transactionFilters");
  return savedFilters ? JSON.parse(savedFilters) : [];
};

const saveFiltersToStorage = (filters: ColumnFiltersState) => {
  localStorage.setItem("transactionFilters", JSON.stringify(filters));
};

const loadSortingFromStorage = (): SortingState => {
  const savedSorting = localStorage.getItem("transactionSorting");
  return savedSorting ? JSON.parse(savedSorting) : [];
};

const saveSortingToStorage = (sorting: SortingState) => {
  localStorage.setItem("transactionSorting", JSON.stringify(sorting));
};

const Transactions = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTransaction, setSelectedTransaction] =
    useState<Transaction | null>(null);
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 0,
    pageSize: 10,
  });
  const [totalPages, setTotalPages] = useState(0);
  const [totalItems, setTotalItems] = useState(0);
  const [sorting, setSorting] = useState<SortingState>(
    loadSortingFromStorage().length > 0
      ? loadSortingFromStorage()
      : [{ id: "date", desc: true }]
  );
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>(
    loadFiltersFromStorage()
  );
  const [selectedDate, setSelectedDate] = useState<Date | undefined>();
  const [modalPopoverOpen, setModalPopoverOpen] = useState(false);
  const [dateRangeFilter, setDateRangeFilter] = useState<DateRange | undefined>(
    () => {
      const filter = columnFilters.find((f) => f.id === "date");
      return filter ? (filter.value as DateRange) : undefined;
    }
  );
  const [descriptionFilter, setDescriptionFilter] = useState<string>(() => {
    const filter = columnFilters.find((f) => f.id === "description");
    return filter ? (filter.value as string) : "";
  });
  const [datePopoverOpen, setDatePopoverOpen] = useState(false);
  const [formSubmitted, setFormSubmitted] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
    watch,
  } = useForm<
    Omit<Transaction, "id"> & { start_date?: string; end_date?: string }
  >();

  // Watch the currently selected transaction type
  const selectedType = watch("transaction_type");

  const formatRecurrencePeriod = (period: string | undefined | null) => {
    if (!period || period === "NONE") return "One-time";
    return period.charAt(0) + period.slice(1).toLowerCase();
  };

  const columns = useMemo(
    () => [
      columnHelper.accessor("date", {
        header: ({ column }) => {
          return (
            <div>
              <div className="flex items-center space-x-2">
                <span>Date</span>
                <button
                  onClick={() =>
                    column.toggleSorting(column.getIsSorted() === "asc")
                  }
                  className="text-gray-500 hover:text-gray-700"
                >
                  {column.getIsSorted() === "asc"
                    ? "↑"
                    : column.getIsSorted() === "desc"
                    ? "↓"
                    : "↕"}
                </button>
              </div>
            </div>
          );
        },
        cell: (info) => {
          const date = new Date(info.getValue());
          return date.toLocaleDateString("en-US", {
            weekday: "short",
            year: "numeric",
            month: "short",
            day: "numeric",
          });
        },
        filterFn: (row, columnId, filterValue: DateRange) => {
          if (!filterValue?.from && !filterValue?.to) return true;
          const date = new Date(row.getValue(columnId));
          const startDate = filterValue.from
            ? new Date(filterValue.from)
            : null;
          const endDate = filterValue.to ? new Date(filterValue.to) : null;
          if (startDate && endDate) {
            return date >= startDate && date <= endDate;
          } else if (startDate) {
            return date >= startDate;
          } else if (endDate) {
            return date <= endDate;
          }
          return true;
        },
      }),
      columnHelper.accessor("description", {
        header: () => <div>Description</div>,
        cell: (info) => (
          <div className="flex flex-col">
            <span className="text-gray-900">
              {info.getValue() || "No description"}
            </span>
          </div>
        ),
      }),
      columnHelper.accessor("category_id", {
        header: ({ column }) => (
          <div>
            <div>Category</div>
            <select
              value={(column.getFilterValue() as string) ?? ""}
              onChange={(e) => column.setFilterValue(e.target.value)}
              className="mt-1 block w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
              <option value="">All</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
        ),
        cell: (info) => {
          const category = categories.find((c) => c.id === info.getValue());
          return (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              {category?.name || "Unknown"}
            </span>
          );
        },
      }),
      columnHelper.accessor("amount", {
        header: ({ column }) => (
          <div className="flex items-center space-x-2">
            <span>Amount</span>
            <button
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="text-gray-500 hover:text-gray-700"
            >
              {column.getIsSorted() === "asc"
                ? "↑"
                : column.getIsSorted() === "desc"
                ? "↓"
                : "↕"}
            </button>
          </div>
        ),
        cell: (info) => {
          const amount = info.getValue();
          const isExpense = info.row.original.transaction_type === "EXPENSE";
          return (
            <div className="flex items-center">
              <span
                className={`font-medium ${
                  isExpense ? "text-red-600" : "text-green-600"
                }`}
              >
                {isExpense ? "-" : "+"}$
                {amount.toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          );
        },
      }),
      columnHelper.accessor("transaction_type", {
        header: ({ column }) => (
          <div>
            <div>Type</div>
            <select
              value={(column.getFilterValue() as string) ?? ""}
              onChange={(e) => column.setFilterValue(e.target.value)}
              className="mt-1 block w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
              <option value="">All</option>
              <option value="EXPENSE">Expense</option>
              <option value="INCOME">Income</option>
            </select>
          </div>
        ),
        cell: (info) => {
          const type = info.getValue();
          return (
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                type === "EXPENSE"
                  ? "bg-red-100 text-red-800"
                  : "bg-green-100 text-green-800"
              }`}
            >
              {type.charAt(0) + type.slice(1).toLowerCase()}
            </span>
          );
        },
      }),
      columnHelper.accessor("id", {
        header: "Actions",
        cell: (info: { getValue: () => number; row: Row<Transaction> }) => (
          <div className="text-right">
            <button
              onClick={() => openModal(info.row.original)}
              className="text-indigo-600 hover:text-indigo-900 mr-4"
            >
              Edit
            </button>
            <button
              onClick={() => handleDelete(info.getValue())}
              className="text-red-600 hover:text-red-900"
            >
              Delete
            </button>
          </div>
        ),
      }),
    ],
    [categories]
  );

  const table = useReactTable({
    data: transactions,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
    manualFiltering: true,
    pageCount: totalPages,
    state: {
      pagination: {
        pageIndex: pagination.page,
        pageSize: pagination.pageSize,
      },
      sorting,
      columnFilters,
    },
    onSortingChange: (newSorting) => {
      const updatedSorting =
        typeof newSorting === "function" ? newSorting(sorting) : newSorting;
      setSorting(updatedSorting);
      saveSortingToStorage(updatedSorting);
    },
    onColumnFiltersChange: (newFilters) => {
      const updatedFilters =
        typeof newFilters === "function"
          ? newFilters(columnFilters)
          : newFilters;
      setColumnFilters(updatedFilters);
      saveFiltersToStorage(updatedFilters);
    },
    onPaginationChange: (updater) => {
      if (typeof updater === "function") {
        const newPagination = updater({
          pageIndex: pagination.page,
          pageSize: pagination.pageSize,
        });
        setPagination({
          page: newPagination.pageIndex,
          pageSize: newPagination.pageSize,
        });
      } else {
        setPagination({
          page: updater.pageIndex,
          pageSize: updater.pageSize,
        });
      }
    },
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [transactionsData, categoriesData] = await Promise.all([
          apiService.getTransactions({
            ...pagination,
            sorting: sorting.map((sort) => ({
              id: sort.id,
              desc: sort.desc,
            })),
            filters: columnFilters.reduce(
              (acc, filter) => ({
                ...acc,
                [filter.id]: filter.value,
              }),
              {}
            ),
          }),
          apiService.getCategories(),
        ]);

        setTransactions(transactionsData.data);
        setCategories(categoriesData);
        setTotalPages(transactionsData.totalPages);
        setTotalItems(transactionsData.total);
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [pagination, sorting, columnFilters]);

  const openModal = (transaction?: Transaction) => {
    if (transaction) {
      setSelectedTransaction(transaction);
      setValue("amount", transaction.amount);
      setValue("description", transaction.description || "");
      setValue("transaction_type", transaction.transaction_type);
      setValue("category_id", transaction.category_id);
      setSelectedDate(new Date(transaction.date));
    } else {
      setSelectedTransaction(null);
      reset({
        amount: 0,
        description: "",
        transaction_type: "EXPENSE",
        category_id: categories.length > 0 ? categories[0].id : 1,
      });
      setSelectedDate(undefined);
    }
    setFormSubmitted(false);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedTransaction(null);
    reset();
    setFormSubmitted(false);
  };

  const onSubmit = async (data: Omit<Transaction, "id">) => {
    setFormSubmitted(true);
    try {
      if (!selectedDate) {
        alert("Please select a date.");
        return;
      }
      const payload = {
        ...data,
        amount: Number(data.amount),
        category_id: Number(data.category_id),
        date: format(selectedDate, "yyyy-MM-dd"),
      };
      if (selectedTransaction) {
        const updatedTransaction = await apiService.updateTransaction(
          selectedTransaction.id,
          payload
        );
        setTransactions(
          transactions.map((t) =>
            t.id === updatedTransaction.id ? updatedTransaction : t
          )
        );
      } else {
        await apiService.createTransaction(payload);
        setLoading(true);
        try {
          const transactionsData = await apiService.getTransactions({
            ...pagination,
            sorting: sorting.map((sort) => ({
              id: sort.id,
              desc: sort.desc,
            })),
            filters: columnFilters.reduce(
              (acc, filter) => ({
                ...acc,
                [filter.id]: filter.value,
              }),
              {}
            ),
          });
          setTransactions(transactionsData.data);
          setTotalPages(transactionsData.totalPages);
          setTotalItems(transactionsData.total);
        } catch (error) {
          console.error("Error fetching transactions after add:", error);
        } finally {
          setLoading(false);
        }
      }
      closeModal();
    } catch (error) {
      console.error("Error saving transaction:", error);
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this transaction?")) {
      try {
        await apiService.deleteTransaction(id);
        // Instead of just filtering local state, refetch the current page
        const transactionsData = await apiService.getTransactions({
          ...pagination,
          sorting: sorting.map((sort) => ({
            id: sort.id,
            desc: sort.desc,
          })),
          filters: columnFilters.reduce(
            (acc, filter) => ({
              ...acc,
              [filter.id]: filter.value,
            }),
            {}
          ),
        });
        setTransactions(transactionsData.data);
        setTotalPages(transactionsData.totalPages);
        setTotalItems(transactionsData.total);
      } catch (error) {
        console.error("Error deleting transaction:", error);
      }
    }
  };

  const handleDateRangeChange = (range: DateRange | undefined) => {
    setDateRangeFilter(range);
    setColumnFilters((prev) => {
      const otherFilters = prev.filter((f) => f.id !== "date");
      if (range && (range.from || range.to)) {
        return [...otherFilters, { id: "date", value: range }];
      }
      return otherFilters;
    });
  };

  const handleDescriptionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setDescriptionFilter(value);
    setColumnFilters((prev) => {
      const otherFilters = prev.filter((f) => f.id !== "description");
      if (value) {
        return [...otherFilters, { id: "description", value }];
      }
      return otherFilters;
    });
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
        <div className="flex gap-3">
          <button
            onClick={() => {
              table.resetColumnFilters();
              setDateRangeFilter(undefined);
              setDescriptionFilter("");
              localStorage.removeItem("transactionFilters");
              localStorage.removeItem("transactionSorting");
            }}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Clear Filters
          </button>
          <button
            onClick={() => openModal()}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Add Transaction
          </button>
        </div>
      </div>
      {/* Filter Bar */}
      <div className="flex flex-wrap gap-4 mb-4">
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">
            DATE
          </label>
          <Popover.Root
            open={datePopoverOpen}
            onOpenChange={setDatePopoverOpen}
          >
            <Popover.Trigger asChild>
              <button
                type="button"
                className="w-64 px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-left focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                {dateRangeFilter?.from && dateRangeFilter?.to
                  ? `${format(dateRangeFilter.from, "MMM d, yyyy")} – ${format(
                      dateRangeFilter.to,
                      "MMM d, yyyy"
                    )}`
                  : "Filter by date range"}
              </button>
            </Popover.Trigger>
            <Popover.Portal>
              <Popover.Content
                sideOffset={8}
                className="z-50 bg-white rounded-lg shadow-lg p-4 border border-gray-200"
                onOpenAutoFocus={(e) => e.preventDefault()}
              >
                <DayPicker
                  mode="range"
                  selected={dateRangeFilter}
                  onSelect={handleDateRangeChange}
                  toDate={new Date()}
                  disabled={{ after: new Date() }}
                  className="rounded-lg"
                />
                <div className="mt-2 flex justify-end">
                  <button
                    className="text-xs text-gray-500 hover:text-gray-700"
                    onClick={() => handleDateRangeChange(undefined)}
                  >
                    Clear
                  </button>
                </div>
              </Popover.Content>
            </Popover.Portal>
          </Popover.Root>
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">
            DESCRIPTION
          </label>
          <input
            type="text"
            value={descriptionFilter}
            onChange={handleDescriptionChange}
            className="w-64 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            placeholder="Filter..."
          />
        </div>
      </div>
      {/* Transactions Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              {table
                .getHeaderGroups()
                .map((headerGroup: HeaderGroup<Transaction>) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map(
                      (header: Header<Transaction, unknown>) => (
                        <th
                          key={header.id}
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                        </th>
                      )
                    )}
                  </tr>
                ))}
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {table.getRowModel().rows.length > 0 ? (
                table.getRowModel().rows.map((row) => (
                  <tr key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <td
                        key={cell.id}
                        className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                      >
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-4 text-sm text-gray-500 text-center"
                  >
                    No transactions found. Add one to get started!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing{" "}
                <span className="font-medium">
                  {pagination.page * pagination.pageSize + 1}
                </span>{" "}
                to{" "}
                <span className="font-medium">
                  {Math.min(
                    (pagination.page + 1) * pagination.pageSize,
                    totalItems
                  )}
                </span>{" "}
                of <span className="font-medium">{totalItems}</span> results
              </p>
            </div>
            <div>
              <nav
                className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px"
                aria-label="Pagination"
              >
                <button
                  onClick={() => table.firstPage()}
                  disabled={!table.getCanPreviousPage()}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                >
                  <span className="sr-only">First</span>
                  {"<<"}
                </button>
                <button
                  onClick={() => table.previousPage()}
                  disabled={!table.getCanPreviousPage()}
                  className="relative inline-flex items-center px-2 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                >
                  <span className="sr-only">Previous</span>
                  {"<"}
                </button>
                <button
                  onClick={() => table.nextPage()}
                  disabled={!table.getCanNextPage()}
                  className="relative inline-flex items-center px-2 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                >
                  <span className="sr-only">Next</span>
                  {">"}
                </button>
                <button
                  onClick={() => table.lastPage()}
                  disabled={!table.getCanNextPage()}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                >
                  <span className="sr-only">Last</span>
                  {">>"}
                </button>
              </nav>
            </div>
          </div>
        </div>
      </div>

      {/* Transaction Modal */}
      {isModalOpen && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div
              className="fixed inset-0 transition-opacity"
              aria-hidden="true"
            >
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>

            <span
              className="hidden sm:inline-block sm:align-middle sm:h-screen"
              aria-hidden="true"
            >
              &#8203;
            </span>

            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div className="sm:flex sm:items-start">
                <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    {selectedTransaction
                      ? "Edit Transaction"
                      : "Add Transaction"}
                  </h3>
                  <div className="mt-4">
                    <form onSubmit={handleSubmit(onSubmit)}>
                      <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                        <div className="sm:col-span-3">
                          <label
                            htmlFor="amount"
                            className="block text-sm font-medium text-gray-700"
                          >
                            Amount
                          </label>
                          <div className="mt-1">
                            <input
                              type="number"
                              step="0.01"
                              id="amount"
                              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              {...register("amount", {
                                required: "Amount is required",
                                min: {
                                  value: 0.01,
                                  message: "Amount must be greater than 0",
                                },
                                max: {
                                  value: 1000000000,
                                  message: "Amount cannot exceed 1 billion",
                                },
                                validate: {
                                  isNumber: (value) =>
                                    !isNaN(value) ||
                                    "Amount must be a valid number",
                                  decimals: (value) => {
                                    const decimals = value
                                      .toString()
                                      .split(".")[1];
                                    return (
                                      !decimals ||
                                      decimals.length <= 2 ||
                                      "Amount cannot have more than 2 decimal places"
                                    );
                                  },
                                },
                              })}
                            />
                            {errors.amount && (
                              <p className="mt-1 text-sm text-red-600">
                                {errors.amount.message}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="sm:col-span-3">
                          <label className="block text-sm font-medium text-gray-700">
                            Date
                          </label>
                          <div className="mt-1">
                            <Popover.Root
                              open={modalPopoverOpen}
                              onOpenChange={setModalPopoverOpen}
                            >
                              <Popover.Trigger asChild>
                                <button
                                  type="button"
                                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-left focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                >
                                  {selectedDate
                                    ? format(selectedDate, "MMM d, yyyy")
                                    : "Select a date"}
                                </button>
                              </Popover.Trigger>
                              <Popover.Portal>
                                <Popover.Content
                                  sideOffset={8}
                                  className="z-50 bg-white rounded-lg shadow-lg p-4 border border-gray-200"
                                  onOpenAutoFocus={(e) => e.preventDefault()}
                                >
                                  <DayPicker
                                    mode="single"
                                    selected={selectedDate}
                                    onSelect={(date) => {
                                      setSelectedDate(date);
                                      if (date) setModalPopoverOpen(false);
                                    }}
                                    toDate={new Date()}
                                    disabled={{ after: new Date() }}
                                    required
                                    className="rounded-lg"
                                  />
                                </Popover.Content>
                              </Popover.Portal>
                            </Popover.Root>
                            {formSubmitted && !selectedDate ? (
                              <p className="mt-1 text-sm text-red-600">
                                Please select a date.
                              </p>
                            ) : null}
                          </div>
                        </div>

                        <div className="sm:col-span-6">
                          <label
                            htmlFor="description"
                            className="block text-sm font-medium text-gray-700"
                          >
                            Description
                          </label>
                          <div className="mt-1">
                            <input
                              type="text"
                              id="description"
                              maxLength={500}
                              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              {...register("description", {
                                required: "Description is required",
                                minLength: {
                                  value: 1,
                                  message: "Description cannot be empty",
                                },
                                maxLength: {
                                  value: 500,
                                  message:
                                    "Description cannot exceed 500 characters",
                                },
                              })}
                            />
                            {errors.description && (
                              <p className="mt-1 text-sm text-red-600">
                                {errors.description.message}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="sm:col-span-3">
                          <label
                            htmlFor="transaction_type"
                            className="block text-sm font-medium text-gray-700"
                          >
                            Type
                          </label>
                          <div className="mt-1">
                            <select
                              id="transaction_type"
                              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              {...register("transaction_type", {
                                required: "Transaction type is required",
                                validate: {
                                  validType: (value) =>
                                    ["INCOME", "EXPENSE"].includes(value) ||
                                    "Invalid transaction type",
                                },
                              })}
                            >
                              <option value="EXPENSE">Expense</option>
                              <option value="INCOME">Income</option>
                            </select>
                          </div>
                        </div>

                        <div className="sm:col-span-3">
                          <label
                            htmlFor="category_id"
                            className="block text-sm font-medium text-gray-700"
                          >
                            Category
                          </label>
                          <div className="mt-1">
                            <select
                              id="category_id"
                              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                              {...register("category_id", {
                                required: "Category is required",
                                validate: {
                                  validCategory: (value) =>
                                    categories.some(
                                      (cat) => cat.id === Number(value)
                                    ) || "Invalid category",
                                },
                              })}
                            >
                              {categories
                                .filter((category) =>
                                  selectedType
                                    ? category.transaction_type === selectedType
                                    : true
                                )
                                .map((category) => (
                                  <option key={category.id} value={category.id}>
                                    {category.name}
                                  </option>
                                ))}
                            </select>
                          </div>
                        </div>
                      </div>

                      <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                        <button
                          type="submit"
                          className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm"
                        >
                          {selectedTransaction
                            ? "Save Changes"
                            : "Add Transaction"}
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
