import "./App.css";
import { Suspense } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Provider } from "react-redux";
import { store } from "./store/store";
import "primereact/resources/themes/lara-light-green/theme.css";
import "primereact/resources/primereact.min.css";
import "primeicons/primeicons.css";
import HomePage from "./pages/HomePage";
function App() {
  return (
    <Provider store={store}>
        <Router>
          <Suspense fallback={<div>Loading...</div>}>
            <Routes>
                <Route path="/" element={<HomePage />} /> {/* Ez lesz a dashboardpage */}
                <Route path="*" element={<HomePage />} />
            </Routes>
          </Suspense>
        </Router>
    </Provider>
  );
}

export default App;
