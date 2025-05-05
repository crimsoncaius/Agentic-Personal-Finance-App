import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

const Navbar = () => {
  const location = useLocation();
  const { pathname } = location;
  const { logout } = useAuth();

  const isActive = (path: string) => {
    if (
      path === "/transactions" &&
      (pathname === "/" || pathname.startsWith("/transactions"))
    ) {
      return true;
    }
    return (
      path !== "/transactions" && path !== "/" && pathname.startsWith(path)
    );
  };

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <span className="text-xl font-bold text-indigo-600">
                Personal Finance
              </span>
            </div>
            <div className="ml-6 flex space-x-8">
              <Link
                to="/transactions"
                className={`inline-flex items-center px-1 pt-1 border-b-2 ${
                  isActive("/transactions")
                    ? "border-indigo-500 text-gray-900"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                } text-sm font-medium leading-5 focus:outline-none focus:text-gray-700 transition duration-150 ease-in-out`}
              >
                Transactions
              </Link>
              <Link
                to="/categories"
                className={`inline-flex items-center px-1 pt-1 border-b-2 ${
                  isActive("/categories")
                    ? "border-indigo-500 text-gray-900"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                } text-sm font-medium leading-5 focus:outline-none focus:text-gray-700 transition duration-150 ease-in-out`}
              >
                Categories
              </Link>
              <Link
                to="/reports"
                className={`inline-flex items-center px-1 pt-1 border-b-2 ${
                  isActive("/reports")
                    ? "border-indigo-500 text-gray-900"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                } text-sm font-medium leading-5 focus:outline-none focus:text-gray-700 transition duration-150 ease-in-out`}
              >
                Reports
              </Link>
              <Link
                to="/assistant"
                className={`inline-flex items-center px-1 pt-1 border-b-2 ${
                  isActive("/assistant")
                    ? "border-indigo-500 text-gray-900"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                } text-sm font-medium leading-5 focus:outline-none focus:text-gray-700 transition duration-150 ease-in-out`}
              >
                Assistant
              </Link>
            </div>
          </div>
          <div className="flex items-center">
            <button
              onClick={logout}
              className="ml-4 px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
