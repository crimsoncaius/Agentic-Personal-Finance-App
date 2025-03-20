import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();
  const { pathname } = location;
  
  const isActive = (path: string) => {
    if (path === '/' && pathname === '/') {
      return true;
    }
    return path !== '/' && pathname.startsWith(path);
  };

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <span className="text-xl font-bold text-indigo-600">Personal Finance</span>
            </div>
            <div className="ml-6 flex space-x-8">
              <Link
                to="/"
                className={`inline-flex items-center px-1 pt-1 border-b-2 ${
                  isActive('/') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } text-sm font-medium leading-5 focus:outline-none focus:text-gray-700 transition duration-150 ease-in-out`}
              >
                Dashboard
              </Link>
              <Link
                to="/transactions"
                className={`inline-flex items-center px-1 pt-1 border-b-2 ${
                  isActive('/transactions') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } text-sm font-medium leading-5 focus:outline-none focus:text-gray-700 transition duration-150 ease-in-out`}
              >
                Transactions
              </Link>
              <Link
                to="/categories"
                className={`inline-flex items-center px-1 pt-1 border-b-2 ${
                  isActive('/categories') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } text-sm font-medium leading-5 focus:outline-none focus:text-gray-700 transition duration-150 ease-in-out`}
              >
                Categories
              </Link>
              <Link
                to="/reports"
                className={`inline-flex items-center px-1 pt-1 border-b-2 ${
                  isActive('/reports') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } text-sm font-medium leading-5 focus:outline-none focus:text-gray-700 transition duration-150 ease-in-out`}
              >
                Reports
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 