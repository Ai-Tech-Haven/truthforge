import { createContext, useContext, useState, useEffect, ReactNode } from "react";

const STORAGE_KEY = "tf_mock_mode";

interface MockModeContextType {
  isMockMode: boolean;
  toggleMockMode: () => void;
}

const MockModeContext = createContext<MockModeContextType>({
  isMockMode: true,
  toggleMockMode: () => {},
});

export const MockModeProvider = ({ children }: { children: ReactNode }) => {
  const [isMockMode, setIsMockMode] = useState<boolean>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    // default true (mock) unless explicitly set to "false"
    return stored === null ? true : stored === "true";
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(isMockMode));
  }, [isMockMode]);

  return (
    <MockModeContext.Provider value={{ isMockMode, toggleMockMode: () => setIsMockMode((p) => !p) }}>
      {children}
    </MockModeContext.Provider>
  );
};

export const useMockMode = () => useContext(MockModeContext);
