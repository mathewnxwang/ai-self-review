import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

// Default role requirements template
const DEFAULT_ROLE_REQUIREMENTS = `# Job Requirements

## Ownership & Impact
- Takes ownership of projects and delivers end-to-end
- Makes net positive impact to the business
- Identifies and solves important problems

## Technical Craft
- Writes high-quality, maintainable code
- Improves system reliability and performance
- Makes good technical decisions

## Teamwork & Collaboration
- Helps unblock team members
- Shares knowledge effectively
- Contributes to a positive team culture
`;

function App() {
  // Form state - load from localStorage for convenience
  const [formData, setFormData] = useState(() => {
    const saved = localStorage.getItem('selfReviewFormData');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return {
          repo: '',
          year: new Date().getFullYear(),
          github_username: '',
          github_token: '',
          role_requirements: DEFAULT_ROLE_REQUIREMENTS,
        };
      }
    }
    return {
      repo: '',
      year: new Date().getFullYear(),
      github_username: '',
      github_token: '',
      role_requirements: DEFAULT_ROLE_REQUIREMENTS,
    };
  });

  const [summary, setSummary] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  // Save non-sensitive form data to localStorage
  useEffect(() => {
    const dataToSave = {
      ...formData,
      github_token: '', // Don't persist tokens
    };
    localStorage.setItem('selfReviewFormData', JSON.stringify(dataToSave));
  }, [formData.repo, formData.year, formData.github_username, formData.role_requirements]);

  const handleChange = (field) => (e) => {
    setFormData({ ...formData, [field]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setGenerating(true);
    setError('');
    setSummary('');

    try {
      const response = await fetch('/api/generate-summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo: formData.repo,
          year: parseInt(formData.year),
          github_username: formData.github_username,
          github_token: formData.github_token,
          role_requirements: formData.role_requirements,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSummary(data.summary);
      } else {
        setError(data.error || 'Failed to generate summary');
      }
    } catch (err) {
      if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
        setError('Cannot connect to backend. Make sure the server is running.');
      } else {
        setError(err.message);
      }
    } finally {
      setGenerating(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(summary);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Self-Review Generator</h1>
        <p>Generate your performance self-review from merged PRs</p>
      </header>

      <main className="app-main">
        <form onSubmit={handleSubmit} className="review-form">
          <div className="form-section">
            <h2>GitHub Configuration</h2>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="repo">Repository (owner/repo)</label>
                <input
                  id="repo"
                  type="text"
                  value={formData.repo}
                  onChange={handleChange('repo')}
                  placeholder="myorg/myrepo"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="year">Year</label>
                <input
                  id="year"
                  type="number"
                  value={formData.year}
                  onChange={handleChange('year')}
                  min="2000"
                  max="2100"
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="github_username">GitHub Username</label>
                <input
                  id="github_username"
                  type="text"
                  value={formData.github_username}
                  onChange={handleChange('github_username')}
                  placeholder="your-username"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="github_token">
                  GitHub Personal Access Token
                  <a 
                    href="https://github.com/settings/tokens" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="help-link"
                  >
                    (Create one)
                  </a>
                </label>
                <input
                  id="github_token"
                  type="password"
                  value={formData.github_token}
                  onChange={handleChange('github_token')}
                  placeholder="ghp_xxxxxxxxxxxx"
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h2>Role Requirements</h2>
            <p className="section-description">
              Define the criteria your work will be evaluated against. The AI will align your PR summaries with these requirements.
            </p>
            <div className="form-group">
              <textarea
                id="role_requirements"
                value={formData.role_requirements}
                onChange={handleChange('role_requirements')}
                placeholder="Enter your role requirements in Markdown format..."
                rows={12}
                required
              />
            </div>
          </div>

          <button 
            type="submit" 
            className="generate-button"
            disabled={generating}
          >
            {generating ? 'Generating... (this may take a minute)' : 'Generate Self-Review'}
          </button>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
        </form>

        {summary && (
          <div className="summary-section">
            <div className="summary-header">
              <h2>Your Self-Review Summary</h2>
              <button onClick={copyToClipboard} className="copy-button">
                Copy to Clipboard
              </button>
            </div>
            <div className="summary-content">
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>
          Your tokens are never stored on the server. They are only used for this single request.
        </p>
      </footer>
    </div>
  );
}

export default App;
