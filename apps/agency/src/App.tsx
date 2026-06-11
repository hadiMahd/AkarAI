import { RouterProvider } from "react-router-dom";
import { router } from "./app/router";
import { Providers } from "./app/providers";
import { ErrorBoundary } from "@/components/ErrorBoundary";

function App() {
  return (
    <ErrorBoundary>
      <Providers>
        <RouterProvider router={router} />
      </Providers>
    </ErrorBoundary>
  );
}

export default App;
