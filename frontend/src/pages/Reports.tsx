import { useEffect, useState } from "react";
import { apiService } from "../api/api";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Sector,
} from "recharts";
import { DayPicker, DateRange } from "react-day-picker";
import * as Popover from "@radix-ui/react-popover";
import { format } from "date-fns";
import "react-day-picker/dist/style.css";

const COLORS = [
  "#8884d8",
  "#82ca9d",
  "#ffc658",
  "#ff8042",
  "#8dd1e1",
  "#a4de6c",
  "#d0ed57",
  "#d8854f",
  "#d0ed57",
  "#a28fd0",
];

const NoOpActiveShape = (props: any) => <Sector {...props} />;

const Reports = () => {
  const [data, setData] = useState<any[]>([]);
  const [type, setType] = useState<"EXPENSE" | "INCOME">("EXPENSE");
  const [dateRange, setDateRange] = useState<DateRange | undefined>();
  const [datePopoverOpen, setDatePopoverOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        transaction_type: type,
      };
      if (dateRange?.from && dateRange?.to) {
        params.start_date = format(dateRange.from, "yyyy-MM-dd");
        params.end_date = format(dateRange.to, "yyyy-MM-dd");
      }
      const response = await apiService.getReportByCategory(params);
      setData(response);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Failed to load report. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line
  }, [type, dateRange]);

  // Pie chart percentage helper
  const getTotal = () => data.reduce((sum, d) => sum + d.total, 0);

  // Filter out zero-value categories for chart and legend
  const filteredData = data.filter((item) => item.total > 0);

  return (
    <div>
      <div className="mb-5 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <h1 className="text-2xl font-semibold text-gray-900">Reports</h1>
        <div className="flex gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type
            </label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value as any)}
              className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            >
              <option value="EXPENSE">Expense</option>
              <option value="INCOME">Income</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date Range
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
                  {dateRange?.from && dateRange?.to
                    ? `${format(dateRange.from, "MMM d, yyyy")} – ${format(
                        dateRange.to,
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
                    selected={dateRange}
                    onSelect={setDateRange}
                    toDate={new Date()}
                    disabled={{ after: new Date() }}
                    className="rounded-lg"
                  />
                  <div className="mt-2 flex justify-end">
                    <button
                      className="text-xs text-gray-500 hover:text-gray-700"
                      onClick={() => setDateRange(undefined)}
                    >
                      Clear
                    </button>
                  </div>
                </Popover.Content>
              </Popover.Portal>
            </Popover.Root>
          </div>
        </div>
      </div>
      {error && (
        <div
          className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative"
          role="alert"
        >
          <span className="block sm:inline">{error}</span>
        </div>
      )}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-gray-500">Loading...</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">
              Breakdown by Category
            </h2>
            {filteredData.length === 0 ? (
              <div className="text-gray-500">
                No data for selected range/type.
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {filteredData.map((item, idx) => (
                  <li key={item.category} className="flex justify-between py-2">
                    <span className="font-medium text-gray-700">
                      {item.category}
                    </span>
                    <span className="text-gray-900 font-semibold">
                      {item.total.toLocaleString(undefined, {
                        style: "currency",
                        currency: "USD",
                      })}
                    </span>
                  </li>
                ))}
                <li className="flex justify-between py-2 font-bold border-t mt-2">
                  <span>Total</span>
                  <span>
                    {filteredData
                      .reduce((sum, d) => sum + d.total, 0)
                      .toLocaleString(undefined, {
                        style: "currency",
                        currency: "USD",
                      })}
                  </span>
                </li>
              </ul>
            )}
          </div>
          <div className="bg-white p-6 rounded-lg shadow flex flex-col items-center justify-center">
            <h2 className="text-lg font-semibold mb-4">Pie Chart</h2>
            {filteredData.length === 0 ? (
              <div className="text-gray-500">No data to display.</div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={filteredData}
                    dataKey="total"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    innerRadius={60}
                    isAnimationActive={false}
                    activeShape={NoOpActiveShape}
                  >
                    {filteredData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(_, __, props: any) => {
                      const total = filteredData.reduce(
                        (sum, d) => sum + d.total,
                        0
                      );
                      const percent =
                        total > 0 ? (props.payload.total / total) * 100 : 0;
                      return [`${percent.toFixed(1)}%`, props.payload.category];
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;
