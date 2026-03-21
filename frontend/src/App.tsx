import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import AnalysisPage from './pages/AnalysisPage';
import ReportsPage from './pages/ReportsPage';
import SuggestionsPage from './pages/SuggestionsPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Parent Route: Wraps the others and renders the Layout */}
        <Route element={<DashboardLayout />}>

          {/* Child Routes: Render inside the Layout's <Outlet /> */}
          <Route path="/" element={<AnalysisPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/suggestions" element={<SuggestionsPage />} />

        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;