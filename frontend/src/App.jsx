import ConfigEditor from './components/ConfigEditor';
import JobRequirements from './components/JobRequirements';
import SelfReviewSummary from './components/SelfReviewSummary';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Self-Review</h1>
        <p>Manage your performance self-review configuration and view summaries</p>
      </header>
      <main className="app-main">
        <ConfigEditor />
        <JobRequirements />
        <SelfReviewSummary />
      </main>
    </div>
  );
}

export default App;
