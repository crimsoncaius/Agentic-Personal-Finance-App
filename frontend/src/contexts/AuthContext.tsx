import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { useNavigate, useLocation } from "react-router-dom";

interface AuthContextType {
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const navigate = useNavigate();
  const location = useLocation();

  // Check token on mount and validate it
  useEffect(() => {
    const token = localStorage.getItem("token");
    console.log("[AuthContext] Initial token check:", {
      exists: !!token,
      token: token ? `${token.substring(0, 10)}...` : null,
    });

    if (token) {
      try {
        // Simple validation - check if it's a non-empty string
        if (typeof token === "string" && token.trim().length > 0) {
          console.log(
            "[AuthContext] Token validated, setting authenticated state"
          );
          setIsAuthenticated(true);
        } else {
          console.log("[AuthContext] Invalid token format, clearing");
          localStorage.removeItem("token");
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error("[AuthContext] Error validating token:", error);
        localStorage.removeItem("token");
        setIsAuthenticated(false);
      }
    } else {
      // Only redirect to login if not already on login or register page
      if (location.pathname !== "/login" && location.pathname !== "/register") {
        console.log("[AuthContext] No token found, redirecting to login");
        navigate("/login");
      }
    }
    setLoading(false); // Set loading to false after check
  }, [navigate, location]);

  const login = (token: string) => {
    console.log("[AuthContext] Login called:", {
      tokenReceived: !!token,
      tokenLength: token?.length,
      tokenPreview: token ? `${token.substring(0, 10)}...` : null,
    });

    if (token) {
      localStorage.setItem("token", token);
      setIsAuthenticated(true);
      console.log("[AuthContext] Token stored, navigating to home");
      navigate("/");
    }
  };

  const logout = () => {
    console.log("[AuthContext] Logout called, clearing token");
    localStorage.removeItem("token");
    setIsAuthenticated(false);
    navigate("/login");
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
