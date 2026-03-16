// Legacy entry point — App.tsx now handles all routing directly.
// This file is kept to avoid any stale import errors during build.
import { Navigate } from "react-router-dom";
const Index = () => <Navigate to="/" replace />;
export default Index;
