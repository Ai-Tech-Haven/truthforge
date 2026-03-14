import { createContext, useContext, useState, ReactNode } from "react";

interface MockModeContextType {
  isMockMode: boolean;
  toggleMockMode: () => void;
}

const MockModeContext = createContext<MockModeContextType>({
  isMockMode: true,
  toggleMockMode: () => {},
});

export const MockModeProvider = ({ children }: { children: ReactNode }) => {
  const [isMockMode, setIsMockMode] = useState(true);
  return (
    <MockModeContext.Provider value={{ isMockMode, toggleMockMode: () => setIsMockMode((p) => !p) }}>
      {children}
    </MockModeContext.Provider>
  );
};

export const useMockMode = () => useContext(MockModeContext);
